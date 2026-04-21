#!/usr/bin/env bash
set -euo pipefail
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
echo "Done → main.pdf"
