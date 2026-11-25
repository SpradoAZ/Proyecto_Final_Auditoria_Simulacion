# Cómo ejecutar el proyecto

Requisito: Python 3.10 o superior ([python.org](https://www.python.org/downloads/)). En Windows, al instalarlo marca **"Add Python to PATH"**.

## Opción 1: solo ver el dashboard (sin instalar nada)

Abre `dashboard/index.html` con doble clic. Ya trae los datos procesados y funciona sin internet.

## Opción 2: todo automático

- **Windows:** doble clic en `ejecutar_windows.bat`
- **Mac / Linux:** `bash ejecutar_mac_linux.sh`

El script crea un entorno virtual, instala las librerías, corre los 4 pasos y abre el dashboard en `http://localhost:8000`.

## Opción 3: comandos paso a paso

### Windows (PowerShell o CMD)

```bat
cd C:\ruta\a\proyecto_final
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python codigo\ejecutar_todo.py
python -m http.server 8000 --directory dashboard
```

Si PowerShell no deja activar el entorno, ejecuta una vez:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Mac / Linux

```bash
cd /ruta/a/proyecto_final
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python codigo/ejecutar_todo.py
python -m http.server 8000 --directory dashboard
```

Luego abre `http://localhost:8000` en el navegador. Para detener el servidor: `Ctrl + C`.

## Correr un paso por separado (útil en la sustentación)

```bash
python codigo/01_auditoria_limpieza.py     # 26 verificaciones y base limpia
python codigo/02_analisis_descriptivo.py   # indicadores, resúmenes y figuras
python codigo/03_modelo_predictivo.py      # regresión: MAE, RMSE y R²
python codigo/04_exportar_dashboard.py     # actualiza dashboard/datos.js
```

## Problemas frecuentes

| Mensaje | Solución |
|---|---|
| `py` o `python` no se reconoce | Reinstala Python marcando "Add Python to PATH" |
| `ModuleNotFoundError` | Activa el entorno (`.venv`) y repite `pip install -r requirements.txt` |
| `Address already in use` (puerto 8000) | Usa otro puerto: `python -m http.server 8080 --directory dashboard` |
| El dashboard abre en blanco | Verifica que `datos.js` esté en la misma carpeta que `index.html` |
| `pip` intenta compilar una librería y falla (pide "Microsoft Visual C++") | Tu versión de Python es muy nueva y esa librería aún no publica instaladores para ella. Instala Python 3.13, borra la carpeta `.venv` y crea el entorno con `py -3.13 -m venv .venv` |
| Al activar el entorno el servidor sigue ocupando la terminal | Detén el servidor con `Ctrl + C` o abre otra terminal |
