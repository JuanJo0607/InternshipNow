from accounts.models import StudentProfile
from applications.models import InternshipApplication
from offers.models import InternshipOffer, InternshipOfferView
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField


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
    if not profile.cedula.strip():
        missing.append('national ID')
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
