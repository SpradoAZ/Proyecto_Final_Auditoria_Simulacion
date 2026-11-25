@echo off
REM Proyecto final - Auditoria de datos de simulacion
REM Doble clic en este archivo, o ejecutarlo desde CMD en la carpeta del proyecto.
cd /d "%~dp0"

if not exist ".venv" (
    echo [1/4] Creando entorno virtual...
    py -m venv .venv || python -m venv .venv
)
call .venv\Scripts\activate.bat

echo [2/4] Instalando dependencias...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt

echo [3/4] Ejecutando limpieza, analisis, modelo y exportacion...
python codigo\ejecutar_todo.py || goto :error

echo [4/4] Abriendo el dashboard en http://localhost:8000 (Ctrl+C para detener)
start "" http://localhost:8000
python -m http.server 8000 --directory dashboard
goto :eof

:error
echo.
echo Ocurrio un error. Revisa el mensaje de arriba.
pause
