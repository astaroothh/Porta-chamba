from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import config
from db import get_conn
from cv_matcher import calcular_match
from cv_generator import generar_cv
from pdf_export import convertir_a_pdf

app = FastAPI(title="Portal de Postulaciones")
templates = Jinja2Templates(directory="templates")


class VacanteIn(BaseModel):
    empresa: str
    cargo: str
    descripcion: str
    email_contacto: str | None = None
    url: str | None = None
    fuente: str = "manual"


class EdicionIn(BaseModel):
    perfil: str
    habilidades: list[str]


class PlantillaCorreoIn(BaseModel):
    asunto_tpl: str
    cuerpo_tpl: str
    cc_default: str | None = None


class ConfigSMTPIn(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    tu_nombre: str | None = None
    pausa_min_seg: int = 25
    pausa_max_seg: int = 45


def _ruta_docx(vacante) -> Path:
    nombre = f"CV_{vacante['empresa']}_{vacante['cargo']}"
    nombre = "".join(c for c in nombre if c.isalnum() or c in " _-").replace(" ", "_")
    return Path("cvs_generados") / f"{nombre}.docx"


def _verificar_token(token: str | None):
    if token != config.API_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")


def _obtener_habilidades() -> list[str]:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT habilidad FROM habilidades_usuario")
        return [row["habilidad"] for row in cur.fetchall()]


# ---------- Dashboard ----------

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM vacantes ORDER BY fecha_creacion DESC")
        vacantes = cur.fetchall()
    return templates.TemplateResponse("dashboard.html", {"request": request, "vacantes": vacantes})


# ---------- Registrar vacantes (formulario web o script de scraping/API) ----------

@app.post("/api/vacantes")
def crear_vacante(vacante: VacanteIn):
    habilidades = _obtener_habilidades()
    resultado = calcular_match(vacante.descripcion, habilidades)

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO vacantes
               (empresa, cargo, descripcion, email_contacto, url, fuente, match_pct, palabras_clave, estado)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'cv_generado')""",
            (
                vacante.empresa, vacante.cargo, vacante.descripcion, vacante.email_contacto,
                vacante.url, vacante.fuente, resultado["match_pct"],
                ", ".join(resultado["habilidades_cubiertas"]),
            ),
        )
        vacante_id = cur.lastrowid

    # genera el CV adaptado ya mismo, así el dashboard lo puede mostrar/descargar
    generar_cv(
        {"id": vacante_id, "empresa": vacante.empresa, "cargo": vacante.cargo},
        resultado["habilidades_cubiertas"],
    )

    return {"id": vacante_id, **resultado}


# ---------- Consultar / actualizar estado (seguimiento manual desde el dashboard) ----------

@app.patch("/api/vacantes/{vacante_id}/estado")
def actualizar_estado(vacante_id: int, estado: str, notas: str | None = None):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE vacantes SET estado=%s, notas=COALESCE(%s, notas) WHERE id=%s",
            (estado, notas, vacante_id),
        )
    return {"ok": True}


# ---------- Endpoints para el script local (protegidos por token) ----------

@app.get("/api/vacantes/pendientes")
def listar_pendientes(token: str = Header(None, alias="X-API-Token")):
    _verificar_token(token)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM vacantes WHERE estado='cv_generado'")
        return cur.fetchall()


@app.get("/api/vacantes/{vacante_id}/cv")
def descargar_cv(vacante_id: int, token: str = Header(None, alias="X-API-Token")):
    _verificar_token(token)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM vacantes WHERE id=%s", (vacante_id,))
        vacante = cur.fetchone()
    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")

    ruta = _ruta_docx(vacante)
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="CV no generado aún")
    return FileResponse(ruta, filename=ruta.name)


@app.post("/api/vacantes/{vacante_id}/marcar-enviado")
def marcar_enviado(vacante_id: int, token: str = Header(None, alias="X-API-Token")):
    _verificar_token(token)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE vacantes SET estado='enviada', fecha_envio=NOW() WHERE id=%s",
            (vacante_id,),
        )
    return {"ok": True}


# ---------- Editor en vivo (desde el navegador, sin token — es tu propio dashboard) ----------

@app.get("/vacantes/{vacante_id}/editar", response_class=HTMLResponse)
def pagina_editar(vacante_id: int, request: Request):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM vacantes WHERE id=%s", (vacante_id,))
        vacante = cur.fetchone()
    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")

    habilidades_cubiertas = [h.strip() for h in (vacante["palabras_clave"] or "").split(",") if h.strip()]
    destacadas = ", ".join(habilidades_cubiertas[:5]) or "automatización de procesos y desarrollo en Python"
    perfil_sugerido = (
        f"Técnico en Programación con experiencia en automatización de procesos, desarrollo de "
        f"herramientas en Python y gestión de bases de datos. Para el cargo de {vacante['cargo']} en "
        f"{vacante['empresa']}, destaco mi manejo de {destacadas}."
    )
    habilidades_texto = (vacante["habilidades_orden"] or "\n".join(habilidades_cubiertas)).replace(", ", "\n")

    return templates.TemplateResponse("editar.html", {
        "request": request,
        "vacante": vacante,
        "perfil_sugerido": perfil_sugerido,
        "habilidades_texto": habilidades_texto,
        "datos_fijos": config.DATOS_CV,
    })


@app.post("/api/vacantes/{vacante_id}/editar")
def guardar_edicion(vacante_id: int, edicion: EdicionIn):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM vacantes WHERE id=%s", (vacante_id,))
        vacante = cur.fetchone()
        if not vacante:
            raise HTTPException(status_code=404, detail="Vacante no encontrada")

        cur.execute(
            "UPDATE vacantes SET perfil_editado=%s, habilidades_orden=%s WHERE id=%s",
            (edicion.perfil, ", ".join(edicion.habilidades), vacante_id),
        )

    # regenera el docx ya con tus cambios
    generar_cv(
        {"id": vacante_id, "empresa": vacante["empresa"], "cargo": vacante["cargo"]},
        habilidades_cubiertas=[],
        perfil_override=edicion.perfil,
        habilidades_orden_override=edicion.habilidades,
    )
    return {"ok": True}


@app.get("/api/vacantes/{vacante_id}/cv.pdf")
def descargar_cv_pdf(vacante_id: int):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM vacantes WHERE id=%s", (vacante_id,))
        vacante = cur.fetchone()
    if not vacante:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")

    ruta_docx = _ruta_docx(vacante)
    if not ruta_docx.exists():
        raise HTTPException(status_code=404, detail="CV no generado aún")

    ruta_pdf = convertir_a_pdf(ruta_docx)
    return FileResponse(ruta_pdf, filename=ruta_pdf.name)


# ---------- Plantilla de correo masivo (editable desde el navegador) ----------

@app.get("/plantilla-correo", response_class=HTMLResponse)
def pagina_plantilla_correo(request: Request):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM plantilla_correo WHERE id=1")
        plantilla = cur.fetchone()
    return templates.TemplateResponse("plantilla_correo.html", {"request": request, "plantilla": plantilla})


@app.post("/api/plantilla-correo")
def guardar_plantilla_correo(plantilla: PlantillaCorreoIn):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE plantilla_correo SET asunto_tpl=%s, cuerpo_tpl=%s, cc_default=%s WHERE id=1""",
            (plantilla.asunto_tpl, plantilla.cuerpo_tpl, plantilla.cc_default),
        )
    return {"ok": True}


