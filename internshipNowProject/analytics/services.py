from collections import Counter
from accounts.models import StudentProfile
from applications.models import InternshipApplication
from offers.models import InternshipOffer, InternshipOfferView
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField


def is_profile_complete(user):
    """
    Verifica si el perfil del estudiante está completo.
    Campos obligatorios: first_name, last_name, cedula, careers, bio, skills, cv_pdf.
    Retorna un dict con 'complete' (bool) y 'missing_fields' (list).
    """
    if user.role != 'student':
        return {'complete': True, 'missing_fields': []}

    try:
        profile = StudentProfile.objects.get(user=user)
    except StudentProfile.DoesNotExist:
        return {'complete': False, 'missing_fields': ['profile']}

    missing = []
    if not profile.cedula.strip():
        missing.append('National ID')
    if not profile.careers.exists():
        missing.append('Career')
    if not profile.bio.strip():
        missing.append('Bio')
    if not profile.skills.strip():
        missing.append('Skills')
    if not profile.cv_pdf:
        missing.append('CV')

    return {
        'complete': len(missing) == 0,
        'missing_fields': missing
    }


def get_demanded_skills(career_id=None):
    """
    Returns top 10 most demanded skills from active offers.
    If career_id is given, filters by that career; falls back to global if no data.
    Returns a dict: {'skills': [...], 'fallback': bool, 'status': 'success'|'no_data'}
    """
    active_offers = InternshipOffer.objects.filter(status='open')
    if not active_offers.exists():
        return {'status': 'no_data', 'skills': [], 'fallback': False}

    def _count_skills(offers_qs):
        counter = Counter()
        for offer in offers_qs:
            if offer.desired_skills:
                counter.update(
                    s.strip() for s in offer.desired_skills.split(',') if s.strip()
                )
        return counter

    fallback = False
    if career_id is not None:
        from accounts.models import Career
        try:
            Career.objects.get(id=career_id)
        except Career.DoesNotExist:
            career_id = None

    if career_id is not None:
        filtered = active_offers.filter(careers__id=career_id)
        counter = _count_skills(filtered)
        if not counter:
            counter = _count_skills(active_offers)
            fallback = True
    else:
        counter = _count_skills(active_offers)

    top_skills = [{'name': skill, 'count': count} for skill, count in counter.most_common(10)]
    return {'status': 'success', 'skills': top_skills, 'fallback': fallback}


def get_export_applications(company_profile, date_from=None, date_to=None, status=None):
    """Returns applications queryset for a company, with optional filters."""
    from applications.models import InternshipApplication
    qs = InternshipApplication.objects.filter(
        offer__company=company_profile
    ).select_related('student__user', 'offer__company').prefetch_related('student__careers')

    if date_from:
        qs = qs.filter(applied_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(applied_at__date__lte=date_to)
    if status:
        qs = qs.filter(status=status)

    return qs.order_by('-applied_at')


def get_export_offers(company_profile, date_from=None, date_to=None, status=None):
    """Returns offers queryset for a company, with optional filters."""
    from offers.models import InternshipOffer
    qs = InternshipOffer.objects.filter(company=company_profile).select_related('company')

    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    if status:
        qs = qs.filter(status=status)

    return qs.order_by('-created_at')


def _apply_period_filter(queryset, date_field, filters):
    if not filters:
        return queryset
    if filters.get('year'):
        queryset = queryset.filter(**{f"{date_field}__year": filters['year']})
    if filters.get('month'):
        queryset = queryset.filter(**{f"{date_field}__month": filters['month']})
    return queryset


def getViewsVsApplicationsPerJob(company_id, filters=None):
    filters = filters or {}
    offers = InternshipOffer.objects.filter(company_id=company_id).order_by('-created_at')
    views_qs = _apply_period_filter(InternshipOfferView.objects.filter(offer__company_id=company_id), 'viewed_at', filters)
    apps_qs = _apply_period_filter(InternshipApplication.objects.filter(offer__company_id=company_id), 'applied_at', filters)

    view_counts = {
        item['offer_id']: item['count']
        for item in views_qs.values('offer_id').annotate(count=Count('id'))
    }
    application_counts = {
        item['offer_id']: item['count']
        for item in apps_qs.values('offer_id').annotate(count=Count('id'))
    }

    return [
        {
            'offer_id': offer.id,
            'title': offer.title,
            'status': offer.status,
            'views_count': view_counts.get(offer.id, 0),
            'applications_count': application_counts.get(offer.id, 0),
        }
        for offer in offers
    ]


def getAverageTimeToClose(company_id, filters=None):
    filters = filters or {}
    closed_offers = InternshipOffer.objects.filter(
        company_id=company_id,
        status='closed',
        closed_at__isnull=False,
    )
    closed_offers = _apply_period_filter(closed_offers, 'closed_at', filters)

    aggregated = closed_offers.annotate(
        duration=ExpressionWrapper(
            F('closed_at') - F('created_at'),
            output_field=DurationField()
        )
    ).aggregate(avg_duration=Avg('duration'))

    average_duration = aggregated.get('avg_duration')
    if average_duration is None:
        return 0.0

    return round(average_duration.total_seconds() / 86400, 2)


def getCandidatesByStatus(company_id, filters=None):
    filters = filters or {}
    apps_qs = _apply_period_filter(
        InternshipApplication.objects.filter(offer__company_id=company_id),
        'applied_at',
        filters
    )

    status_counts = {
        item['status']: item['count']
        for item in apps_qs.values('status').annotate(count=Count('id'))
    }

    status_labels = dict(InternshipApplication.STATUS_CHOICES)
    return [
        {
            'status': status,
            'label': status_labels.get(status, status.title()),
            'count': status_counts.get(status, 0),
        }
        for status, _ in InternshipApplication.STATUS_CHOICES
    ]
