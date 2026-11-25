#!/usr/bin/env bash
# Proyecto final - Auditoría de datos de simulación
# Uso:  bash ejecutar_mac_linux.sh
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "[1/4] Creando entorno virtual..."
  python3 -m venv .venv
fi
source .venv/bin/activate

echo "[2/4] Instalando dependencias..."
python -m pip install --upgrade pip > /dev/null
python -m pip install -r requirements.txt

echo "[3/4] Ejecutando limpieza, análisis, modelo y exportación..."
python codigo/ejecutar_todo.py

echo "[4/4] Dashboard en http://localhost:8000 (Ctrl+C para detener)"
( sleep 1; (open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null) ) &
python -m http.server 8000 --directory dashboard
