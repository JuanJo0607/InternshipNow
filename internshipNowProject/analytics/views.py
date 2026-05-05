from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from accounts.models import CompanyProfile
from analytics.services import getViewsVsApplicationsPerJob, getAverageTimeToClose, getCandidatesByStatus, is_profile_complete


@login_required
def company_metrics_page(request, company_id):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    if profile.id != company_id:
        return redirect('home')
    return render(request, 'analytics/company_metrics.html', {'company': profile})


@login_required
def company_metrics_api(request, id):
    company_id = id
    if request.user.role != 'company':
        return JsonResponse({'error': 'Forbidden'}, status=403)

    profile = CompanyProfile.objects.get(user=request.user)
    if profile.id != company_id:
        return JsonResponse({'error': 'Not found'}, status=404)

    filters = {}
    month = request.GET.get('month')
    year = request.GET.get('year')
    try:
        if month:
            filters['month'] = int(month)
        if year:
            filters['year'] = int(year)
    except ValueError:
        return JsonResponse({'error': 'Invalid month or year'}, status=400)

    metrics = getViewsVsApplicationsPerJob(company_id, filters)
    average_time_to_close = getAverageTimeToClose(company_id, filters)
    candidates_by_status = getCandidatesByStatus(company_id, filters)

    total_views = sum(item['views_count'] for item in metrics)
    total_applications = sum(item['applications_count'] for item in metrics)

    return JsonResponse({
        'views_vs_applications': metrics,
        'average_time_to_close_days': average_time_to_close,
        'candidates_by_status': candidates_by_status,
        'totals': {
            'total_views': total_views,
            'total_applications': total_applications,
            'average_time_to_close_days': average_time_to_close,
        }
    })


@login_required
def profile_status(request):
    status = is_profile_complete(request.user)
    return JsonResponse(status)
