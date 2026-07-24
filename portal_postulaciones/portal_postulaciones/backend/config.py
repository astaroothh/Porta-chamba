import os

# --- Base de datos ---
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "postulaciones")

# --- Seguridad ---
# Token compartido entre el servidor y tu script local (send_pending.py).
# Genera uno fuerte, ej: python -c "import secrets; print(secrets.token_hex(32))"
API_TOKEN = os.environ.get("API_TOKEN", "CAMBIA_ESTE_TOKEN")

# --- Datos fijos de tu CV (no cambian entre vacantes) ---
DATOS_CV = {
    "nombre": "Alex Santiago Vela Tirado",
    "telefono": "3015174473",
    "email": "alex.santiagovela1005@gmail.com",
    "estudios": [
        ("Universidad Germana (UniGermana)", "Ingeniería de Software — 5.° semestre (en curso)", "2025 – Actualmente"),
        ("INCAP", "Técnico Laboral: Operación de Programas Informáticos y Bases de Datos", "2025 – 2026"),
        ("CESDE", "Técnico Laboral: Auxiliar Administrativo", "2024 – 2026"),
        ("Gimnasio Makarenko", "Bachiller Académico", "2022"),
    ],
    "experiencia": [
        {
            "empresa": "Marsh McLennan — Aprendiz SENA",
            "rol": "Apoyo Operaciones Consumer – Automatización & Herramientas Livianas",
            "periodo": "Agosto 2024 – Febrero 2026",
            "logros": [
                "Desarrollé herramientas en Python a la medida de las necesidades operativas del área Consumer, reduciendo tiempos de gestión.",
                "Ejecuté proyectos de automatización de software con Python e integración con Microsoft Access.",
                "Gestioné y optimicé bases de datos (SQL Server, MySQL, Access) para el seguimiento de pólizas y clientes.",
                "Trabajé con Azure para el soporte de soluciones automatizadas en la nube.",
                "Apoyé la transformación digital de procesos manuales en el sector asegurador.",
            ],
        },
        {
            "empresa": "Frisby S.A.S",
            "rol": "Asistente Administrativo",
            "periodo": "Noviembre 2023 – Enero 2024",
            "logros": [
                "Apoyé en tareas administrativas y operativas del establecimiento.",
                "Brindé atención al cliente, gestionando solicitudes y asegurando una experiencia de servicio de calidad.",
                "Gestioné entregas y coordiné operaciones de manera puntual y eficiente.",
            ],
        },
    ],
    "idiomas": "Español (nativo) | Inglés B1",
    "categorias_habilidades": {
        "Lenguajes": ["Python", "C# .NET", "JavaScript"],
        "Bases de Datos": ["SQL Server", "MySQL", "Microsoft Access"],
        "Herramientas": ["Git", "Azure", "NumPy", "Excel Avanzado", "Power BI"],
        "Metodologías": ["Scrum / Ágil", "testing", "optimización de BD"],
    },
}
