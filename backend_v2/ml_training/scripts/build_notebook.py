"""
Generate ml_training/notebooks/phase3_colab.ipynb
Run: python ml_training/scripts/build_notebook.py
"""

import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

def md(*src):
    return {"cell_type": "markdown", "metadata": {}, "source": list(src)}

def code(*src):
    return {"cell_type": "code", "execution_count": None,
            "metadata": {}, "outputs": [], "source": list(src)}

NL = "\n"

cells = [

md(
"# Phase 3 — Skin-Condition Classifier\n",
"## Google SCIN + Fitzpatrick17k via HuggingFace\n",
NL,
"**No Google Drive needed for data.** Both datasets load directly from HuggingFace.\n",
NL,
"Runtime -> Change runtime type -> **T4 GPU**\n",
NL,
"### One-time setup:\n",
"1. Accept SCIN terms at https://huggingface.co/datasets/google/scin\n",
"2. Accept Fitzpatrick17k terms (search `mattgroh/fitzpatrick17k` on HF)\n",
"3. Create a HF **read token** at https://huggingface.co/settings/tokens\n",
"4. Push your repo to GitHub, fill `GITHUB_USER` in Cell 1\n",
NL,
"| Source | Total | After face filter | Fitzpatrick |\n",
"|---|---|---|---|\n",
"| `google/scin` | ~10k | ~1-3k | yes |\n",
"| `fitzpatrick17k` | ~16k | ~2-4k | yes |\n",
"| **Combined** | **~26k** | **~3-7k** | **yes** |",
),

md("## 0. Confirm GPU"),
code(
"!nvidia-smi | head -12\n",
"import torch\n",
'print("CUDA:", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")',
),

md(
"## 1. Clone repo + install\n",
"`ml_training` now lists `datasets` and `huggingface-hub` as hard deps.",
),
code(
'GITHUB_USER = "moodykhalif23"\n',
'BRANCH = "main"\n',
NL,
"!git clone -b {BRANCH} https://github.com/{GITHUB_USER}/skincare.git /content/skincare\n",
"%cd /content/skincare/backend_v2\n",
NL,
"!pip install -q -e ml_service\n",
"!pip install -q -e ml_training\n",
'print("install done")',
),

md(
"## 2. HuggingFace login\n",
"Paste your read token from https://huggingface.co/settings/tokens",
),
code(
"from huggingface_hub import login\n",
"login()\n",
NL,
"# Non-interactive:\n",
'# import os; os.environ["HUGGINGFACE_TOKEN"] = "hf_YOUR_TOKEN"',
),

md(
"## 3. Preview SCIN schema + body-part distribution\n",
"Streams 200 rows for the schema check, then the full set for the body-part count.",
),
code(
"from datasets import load_dataset\n",
"from collections import Counter\n",
NL,
'print("--- SCIN schema (first 200 rows) ---")\n',
'preview = load_dataset("google/scin", split="train[:200]")\n',
"for col, feat in preview.features.items():\n",
'    sample = "<image>" if col in ("image","img") else str(preview[0].get(col,""))[:60]\n',
'    print(f"  {col:<35} {str(feat):<25}  e.g. {sample!r}")\n',
NL,
'BP_CANDS   = ["body_part","anatom_site","location","site","region","body_location"]\n',
'FACE_TERMS = {"face","neck","scalp","cheek","forehead","chin","nose","perioral","periorbital","head"}\n',
"bp_col = next((c for c in preview.features if c.lower() in BP_CANDS), None)\n",
NL,
"if bp_col:\n",
'    print(f"\\nbody-part column: {bp_col!r} -- loading full dataset...")\n',
'    ds_full = load_dataset("google/scin", split="train")\n',
'    dist = Counter(str(r.get(bp_col,"")).lower().strip() for r in ds_full)\n',
"    for val, n in dist.most_common(25):\n",
'        flag = "KEEP" if any(t in val for t in FACE_TERMS) else "skip"\n',
'        print(f"  [{flag}]  {val!r:<40} {n}")\n',
"    kept  = sum(n for v,n in dist.items() if any(t in v for t in FACE_TERMS))\n",
"    total = sum(dist.values())\n",
'    print(f"\\n-> Face-region: ~{kept} / {total} ({100*kept/total:.0f}%) will enter precompute")\n',
"else:\n",
'    print("No body-part column found -- face detector will be the only filter.")',
),

md(
"## 4. Precompute aligned face tensors\n",
NL,
"Streams from HuggingFace, filters to face/neck/scalp, runs:\n",
"`decode -> face-detect -> align -> CLAHE+WB -> save .npy`\n",
NL,
"| --source | What loads |\n",
"|---|---|\n",
"| `scin_hf` | SCIN only (~10 min) |\n",
"| `fitzpatrick17k` | Fitzpatrick17k only |\n",
"| `all` | Both combined (recommended, ~30-50 min) |\n",
NL,
"Fully resumable -- re-run to continue.",
),
code(
"# Cache HF downloads. Mount Drive to persist across sessions:\n",
"# from google.colab import drive; drive.mount('/content/drive')\n",
"# HF_CACHE = '/content/drive/MyDrive/skincare/hf_cache'\n",
"HF_CACHE = '/content/hf_cache'   # in-session only",
),
code(
"SOURCE = 'all'   # scin_hf | fitzpatrick17k | all\n",
NL,
"!python -m skin_training.data.precompute \\\n",
"  --source {SOURCE} \\\n",
"  --output /content/work \\\n",
"  --aligned-size 256 \\\n",
"  --hf-cache-dir {HF_CACHE} \\\n",
"  --verbose 2>&1 | tail -50",
),
code(
"import json, re, pandas as pd\n",
"idx = json.loads(open('/content/work/index.json').read())\n",
"print(json.dumps(idx, indent=2))\n",
"n, pct = idx['n_samples'], idx.get('face_detect_skip_pct','?')\n",
'print(f"\\nAligned face tensors: {n}  |  face-detector skip rate: {pct}%")\n',
"df = pd.read_csv('/content/work/labels.csv')\n",
"cond_cols = [c for c in df.columns if re.match(r'^c\\d+_', c)]\n",
'print("\\nCondition coverage:")\n',
"for col in cond_cols:\n",
"    n_pos = int(df[col].sum())\n",
"    pct2  = 100 * n_pos / max(1, len(df))\n",
'    flag  = "[!] " if n_pos < 30 else "    "\n',
'    print(f"  {flag}{col:<28} {n_pos:>6} positives  ({pct2:.1f}%)")\n',
"if n < 300:\n",
'    print("\\n[!] Very few samples -- try --all-body-parts")',
),

md("## 5. Configure training"),
code(
"import yaml\n",
"from pathlib import Path\n",
"cfg = yaml.safe_load(Path('ml_training/configs/base.yaml').read_text())\n",
"cfg['data']['aligned_dir']          = '/content/work'\n",
"cfg['train']['checkpoint_dir']      = '/content/work/runs/exp1'\n",
"cfg['train']['batch_size']          = 32\n",
"cfg['train']['epochs']              = 25\n",
"cfg['train']['mixed_precision']     = True\n",
"cfg['train']['early_stop_patience'] = 6\n",
"Path('/content/config.yaml').write_text(yaml.safe_dump(cfg))\n",
"print(yaml.safe_dump(cfg))",
),

md("## 6. Train (~40-80 min on T4)\n", "Resumable -- interrupt and re-run to continue from last.pt."),
code("!python -m skin_training.train.loop --config /content/config.yaml --verbose"),

md("## 7. TensorBoard (run in a second tab while training)"),
code("%load_ext tensorboard\n", "%tensorboard --logdir /content/work/runs/exp1/tb"),

md("## 8. Export ONNX + roundtrip check"),
code(
"!python -m skin_training.export.to_onnx \\\n",
"  --checkpoint /content/work/runs/exp1/best.pt \\\n",
"  --config /content/config.yaml \\\n",
"  --output /content/work/skin_classifier_mobilenet.onnx \\\n",
"  --verbose",
),

md("## 9. Save to Drive + download\n", "Drive only used here (output artifacts), never for input data."),
code(
"from google.colab import drive, files\n",
"drive.mount('/content/drive')\n",
"!mkdir -p /content/drive/MyDrive/skincare/artifacts\n",
"!cp /content/work/skin_classifier_mobilenet.onnx /content/drive/MyDrive/skincare/artifacts/\n",
"!cp /content/work/runs/exp1/best.pt            /content/drive/MyDrive/skincare/artifacts/\n",
"!cp /content/work/index.json                   /content/drive/MyDrive/skincare/artifacts/\n",
"print('saved to Drive')\n",
"files.download('/content/work/skin_classifier_mobilenet.onnx')",
),

md(
"## 10. Local install (Windows machine)\n",
NL,
"```powershell\n",
"Copy-Item $HOME\\Downloads\\skin_classifier_mobilenet.onnx `\n",
"  C:\\Users\\Sozuri\\skincare\\backend_v2\\ml_service\\models\\\n",
NL,
"cd C:\\Users\\Sozuri\\skincare\\backend_v2\n",
"docker compose build ml-service\n",
"docker compose up -d ml-service\n",
NL,
'curl http://localhost:8013/healthz   # expect models_loaded: true\n',
"```\n",
NL,
'After that POST /api/v1/analyze returns "inference_mode": "onnx_mobilenet".\n',
NL,
"**Report back with:**\n",
"- Final val_F1_macro\n",
"- Fitzpatrick-stratified F1 block\n",
"- index.json (samples per source)\n",
NL,
"-> I will start Phase 6: MobileNet distillation + INT8 quant",
),

]  # end cells

nb = {
    "cells": cells,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"name": "phase3_colab.ipynb", "provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = ROOT / "notebooks" / "phase3_colab.ipynb"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf8")
# verify
nb2 = json.loads(out.read_text(encoding="utf8"))
code_cells = sum(1 for c in nb2["cells"] if c["cell_type"] == "code")
print(f"written {out}  |  {len(nb2['cells'])} cells ({code_cells} code)")
