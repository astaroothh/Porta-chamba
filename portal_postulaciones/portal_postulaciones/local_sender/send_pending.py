"""
send_pending.py — corre en tu PC, no en el VPS.

Flujo:
  1. Pregunta al servidor qué vacantes están en estado 'cv_generado'.
  2. Descarga el .docx ya adaptado para cada una.
  3. Envía el correo con el CV adjunto, con pausas para no parecer spam.
  4. Le avisa al servidor que quedó 'enviada'.

Configura antes de correr:
    export PORTAL_URL="https://tu-dominio-o-ip:8000"
    export API_TOKEN="el_mismo_token_que_pusiste_en_config.py_del_servidor"
    export SMTP_HOST="smtp.gmail.com"
    export SMTP_PORT="587"
    export SMTP_USER="tucorreo@gmail.com"
    export SMTP_PASS="tu_contraseña_de_aplicacion"

Requisitos:
    pip install requests
"""

import os
import time
import random
import smtplib
import ssl
from pathlib import Path
from email.message import EmailMessage

import requests

PORTAL_URL = os.environ["PORTAL_URL"].rstrip("/")
API_TOKEN = os.environ["API_TOKEN"]
SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]

TU_NOMBRE = "Tu Nombre Aquí"  # <-- cámbialo
HEADERS = {"X-API-Token": API_TOKEN}
DESCARGAS_DIR = Path("cvs_descargados")
PAUSA_MIN_SEG, PAUSA_MAX_SEG = 25, 45


def obtener_plantilla():
    r = requests.get(f"{PORTAL_URL}/api/plantilla-correo", headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def obtener_pendientes():
    r = requests.get(f"{PORTAL_URL}/api/vacantes/pendientes", headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def descargar_cv(vacante) -> Path:
    r = requests.get(f"{PORTAL_URL}/api/vacantes/{vacante['id']}/cv", headers=HEADERS, timeout=30)
    r.raise_for_status()
    DESCARGAS_DIR.mkdir(exist_ok=True)
    ruta = DESCARGAS_DIR / f"CV_{vacante['id']}.docx"
    ruta.write_bytes(r.content)
    return ruta


def enviar_correo(smtp, vacante, ruta_cv: Path, plantilla: dict):
    if not vacante.get("email_contacto"):
        return False, "sin email de contacto"

    asunto = plantilla["asunto_tpl"].format(cargo=vacante["cargo"], empresa=vacante["empresa"])
    cuerpo = plantilla["cuerpo_tpl"].format(cargo=vacante["cargo"], empresa=vacante["empresa"])
    cc = vacante.get("cc_contacto") or plantilla.get("cc_default")

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = vacante["email_contacto"]
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = asunto
    msg.set_content(cuerpo)
    msg.add_attachment(
        ruta_cv.read_bytes(),
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=ruta_cv.name,
    )
    smtp.send_message(msg)
    return True, "enviado"


def marcar_enviado(vacante_id):
    requests.post(
        f"{PORTAL_URL}/api/vacantes/{vacante_id}/marcar-enviado", headers=HEADERS, timeout=20
    )


def main():
    pendientes = obtener_pendientes()
    print(f"{len(pendientes)} vacante(s) pendiente(s) de envío.")
    if not pendientes:
        return

    plantilla = obtener_plantilla()

    contexto = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls(context=contexto)
        smtp.login(SMTP_USER, SMTP_PASS)

        for i, vacante in enumerate(pendientes, 1):
            try:
                ruta_cv = descargar_cv(vacante)
                ok, detalle = enviar_correo(smtp, vacante, ruta_cv, plantilla)
                if ok:
                    marcar_enviado(vacante["id"])
                print(f"[{i}/{len(pendientes)}] {vacante['empresa']} - {detalle}")
            except Exception as e:
                print(f"[{i}/{len(pendientes)}] ERROR con {vacante['empresa']}: {e}")

            if i < len(pendientes):
                time.sleep(random.uniform(PAUSA_MIN_SEG, PAUSA_MAX_SEG))

    print("Listo.")


if __name__ == "__main__":
    main()
