"""Knowledge distillation: EfficientNet-B0 teacher -> MobileNetV3-small student.

Per spec §5.2:
  Train EfficientNet (teacher, ~20 MB) for accuracy.
  Distil into MobileNet (student, ~5 MB) for deployment.
  Target: student matches teacher within ~3 F1 points.

Distillation loss (Hinton 2015):
  L = alpha * L_student_hard + (1 - alpha) * T^2 * L_KD
  where L_KD = MSE(sigma(teacher_logits/T), sigma(student_logits/T))
  and T is the temperature.

We use MSE on sigmoid outputs (multi-label) rather than KL divergence
(which assumes softmax / single-label).
"""

from __future__ import annotations

import argparse
import logging
import math
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from ..config import Config
from ..data.dataset import AlignedFaceDataset, load_samples, stratified_split
from ..data.sampler import class_balanced_sampler
from ..eval.metrics import evaluate, format_report
from ..models.classifier import build_model
from .losses import MultiHeadLoss, compute_pos_weight

log = logging.getLogger("distill")


def distil(
    teacher_ckpt: Path,
    student_backbone: str = "mobilenetv3_small_100",
    config_yaml: Path | None = None,
    alpha: float = 0.5,
    temperature: float = 4.0,
    epochs: int | None = None,
    output_dir: Path | None = None,
) -> dict:
    """Run distillation and return a dict with the best student checkpoint path.

    Args:
        teacher_ckpt:      Path to the teacher best.pt (EfficientNet-B0).
        student_backbone:  timm name for the student (MobileNetV3 by default).
        config_yaml:       Path to training config YAML (inherits data/loss settings).
        alpha:             Weight for hard (ground-truth) loss vs soft (KD) loss.
        temperature:       Softening temperature for the teacher logits.
        epochs:            Override epochs from config.
        output_dir:        Where to save the student checkpoint.
    """
    if config_yaml is None:
        raise ValueError("config_yaml is required")

    cfg = Config.from_yaml(config_yaml)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info("distil: teacher=%s  student=%s  device=%s", teacher_ckpt.name,
             student_backbone, device)

    # ── data ─────────────────────────────────────────────────────────────────
    aligned_dir = cfg.data.aligned_dir / "aligned"
    labels_csv  = cfg.data.aligned_dir / "labels.csv"
    samples     = load_samples(labels_csv, aligned_dir)
    train_s, val_s, _ = stratified_split(samples, cfg.data.val_split,
                                         cfg.data.test_split, cfg.train.seed)

    train_ds = AlignedFaceDataset(aligned_dir, train_s, cfg.data.image_size, train=True)
    val_ds   = AlignedFaceDataset(aligned_dir, val_s,   cfg.data.image_size, train=False)
    sampler  = class_balanced_sampler(train_s)
    train_loader = DataLoader(train_ds, batch_size=cfg.train.batch_size, sampler=sampler,
                              num_workers=cfg.data.num_workers, pin_memory=cfg.data.pin_memory,
                              drop_last=True)
    val_loader   = DataLoader(val_ds, batch_size=cfg.train.batch_size, shuffle=False,
                              num_workers=cfg.data.num_workers, pin_memory=cfg.data.pin_memory)

    # ── teacher (frozen) ─────────────────────────────────────────────────────
    teacher = build_model(
        cfg.model.backbone, pretrained=False, embed_dim=cfg.model.embed_dim,
        dropout=0.0, n_conditions=cfg.model.n_conditions,
        n_skin_types=cfg.model.n_skin_types,
        skin_type_head_enabled=cfg.model.skin_type_head_enabled,
    ).to(device)
    payload = torch.load(teacher_ckpt, map_location="cpu", weights_only=False)
    teacher.load_state_dict(payload["model"])
    teacher.eval()
    for p in teacher.parameters():
        p.requires_grad_(False)
    log.info("teacher loaded from %s (frozen)", teacher_ckpt)

    # ── student ───────────────────────────────────────────────────────────────
    student = build_model(
        student_backbone, pretrained=True, embed_dim=cfg.model.embed_dim,
        dropout=cfg.model.dropout, n_conditions=cfg.model.n_conditions,
        n_skin_types=cfg.model.n_skin_types,
        skin_type_head_enabled=cfg.model.skin_type_head_enabled,
    ).to(device)

    # ── loss, optimizer, scheduler ───────────────────────────────────────────
    label_matrix = np.stack([s.label_vector for s in train_s]).astype(np.int32)
    pos_weight   = compute_pos_weight(label_matrix, cap=cfg.loss.pos_weight_cap).to(device)
    hard_loss_fn = MultiHeadLoss(pos_weight=pos_weight).to(device)

    n_epochs = epochs if epochs is not None else cfg.train.epochs
    optimizer = torch.optim.AdamW(student.parameters(),
                                  lr=cfg.train.lr, weight_decay=cfg.train.weight_decay)
    total_steps  = n_epochs * len(train_loader)
    warmup_steps = cfg.train.warmup_epochs * len(train_loader)
    scheduler    = _cosine_with_warmup(optimizer, warmup_steps, total_steps)
    scaler       = torch.amp.GradScaler("cuda",
                       enabled=cfg.train.mixed_precision and device.type == "cuda")

    out_dir = output_dir or (cfg.train.checkpoint_dir.parent / "student")
    out_dir.mkdir(parents=True, exist_ok=True)
    writer  = SummaryWriter(log_dir=str(out_dir / "tb"))

    best_f1, patience = 0.0, 0

    for epoch in range(n_epochs):
        student.train()
        t0 = time.time()
        total_loss = 0.0

        for step, batch in enumerate(tqdm(train_loader, desc=f"distil epoch {epoch}")):
            images = batch["image"].to(device, non_blocking=True)
            labels = batch["labels"].to(device, non_blocking=True)

            # Teacher soft targets (no grad, already frozen)
            with torch.no_grad():
                t_out = teacher(images)
                # Soften with temperature
                soft_targets = torch.sigmoid(t_out.logits_conditions / temperature)

            with torch.amp.autocast("cuda", enabled=scaler.is_enabled()):
                s_out      = student(images)
                # Hard loss: student vs ground truth
                hard       = hard_loss_fn(s_out.logits_conditions, labels).total
                # Soft loss: MSE between softened student and teacher outputs
                soft_student = torch.sigmoid(s_out.logits_conditions / temperature)
                soft        = F.mse_loss(soft_student, soft_targets) * (temperature ** 2)
                loss        = alpha * hard + (1.0 - alpha) * soft

            optimizer.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            if cfg.train.grad_clip:
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(student.parameters(), cfg.train.grad_clip)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            total_loss += float(loss.detach().cpu())

        val_report, val_f1 = _validate(student, val_loader, device)
        log.info("epoch %d: val_F1=%.3f hard+soft loss=%.4f  %.1fs",
                 epoch, val_f1, total_loss / len(train_loader), time.time() - t0)
        writer.add_scalar("val/f1_macro", val_f1, epoch)

        if val_f1 > best_f1:
            best_f1, patience = val_f1, 0
            _save(out_dir / "best_student.pt", epoch, student, optimizer, scheduler,
                  scaler, best_f1, cfg, student_backbone)
        else:
            patience += 1
        _save(out_dir / "last_student.pt", epoch, student, optimizer, scheduler,
              scaler, best_f1, cfg, student_backbone)

        if cfg.train.early_stop_patience and patience >= cfg.train.early_stop_patience:
            log.info("early stop at epoch %d", epoch)
            break

    writer.close()
    log.info("distillation done: best val_F1=%.3f\n%s",
             best_f1, format_report(val_report))
    return {"best_f1": best_f1, "checkpoint": str(out_dir / "best_student.pt"),
            "student_backbone": student_backbone}


