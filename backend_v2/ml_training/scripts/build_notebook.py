"""
Generate ml_training/notebooks/phase3_colab.ipynb
Run: python ml_training/scripts/build_notebook.py
"""

import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
NL = "\n"

def md(*src):
    return {"cell_type": "markdown", "metadata": {}, "source": list(src)}

def code(*src):
    return {"cell_type": "code", "execution_count": None,
            "metadata": {}, "outputs": [], "source": list(src)}

cells = [

md(
"# Phase 3 - Skin-Condition Classifier Training\n",
"## Google SCIN + Fitzpatrick17k via HuggingFace (streaming)\n",
NL,
"**Key fix:** `streaming=True` means NO 13 GB download.\n",
"Images are processed one at a time directly from HuggingFace parquet shards.\n",
"Free Colab (15 GB disk) works fine.\n",
NL,
"**One-time setup before running:**\n",
"1. Accept SCIN terms at https://huggingface.co/datasets/google/scin\n",
"2. Accept Fitzpatrick17k (search `mattgroh/fitzpatrick17k` on HF)\n",
"3. Get a **read token** from https://huggingface.co/settings/tokens\n",
"4. Push repo to GitHub, fill `GITHUB_USER` in Cell 1\n",
NL,
"| Source | Total images | After face/neck filter |\n",
"|---|---|---|\n",
"| `google/scin` | ~10k | ~1-3k |\n",
"| `fitzpatrick17k` | ~16k | ~2-4k |\n",
"| **Combined** | **~26k scanned, ~13 GB streamed** | **~3-7k saved** |",
),

md("## 0. Confirm GPU"),
code(
"!nvidia-smi | head -10\n",
"import torch\n",
'print("CUDA:", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")',
),

md("## 1. Clone repo + install"),
code(
'GITHUB_USER = "moodykhalif23"\n',
'BRANCH = "main"\n',
NL,
"!git clone -b {BRANCH} https://github.com/{GITHUB_USER}/skincare.git /content/skincare\n",
"%cd /content/skincare/backend_v2\n",
NL,
"!pip install -q -e ml_service\n",
"!pip install -q -e ml_training   # includes datasets, huggingface-hub\n",
'print("install done")',
),

md(
"## 2. Set HuggingFace token\n",
"\n",
"> **Why not `login()`?**  \n",
"> When running Colab from the VS Code extension, the vault secret injection\n",
"> is unavailable. Set the token directly via `os.environ` instead.\n",
"\n",
"Paste your **read token** from https://huggingface.co/settings/tokens\n",
"(it starts with `hf_`)",
),
code(
"import os\n",
"HF_TOKEN = 'hf_PASTE_YOUR_TOKEN_HERE'   # <-- replace this\n",
NL,
"os.environ['HF_TOKEN'] = HF_TOKEN\n",
NL,
"# Verify it works\n",
"from huggingface_hub import whoami\n",
"try:\n",
"    info = whoami(token=HF_TOKEN)\n",
"    print('Logged in as:', info['name'])\n",
"except Exception as e:\n",
"    print('Auth error:', e)\n",
"    print('Check your token at https://huggingface.co/settings/tokens')",
),

md(
"## 3. Inspect SCIN schema (streaming - no download)\n",
"Reads only a tiny header to show available columns and the body-part distribution.\n",
"No parquet files downloaded.",
),
code(
"from datasets import load_dataset\n",
"from collections import Counter\n",
NL,
"# streaming=True: reads schema immediately, images stream on demand\n",
'ds = load_dataset("google/scin", split="train", streaming=True, token=HF_TOKEN)\n',
NL,
"print('--- Available columns ---')\n",
"for col, feat in ds.features.items():\n",
'    print(f"  {col:<35} {str(feat)}")\n',
NL,
"# Body-part distribution: peek at first 2000 rows (fast, minimal data transfer)\n",
'BP_CANDS   = ["body_part","anatom_site","location","site","region","body_location"]\n',
'FACE_TERMS = {"face","neck","scalp","cheek","forehead","chin","nose","perioral","periorbital","head"}\n',
"bp_col = next((c for c in ds.features if c.lower() in BP_CANDS), None)\n",
NL,
"print(f'\\nbody-part column: {bp_col!r}')\n",
"if bp_col:\n",
"    dist = Counter()\n",
"    for i, row in enumerate(ds):\n",
"        if i >= 2000: break\n",
"        dist[str(row.get(bp_col,'')).lower().strip()] += 1\n",
"    print('\\nTop 20 values (from first 2000 rows):')\n",
"    for val, n in dist.most_common(20):\n",
'        flag = "KEEP" if any(t in val for t in FACE_TERMS) else "skip"\n',
'        print(f"  [{flag}]  {val!r:<40} {n}")\n',
"    kept  = sum(n for v,n in dist.items() if any(t in v for t in FACE_TERMS))\n",
"    total = sum(dist.values())\n",
'    print(f"\\n-> ~{kept}/{total} ({100*kept/max(total,1):.0f}%) of first 2000 rows are face-region")\n',
"else:\n",
'    print("No body-part column -- all rows will be fed to the face detector")',
),

md(
"## 4. Precompute aligned face tensors  (~20-60 min)\n",
NL,
"Streams from HuggingFace, filters face/neck/scalp rows, runs:\n",
"`decode -> face-detect -> align -> CLAHE+WB -> save .npy`\n",
NL,
"Disk usage: only the .npy files (~200 MB for 1k faces, ~600 MB for 3k).\n",
"No parquet shards saved locally.\n",
NL,
"| `--source` | What streams |\n",
"|---|---|\n",
"| `scin_hf` | SCIN only |\n",
"| `fitzpatrick17k` | Fitzpatrick17k only |\n",
"| `all` | Both combined (recommended) |\n",
NL,
"Fully resumable - re-run to continue.",
),
code(
"SOURCE = 'all'   # scin_hf | fitzpatrick17k | all\n",
NL,
"!python -m skin_training.data.precompute \\\n",
"  --source {SOURCE} \\\n",
"  --output /content/work \\\n",
"  --aligned-size 256 \\\n",
"  --verbose 2>&1 | tail -60",
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
'    print("\\n[!] Very few samples - try --all-body-parts flag")',
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

md("## 6. Train  (~40-80 min on T4)\n", "Resumable - interrupt and re-run to continue from last.pt."),
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

md("## 9. Save to Drive + download\n", "Drive is only used here (artifact output), never for input data."),
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
"## 10. Local install  (Windows machine)\n",
NL,
"```powershell\n",
"Copy-Item $HOME\\Downloads\\skin_classifier_mobilenet.onnx `\n",
"  C:\\Users\\Sozuri\\skincare\\backend_v2\\ml_service\\models\\\n",
NL,
"cd C:\\Users\\Sozuri\\skincare\\backend_v2\n",
"docker compose build ml-service\n",
"docker compose up -d ml-service\n",
NL,
"curl http://localhost:8013/healthz   # expect models_loaded: true\n",
"```\n",
NL,
'After that POST /api/v1/analyze returns `"inference_mode": "onnx_mobilenet"`.\n',
NL,
"Report back: val_F1_macro + Fitzpatrick stratified block + index.json\n",
"Then I start Phase 6: MobileNet distillation + INT8 quant.",
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
nb2 = json.loads(out.read_text(encoding="utf8"))
code_n = sum(1 for c in nb2["cells"] if c["cell_type"] == "code")
print(f"written {out}  |  {len(nb2['cells'])} cells ({code_n} code)")
