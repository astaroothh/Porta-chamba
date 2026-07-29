import subprocess
from pathlib import Path


def convertir_a_pdf(ruta_docx: Path) -> Path:
    """
    Requiere LibreOffice instalado en el servidor:
        sudo apt install libreoffice --no-install-recommends
    """
    subprocess.run(
        [
            "soffice", "--headless", "--convert-to", "pdf",
            "--outdir", str(ruta_docx.parent), str(ruta_docx),
        ],
        check=True,
        timeout=60,
    )
    return ruta_docx.with_suffix(".pdf")
