"""Training loop.

Reads Config from YAML, builds loaders/model/loss/optimizer, trains with
mixed-precision + cosine schedule + early stopping + TensorBoard logging, and
writes `best.pt` + `last.pt` to the run directory.
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm

from ..config import Config
from ..data.dataset import AlignedFaceDataset, load_samples, stratified_split
from ..data.sampler import class_balanced_sampler
from ..eval.metrics import evaluate, format_report
from ..models.classifier import build_model
from .losses import MultiHeadLoss, compute_pos_weight

log = logging.getLogger("train")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train skin condition classifier")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--resume", type=Path, default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    cfg = Config.from_yaml(args.config)
    _set_seed(cfg.train.seed)
    train_model(cfg, resume_from=args.resume)


def train_model(cfg: Config, resume_from: Path | None = None) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info("device=%s, config.model.backbone=%s", device, cfg.model.backbone)

    # --- data ---------------------------------------------------------------
    aligned_dir = cfg.data.aligned_dir / "aligned"
    labels_csv = cfg.data.aligned_dir / "labels.csv"
    if not labels_csv.is_file():
        log.error("labels.csv not found at %s — run skin-precompute first", labels_csv)
        sys.exit(2)

    samples = load_samples(labels_csv, aligned_dir)
    if not samples:
        log.error("no usable samples in %s", cfg.data.aligned_dir)
        sys.exit(2)
    train_s, val_s, test_s = stratified_split(samples, cfg.data.val_split, cfg.data.test_split, cfg.train.seed)
    log.info("samples: train=%d val=%d test=%d", len(train_s), len(val_s), len(test_s))

    train_ds = AlignedFaceDataset(aligned_dir, train_s, cfg.data.image_size, train=True)
    val_ds   = AlignedFaceDataset(aligned_dir, val_s,   cfg.data.image_size, train=False)

    train_batch_size = min(cfg.train.batch_size, max(1, len(train_ds)))
    val_batch_size = min(cfg.train.batch_size, max(1, len(val_ds)))
    num_workers = min(cfg.data.num_workers, os.cpu_count() or cfg.data.num_workers)
    drop_last = len(train_ds) > train_batch_size
    if train_batch_size != cfg.train.batch_size or num_workers != cfg.data.num_workers:
        log.warning(
            "adjusting loader settings for dataset size: batch_size %d→%d, num_workers %d→%d, drop_last=%s",
            cfg.train.batch_size, train_batch_size, cfg.data.num_workers, num_workers, drop_last,
        )

    sampler = class_balanced_sampler(train_s)
    train_loader = DataLoader(
        train_ds, batch_size=train_batch_size, sampler=sampler,
        num_workers=num_workers, pin_memory=cfg.data.pin_memory, drop_last=drop_last,
    )
    val_loader = DataLoader(
        val_ds, batch_size=val_batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=cfg.data.pin_memory,
    )

    # --- model / loss / optim ----------------------------------------------
    model = build_model(
        cfg.model.backbone, cfg.model.pretrained, cfg.model.embed_dim,
        cfg.model.dropout, cfg.model.n_conditions, cfg.model.n_skin_types,
        cfg.model.skin_type_head_enabled,
    ).to(device)

    label_matrix = np.stack([s.label_vector for s in train_s]).astype(np.int32)
    pos_weight = compute_pos_weight(label_matrix, cap=cfg.loss.pos_weight_cap).to(device)
    criterion = MultiHeadLoss(
        pos_weight=pos_weight,
        skin_type_weight=cfg.loss.skin_type_weight,
        label_smoothing=cfg.train.label_smoothing,
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(), lr=cfg.train.lr, weight_decay=cfg.train.weight_decay
    )
    scheduler = _build_scheduler(optimizer, cfg, steps_per_epoch=len(train_loader))

    scaler = torch.amp.GradScaler("cuda", enabled=cfg.train.mixed_precision and device.type == "cuda")

    # --- checkpoint restore -------------------------------------------------
    start_epoch = 0
    best_f1 = 0.0
    ckpt_dir = cfg.train.checkpoint_dir
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    if resume_from is not None and resume_from.is_file():
        start_epoch, best_f1 = _load_checkpoint(resume_from, model, optimizer, scheduler, scaler)
        log.info("resumed from %s at epoch=%d best_f1=%.3f", resume_from, start_epoch, best_f1)

    writer = SummaryWriter(log_dir=str(ckpt_dir / "tb"))
    patience = 0

    # --- loop ---------------------------------------------------------------
    for epoch in range(start_epoch, cfg.train.epochs):
        model.train()
        t0 = time.time()
        running = 0.0
        for step, batch in enumerate(tqdm(train_loader, desc=f"epoch {epoch}")):
            images = batch["image"].to(device, non_blocking=True)
            labels = batch["labels"].to(device, non_blocking=True)

            with torch.amp.autocast("cuda", enabled=scaler.is_enabled()):
                out = model(images)
                loss_breakdown = criterion(out.logits_conditions, labels)
            loss = loss_breakdown.total
            optimizer.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            if cfg.train.grad_clip is not None:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.train.grad_clip)
            scaler.step(optimizer)
            scaler.update()
            if scheduler is not None:
                scheduler.step()

            running += float(loss.detach().cpu())
            if step % cfg.train.log_every == 0:
                writer.add_scalar("train/loss", running / (step + 1), epoch * len(train_loader) + step)

        val_report, val_f1_macro = _validate(model, val_loader, device, cfg.model.n_conditions)
        log.info("epoch %d: val_F1_macro=%.3f  time=%.1fs", epoch, val_f1_macro, time.time() - t0)
        writer.add_scalar("val/f1_macro", val_f1_macro, epoch)
        for m in val_report.overall:
            writer.add_scalar(f"val/f1/{m.label}", m.f1, epoch)
            if m.auc is not None:
                writer.add_scalar(f"val/auc/{m.label}", m.auc, epoch)

        best_path = ckpt_dir / "best.pt"
        is_best = (not best_path.is_file()) or (val_f1_macro > best_f1)
        if is_best:
            best_f1 = val_f1_macro
            patience = 0
            _save_checkpoint(best_path, epoch, model, optimizer, scheduler, scaler, best_f1, cfg)
        else:
            patience += 1
        if epoch % cfg.train.save_every_epochs == 0:
            _save_checkpoint(ckpt_dir / "last.pt", epoch, model, optimizer, scheduler, scaler, best_f1, cfg)

        if cfg.train.early_stop_patience and patience >= cfg.train.early_stop_patience:
            log.info("early stop at epoch %d (patience=%d)", epoch, patience)
            break

    writer.close()
    log.info("best val_F1_macro=%.3f  (checkpoint: %s)", best_f1, ckpt_dir / "best.pt")
    log.info("\n%s", format_report(val_report))
    return {"best_f1_macro": best_f1, "checkpoint": str(ckpt_dir / "best.pt")}


# --- helpers -----------------------------------------------------------------
def _validate(model, loader, device, n_conditions: int):
    model.eval()
    all_probs: list[np.ndarray] = []
    all_targets: list[np.ndarray] = []
    all_fp: list[np.ndarray] = []
    with torch.no_grad():
        for batch in loader:
            images = batch["image"].to(device, non_blocking=True)
            out = model(images)
            probs = torch.sigmoid(out.logits_conditions).cpu().numpy()
            all_probs.append(probs)
            all_targets.append(batch["labels"].numpy())
            all_fp.append(batch["fitzpatrick"].numpy())
    probs = np.concatenate(all_probs)
    targets = np.concatenate(all_targets)
    fp = np.concatenate(all_fp)
    report = evaluate(probs, targets, fp)
    macro_f1 = float(np.mean([m.f1 for m in report.overall])) if report.overall else 0.0
    return report, macro_f1


def _build_scheduler(optimizer, cfg: Config, steps_per_epoch: int):
    total_steps = cfg.train.epochs * steps_per_epoch
    warmup_steps = cfg.train.warmup_epochs * steps_per_epoch
    if cfg.train.lr_schedule == "cosine":
        def lr_lambda(step: int) -> float:
            if step < warmup_steps:
                return step / max(1, warmup_steps)
            progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
            return 0.5 * (1 + math.cos(math.pi * progress))
        return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    if cfg.train.lr_schedule == "step":
        return torch.optim.lr_scheduler.StepLR(optimizer, step_size=max(1, cfg.train.epochs // 3), gamma=0.1)
    return None


def _save_checkpoint(path, epoch, model, optimizer, scheduler, scaler, best_f1, cfg: Config) -> None:
    payload = {
        "epoch": epoch,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict() if scheduler is not None else None,
        "scaler": scaler.state_dict(),
        "best_f1": best_f1,
        "config": {"model": asdict(cfg.model), "train": asdict(cfg.train)},
    }
    torch.save(payload, path)


def _load_checkpoint(path, model, optimizer, scheduler, scaler):
    payload = torch.load(path, map_location="cpu", weights_only=False)
    model.load_state_dict(payload["model"])
    optimizer.load_state_dict(payload["optimizer"])
    if payload.get("scheduler") is not None and scheduler is not None:
        scheduler.load_state_dict(payload["scheduler"])
    if payload.get("scaler") is not None:
        scaler.load_state_dict(payload["scaler"])
    return int(payload.get("epoch", 0)) + 1, float(payload.get("best_f1", 0.0))


def _set_seed(seed: int) -> None:
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


if __name__ == "__main__":
    main()
