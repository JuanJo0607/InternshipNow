
def normalize_skills(skills_text: str) -> set[str]:
    """
    Convierte un string de habilidades separadas por comas en un set de
    strings en minúsculas y sin espacios extra.
    """
    if not skills_text:
        return set()
    return {s.strip().lower() for s in skills_text.split(',') if s.strip()}


def calculate_match_score(student_skills_text: str, offer_skills_text: str) -> int:
    """
    Calcula el porcentaje de compatibilidad entre las habilidades de un
    estudiante y las requeridas por una oferta.

    Fórmula: (skills en común / skills requeridas por la oferta) * 100
    """
    student_skills = normalize_skills(student_skills_text)
    offer_skills = normalize_skills(offer_skills_text)

    if not offer_skills:
        return 0

    matched = student_skills & offer_skills
    score = int((len(matched) / len(offer_skills)) * 100)
    return score


def annotate_offers_with_score(offers, student_skills_text: str) -> list[dict]:
    """
    Recibe un queryset de InternshipOffer y el texto de habilidades del
    estudiante. Retorna una lista de dicts con la oferta y su score,
    ordenada de mayor a menor compatibilidad.

    Uso en views.py:
        from .matching import annotate_offers_with_score
        ranked = annotate_offers_with_score(offers, profile.skills)
    """
    result = []
    for offer in offers:
        score = calculate_match_score(student_skills_text, offer.desired_skills)
        result.append({
            'offer': offer,
            'score': score,
            'score_label': _score_label(score),
            'score_color': _score_color(score),
            'score_color_bar': _score_color_bar(score),
        })

    result.sort(key=lambda x: x['score'], reverse=True)
    return result


def _score_label(score: int) -> str:
    if score >= 80:
        return 'Alta compatibilidad'
    elif score >= 50:
        return 'Compatibilidad media'
    elif score > 0:
        return 'Baja compatibilidad'
    else:
        return 'Sin coincidencias'


def _score_color(score: int) -> str:
    """Clase CSS de Tailwind para el badge de color según el score."""
    if score >= 80:
        return 'bg-green-100 text-green-800'
    elif score >= 50:
        return 'bg-yellow-100 text-yellow-800'
    elif score > 0:
        return 'bg-orange-100 text-orange-800'
    else:
        return 'bg-gray-100 text-gray-500'

def _score_color_bar(score: int) -> str:
    """Clase Tailwind para la barra de progreso."""
    if score >= 80:
        return 'bg-green-500'
    elif score >= 50:
        return 'bg-yellow-400'
    elif score > 0:
        return 'bg-orange-400'
    else:
        return 'bg-gray-300'