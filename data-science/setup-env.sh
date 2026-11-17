#!/usr/bin/env bash
# Crea data-science/.venv, instala data-science/requirements.txt y enlaza .venv en la raíz.
# Lo ejecuta el postCreateCommand del Dev Container; es idempotente.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DS="$ROOT/data-science"
PY="$DS/.venv/bin/python"
REQ="$DS/requirements.txt"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# uv no viene en la imagen base.
python -m pip install --user --quiet uv
export PATH="$HOME/.local/bin:$PATH"

uv venv "$DS/.venv" --python "$(command -v python3.13 || command -v python)"

# Fase 1: todo salvo keplergl. Las ruedas torch/torchaudio/torchvision +cpu solo existen en el índice de PyTorch.
grep -v -i '^keplergl==' "$REQ" > "$TMP/req-sin-keplergl.txt"
uv pip install --python "$PY" -r "$TMP/req-sin-keplergl.txt" \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  --index-strategy unsafe-best-match

# Fase 2: keplergl pide pyarrow==16.0.0 (sin rueda para 3.13) como dependencia de build, así que se
# instala sin aislamiento de build. Usa el setuptools<81 fijado en requirements.txt (necesita pkg_resources).
uv pip install --python "$PY" --no-build-isolation --no-deps "$(grep -i '^keplergl==' "$REQ")"

uv pip check --python "$PY"

# Compatibilidad con speckit y AGENTS.md §K: .venv/bin/python en la raíz.
ln -sfn data-science/.venv "$ROOT/.venv"
