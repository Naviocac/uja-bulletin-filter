"""
categories.py

The fixed list of general interest categories and their subtopics, used by
both telegram_commands.py (to build the button menus) and main.py (to turn
a subscriber's choices into a preference description for the AI filter).

Keys (the dict keys here, and the ones stored in data/subscribers.json)
must never change once people have subscribed, or their saved choices will
silently stop matching anything. Adding a brand new category or subtopic
later is fine; renaming or removing an existing key is not.
"""

CATEGORIES = {
    "ciencias": {
        "label": "🔬 Ciencias",
        "subtopics": {
            "investigacion": "Investigación",
            "laboratorios": "Laboratorios",
            "conferencias_cientificas": "Conferencias científicas",
            "bio_quim_fisica": "Biología/Química/Física",
        },
    },
    "letras": {
        "label": "📚 Letras",
        "subtopics": {
            "literatura": "Literatura",
            "historia": "Historia",
            "filosofia": "Filosofía",
            "idiomas": "Idiomas",
            "humanidades": "Humanidades (general)",
        },
    },
    "ingenieria_mates": {
        "label": "💻⚙️ Ingeniería y Matemáticas",
        "subtopics": {
            "programacion": "Programación",
            "ia_ml": "IA / Machine Learning",
            "hackathons": "Hackathons",
            "ciberseguridad": "Ciberseguridad",
            "matematicas": "Matemáticas / estadística",
        },
    },
    "deporte": {
        "label": "⚽ Deporte",
        "subtopics": {
            "gimnasio_instalaciones": "Gimnasio/Instalaciones",
            "torneos": "Torneos",
            "maraton_running": "Maratón/Running",
            "clases_deportivas": "Clases deportivas",
            "ligas_internas": "Ligas internas",
        },
    },
    "gestion": {
        "label": "🏛️ Gestión/Administración",
        "subtopics": {
            "becas": "Becas",
            "matricula": "Matrícula",
            "tramites_administrativos": "Trámites administrativos",
            "normativa": "Normativa",
        },
    },
    "erasmus": {
        "label": "🌍 Erasmus/Movilidad",
        "subtopics": {
            "intercambios": "Intercambios",
            "becas_internacionales": "Becas internacionales",
            "idiomas_movilidad": "Idiomas para movilidad",
            "convocatorias": "Convocatorias",
        },
    },
    "empleo": {
        "label": "💼 Empleo/Prácticas",
        "subtopics": {
            "practicas_empresa": "Prácticas en empresa",
            "ofertas_empleo": "Ofertas de empleo",
            "ferias_empleo": "Ferias de empleo",
            "emprendimiento": "Emprendimiento",
        },
    },
    "cultura": {
        "label": "🎭 Cultura/Ocio",
        "subtopics": {
            "teatro_musica": "Teatro/Música",
            "exposiciones": "Exposiciones",
            "cine": "Cine",
            "excursiones": "Excursiones",
        },
    },
}


def build_preference_text(interests: dict) -> str | None:
    """Turns a subscriber's {category_key: [subtopic_key, ...]} choices into
    a short natural-language description to hand to the AI filter.
    Returns None if the subscriber hasn't picked anything yet."""
    parts = []
    for cat_key, sub_keys in interests.items():
        category = CATEGORIES.get(cat_key)
        if not category or not sub_keys:
            continue
        sub_labels = [
            category["subtopics"][s] for s in sub_keys if s in category["subtopics"]
        ]
        if sub_labels:
            parts.append(f"{category['label']} ({', '.join(sub_labels)})")
    return "; ".join(parts) if parts else None