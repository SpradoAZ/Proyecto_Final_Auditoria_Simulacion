"""
Ejecuta todo el proceso en orden, desde el Excel original hasta el dashboard.
Uso (desde la carpeta raíz del proyecto):  python codigo/ejecutar_todo.py
Requisitos: Python 3.10+, pandas, openpyxl, numpy, matplotlib, scikit-learn
"""
import subprocess
import sys
from pathlib import Path

CODIGO = Path(__file__).resolve().parent
for script in ["01_auditoria_limpieza.py", "02_analisis_descriptivo.py", "03_modelo_predictivo.py",
               "04_exportar_dashboard.py"]:
    print(f"\n=== {script} ===")
    subprocess.run([sys.executable, str(CODIGO / script)], check=True)
print("\nListo. Abre dashboard/index.html en el navegador.")
