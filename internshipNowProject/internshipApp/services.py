from .models import StudentProfile

def is_profile_complete(user):
    """
    Verifica si el perfil del estudiante está completo.
    Campos obligatorios: cv_pdf, bio, skills.
    Retorna un dict con 'complete' (bool) y 'missing_fields' (list).
    """
    if user.role != 'student':
        return {'complete': True, 'missing_fields': []}

    try:
        profile = StudentProfile.objects.get(user=user)
    except StudentProfile.DoesNotExist:
        return {'complete': False, 'missing_fields': ['profile']}

    missing = []
    if not profile.cv_pdf:
        missing.append('cv')
    if not profile.bio.strip():
        missing.append('bio')
    if not profile.skills.strip():
        missing.append('skills')

    return {
        'complete': len(missing) == 0,
        'missing_fields': missing
    }