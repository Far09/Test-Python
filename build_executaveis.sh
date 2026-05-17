#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Erro: Python não encontrado: $PYTHON_BIN" >&2
  exit 1
fi

echo "==> Instalando/atualizando PyInstaller"
"$PYTHON_BIN" -m pip install --upgrade pip pyinstaller

echo "==> Limpando builds anteriores"
rm -rf build dist

NOME="portal-chamados"

echo "==> Gerando executável"
"$PYTHON_BIN" -m PyInstaller \
  --onefile \
  --name "$NOME" \
  portal_chamados.py

echo "Executável gerado em: dist/$NOME"
