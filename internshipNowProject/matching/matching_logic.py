
def normalize_skills(skills_text: str) -> set[str]:
    """
    Convierte un string de habilidades separadas por comas en un set de
    strings en minúsculas y sin espacios extra.
    """
    if not skills_text:
        return set()
    return {s.strip().lower() for s in skills_text.split(',') if s.strip()}


def calculate_match_score(student_skills_text: str, offer_skills_text: str, student_careers=None, offer_careers=None) -> int:
    """
    Calcula el porcentaje de compatibilidad entre las habilidades de un
    estudiante y las requeridas por una oferta, considerando también carreras.

    Fórmula base (skills): (skills en común / skills requeridas por la oferta) * 100
    Si hay coincidencia de carreras, se da un boost al score.
    """
    student_skills = normalize_skills(student_skills_text)
    offer_skills = normalize_skills(offer_skills_text)

    # Calculate skills match
    if not offer_skills:
        skills_score = 0
    else:
        matched = student_skills & offer_skills
        skills_score = int((len(matched) / len(offer_skills)) * 100)

    # Check if careers match (boost for career alignment)
    career_boost = 0
    if student_careers and offer_careers:
        # student_careers and offer_careers should be QuerySets or lists of Career objects
        student_career_names = {c.name.lower() for c in student_careers} if hasattr(student_careers, '__iter__') else set()
        offer_career_names = {c.name.lower() for c in offer_careers} if hasattr(offer_careers, '__iter__') else set()
        
        if student_career_names and offer_career_names:
            if student_career_names & offer_career_names:
                career_boost = 15  # Boost score by 15% if careers match
    
    final_score = min(skills_score + career_boost, 100)
    return final_score


def annotate_offers_with_score(offers, student_skills_text: str, student_careers=None) -> list[dict]:
    """
    Recibe un queryset de InternshipOffer, el texto de habilidades del
    estudiante, y opcionalmente sus carreras. Retorna una lista de dicts con la oferta y su score,
    ordenada de mayor a menor compatibilidad.
    """
    result = []
    for offer in offers:
        score = calculate_match_score(student_skills_text, offer.desired_skills, student_careers, offer.careers.all())
        result.append({
            'offer': offer,
            'score': score,
            'score_label': _score_label(score),
            'score_color': _score_color(score),
            'score_color_bar': _score_color_bar(score),
        })

    result.sort(key=lambda x: x['score'], reverse=True)
    return result


def get_suggestions(offers, student_skills_text: str, student_careers=None) -> dict:
    """
    US-12 – Lógica principal de sugerencias personalizadas.

    Caso 1 – El estudiante TIENE habilidades:
        Retorna las ofertas con score > 0, ordenadas de mayor a menor.

    Caso 2 – El estudiante NO tiene habilidades pero TIENE carreras:
        Retorna las ofertas cuyas carreras coincidan con las del estudiante,
        priorizadas por cercanía temporal.

    Caso 3 – El estudiante NO tiene habilidades ni carreras:
        Retorna las 5 ofertas más recientes.

    student_careers puede ser un QuerySet de Career objects o None

    Retorna un dict con:
        - 'ranked_offers': lista de dicts (igual formato que annotate_offers_with_score)
        - 'mode': 'skills' | 'career' | 'recent'
        - 'careers': carreras del estudiante (para mostrar en el template)
    """
    has_skills = bool(normalize_skills(student_skills_text))
    has_careers = bool(student_careers and student_careers.exists() if hasattr(student_careers, 'exists') else student_careers and len(student_careers) > 0)

    if has_skills:
        ranked = annotate_offers_with_score(offers, student_skills_text, student_careers)
        matched = [r for r in ranked if r['score'] >= 50]
        return {
            'ranked_offers': matched,
            'mode': 'skills',
            'careers': list(student_careers) if student_careers else [],
        }

    # Sin habilidades: buscar por carrera
    if has_careers:
        career_offers = offers.filter(careers__in=student_careers).distinct().order_by('-created_at')[:5]
        ranked = []
        for offer in career_offers:
            ranked.append({
                'offer': offer,
                'score': 0,
                'score_label': 'Matches your career',
                'score_color': 'bg-blue-100 text-blue-800',
                'score_color_bar': 'bg-blue-300',
            })
        
        return {
            'ranked_offers': ranked,
            'mode': 'career',
            'careers': list(student_careers) if student_careers else [],
        }

    # Sin habilidades ni carreras: mostrar recientes
    recent_offers = offers.order_by('-created_at')[:5]
    ranked = []
    for offer in recent_offers:
        ranked.append({
            'offer': offer,
            'score': 0,
            'score_label': 'Recent offer',
            'score_color': 'bg-gray-100 text-gray-800',
            'score_color_bar': 'bg-gray-300',
        })

    return {
        'ranked_offers': ranked,
        'mode': 'recent',
        'careers': list(student_careers) if student_careers else [],
    }


def _score_label(score: int) -> str:
    if score >= 80:
        return 'High compatibility'
    elif score >= 50:
        return 'Medium compatibility'
    elif score > 0:
        return 'Low compatibility'
    else:
        return 'No match'


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


def rank_candidates_for_offer(offer, students) -> list[dict]:
    """
    FR-13 - Candidate Recommendation for Companies.

    Recibe una InternshipOffer y un queryset de StudentProfile.
    Retorna una lista de dicts ordenada de mayor a menor score,
    incluyendo solo estudiantes con score > 0.
    """
    result = []
    offer_skills = normalize_skills(offer.desired_skills)

    for student in students:
        if not student.skills:
            continue
        student_skills = normalize_skills(student.skills)
        matched = student_skills & offer_skills
        score = int((len(matched) / len(offer_skills)) * 100) if offer_skills else 0
        if score == 0:
            continue
        result.append({
            'student': student,
            'score': score,
            'score_label': _score_label(score),
            'score_color': _score_color(score),
            'score_color_bar': _score_color_bar(score),
            'matched_skills': matched,
        })

    result.sort(key=lambda x: x['score'], reverse=True)
    return result