# ── helpers ───────────────────────────────────────────────────────────────────

def _validate(model, loader, device):
    model.eval()
    all_probs, all_targets, all_fp = [], [], []
    with torch.no_grad():
        for batch in loader:
            out  = model(batch["image"].to(device, non_blocking=True))
            all_probs.append(torch.sigmoid(out.logits_conditions).cpu().numpy())
            all_targets.append(batch["labels"].numpy())
            all_fp.append(batch["fitzpatrick"].numpy())
    probs   = np.concatenate(all_probs)
    targets = np.concatenate(all_targets)
    fp      = np.concatenate(all_fp)
    report  = evaluate(probs, targets, fp)
    macro   = float(np.mean([m.f1 for m in report.overall])) if report.overall else 0.0
    return report, macro


def _cosine_with_warmup(optimizer, warmup_steps: int, total_steps: int):
    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return step / max(1, warmup_steps)
        progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
        return 0.5 * (1 + math.cos(math.pi * progress))
    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


def _save(path, epoch, model, opt, sched, scaler, best_f1, cfg, backbone):
    torch.save({
        "epoch": epoch, "model": model.state_dict(), "optimizer": opt.state_dict(),
        "scheduler": sched.state_dict(), "scaler": scaler.state_dict(),
        "best_f1": best_f1, "student_backbone": backbone,
        "config": {"model": asdict(cfg.model), "train": asdict(cfg.train)},
    }, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Knowledge distillation: teacher -> student")
    parser.add_argument("--teacher", type=Path, required=True,
                        help="Path to teacher best.pt checkpoint")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--student-backbone", default="mobilenetv3_small_100")
    parser.add_argument("--alpha", type=float, default=0.5,
                        help="Hard-loss weight (0=full KD, 1=no KD, 0.5=balanced)")
    parser.add_argument("--temperature", type=float, default=4.0)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    distil(
        teacher_ckpt=args.teacher,
        student_backbone=args.student_backbone,
        config_yaml=args.config,
        alpha=args.alpha,
        temperature=args.temperature,
        epochs=args.epochs,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
