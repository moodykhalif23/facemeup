"""Evaluation metrics: per-condition + Fitzpatrick-stratified.

Spec §11 — accuracy alone is insufficient for multi-label dermatology: we need
precision, recall, F1, ROC-AUC per condition. Spec §12 — also report metrics
stratified by Fitzpatrick I-VI to expose skin-tone bias.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ..data.labels import CONDITION_NAMES


@dataclass
class ConditionMetrics:
    label: str
    precision: float
    recall: float
    f1: float
    auc: float | None
    support: int   # number of positives in the eval set


@dataclass
class FitzpatrickMetrics:
    bucket: int
    n_samples: int
    f1_macro: float
    per_condition: list[ConditionMetrics] = field(default_factory=list)


@dataclass
class EvalReport:
    overall: list[ConditionMetrics]
    stratified: list[FitzpatrickMetrics]
    threshold: float
    n_samples: int


def evaluate(
    probs: np.ndarray,            # (N, n_conditions) in [0,1]
    targets: np.ndarray,          # (N, n_conditions) in {0,1}
    fitzpatrick: np.ndarray,      # (N,) int, 0 = unknown
    threshold: float = 0.5,
) -> EvalReport:
    if probs.shape != targets.shape:
        raise ValueError(f"shape mismatch: probs {probs.shape}, targets {targets.shape}")

    overall = _per_condition(probs, targets, threshold)
    stratified: list[FitzpatrickMetrics] = []
    for bucket in sorted(set(int(x) for x in fitzpatrick)):
        if bucket == 0:
            continue
        mask = fitzpatrick == bucket
        if mask.sum() < 5:
            continue
        sub = _per_condition(probs[mask], targets[mask], threshold)
        f1_macro = float(np.mean([m.f1 for m in sub])) if sub else 0.0
        stratified.append(
            FitzpatrickMetrics(bucket=bucket, n_samples=int(mask.sum()), f1_macro=f1_macro, per_condition=sub)
        )

    return EvalReport(overall=overall, stratified=stratified, threshold=threshold, n_samples=int(len(probs)))


def _per_condition(probs: np.ndarray, targets: np.ndarray, threshold: float) -> list[ConditionMetrics]:
    preds = (probs >= threshold).astype(np.int32)
    out: list[ConditionMetrics] = []
    for i, name in enumerate(CONDITION_NAMES):
        y_true = targets[:, i].astype(np.int32)
        y_prob = probs[:, i]
        y_pred = preds[:, i]
        support = int(y_true.sum())
        p = float(precision_score(y_true, y_pred, zero_division=0))
        r = float(recall_score(y_true, y_pred, zero_division=0))
        f = float(f1_score(y_true, y_pred, zero_division=0))
        auc: float | None
        try:
            auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else None
        except ValueError:
            auc = None
        out.append(ConditionMetrics(label=name, precision=p, recall=r, f1=f, auc=auc, support=support))
    return out


def format_report(report: EvalReport) -> str:
    lines = [f"Evaluation (N={report.n_samples}, threshold={report.threshold})", ""]
    lines.append("Overall per-condition:")
    lines.append(f"  {'condition':<20}  {'P':>6}  {'R':>6}  {'F1':>6}  {'AUC':>6}  {'n+':>5}")
    for m in report.overall:
        auc_s = f"{m.auc:.3f}" if m.auc is not None else "  -- "
        lines.append(f"  {m.label:<20}  {m.precision:.3f}  {m.recall:.3f}  {m.f1:.3f}  {auc_s:>6}  {m.support:>5}")
    if report.stratified:
        lines.append("")
        lines.append("Fitzpatrick-stratified macro F1:")
        for fp in report.stratified:
            lines.append(f"  bucket {fp.bucket} (n={fp.n_samples}): F1_macro={fp.f1_macro:.3f}")
    return "\n".join(lines)
