import re

STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "para", "con", "un",
    "una", "que", "por", "se", "su", "es", "al", "del", "como", "más",
    "the", "and", "for", "with", "of", "to", "in", "on", "an",
}


def calcular_match(descripcion_vacante: str, mis_habilidades: list[str]) -> dict:
    """
    Compara el texto de la vacante contra tu lista de habilidades reales.
    Devuelve el % de coincidencia y cuáles palabras clave sí y no cubres.

    OJO: esto mide coincidencia TEXTUAL (lo que de verdad revisan los ATS),
    no qué tan buen candidato eres. Es una guía, no una verdad absoluta.
    """
    texto = descripcion_vacante.lower()

    # Palabras "importantes" mencionadas en la vacante (candidatas a requisito)
    palabras_vacante = set(re.findall(r"[a-záéíóúñ0-9\.\#\+]{3,}", texto))
    palabras_vacante -= STOPWORDS

    habilidades_norm = [h.lower() for h in mis_habilidades]
    cubiertas = sorted({h for h in habilidades_norm if h in texto})
    no_mencionadas_en_vacante = sorted(set(habilidades_norm) - set(cubiertas))

    # Requisitos técnicos típicos que aparecen en la vacante pero no declaraste
    posibles_gaps = sorted(
        p for p in palabras_vacante
        if len(p) > 3 and p not in " ".join(habilidades_norm)
    )[:15]  # top 15 para no saturar

    if not habilidades_norm:
        pct = 0.0
    else:
        pct = round(100 * len(cubiertas) / len(habilidades_norm), 1)

    return {
        "match_pct": pct,
        "habilidades_cubiertas": cubiertas,
        "posibles_palabras_faltantes": posibles_gaps,
    }