@app.get("/api/plantilla-correo")
def obtener_plantilla_correo(token: str = Header(None, alias="X-API-Token")):
    _verificar_token(token)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM plantilla_correo WHERE id=1")
        return cur.fetchone()


# ---------- Configuración de envío SMTP (editable desde el navegador) ----------

@app.get("/configuracion-envio", response_class=HTMLResponse)
def pagina_configuracion_envio(request: Request):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM config_smtp WHERE id=1")
        config_smtp = cur.fetchone()
        cur.execute("SELECT estado, COUNT(*) as n FROM vacantes GROUP BY estado")
        conteos = {row["estado"]: row["n"] for row in cur.fetchall()}

    stats = {
        "cv_generado": conteos.get("cv_generado", 0),
        "enviada": conteos.get("enviada", 0),
        "respondida": conteos.get("respondida", 0),
        "entrevista": conteos.get("entrevista", 0),
    }
    return templates.TemplateResponse("configuracion_envio.html", {
        "request": request, "config": config_smtp, "stats": stats,
    })


@app.post("/api/config-smtp")
def guardar_config_smtp(cfg: ConfigSMTPIn):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """UPDATE config_smtp SET smtp_host=%s, smtp_port=%s, smtp_user=%s, smtp_pass=%s,
               tu_nombre=%s, pausa_min_seg=%s, pausa_max_seg=%s WHERE id=1""",
            (cfg.smtp_host, cfg.smtp_port, cfg.smtp_user, cfg.smtp_pass,
             cfg.tu_nombre, cfg.pausa_min_seg, cfg.pausa_max_seg),
        )
    return {"ok": True}


@app.get("/api/config-smtp")
def obtener_config_smtp(token: str = Header(None, alias="X-API-Token")):
    _verificar_token(token)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM config_smtp WHERE id=1")
        return cur.fetchone()
