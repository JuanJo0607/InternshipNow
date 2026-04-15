from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .forms import CustomUserCreationForm, StudentProfileForm, CompanyProfileForm, InternshipOfferForm, StudentCVForm, ApplicationStatusForm
from .models import StudentProfile, CompanyProfile, InternshipOffer, InternshipApplication, InternshipOfferView
from .services import getViewsVsApplicationsPerJob, getAverageTimeToClose, getCandidatesByStatus
from django.contrib.auth import authenticate, login
from .matching import annotate_offers_with_score



@login_required
def student_offers(request):
    """
    FR-07 + FR-11: Lista de ofertas abiertas con filtros y score de compatibilidad.
    Las ofertas se ordenan de mayor a menor score cuando el estudiante tiene
    habilidades registradas en su perfil.
    """
    if request.user.role != 'student':
        return redirect('home')

    offers = InternshipOffer.objects.filter(status='open').order_by('-created_at')

    location = request.GET.get('location', '').strip()
    salary   = request.GET.get('salary', '').strip()
    modality = request.GET.get('modality', '').strip()
    skill    = request.GET.get('skill', '').strip()

    if location:
        offers = offers.filter(location__icontains=location)
    if salary:
        offers = offers.filter(salary__gte=salary)
    if modality:
        offers = offers.filter(modality=modality)
    if skill:
        offers = offers.filter(desired_skills__icontains=skill)

    # FR-11 – calcular score de compatibilidad
    try:
        profile = StudentProfile.objects.get(user=request.user)
        student_skills = profile.skills
    except StudentProfile.DoesNotExist:
        student_skills = ''

    ranked_offers = annotate_offers_with_score(offers, student_skills)

    # US-08 – IDs de ofertas ya aplicadas
    applied_ids = list(
        InternshipApplication.objects.filter(student__user=request.user).values_list('offer_id', flat=True)
    )

    return render(request, 'student_offers.html', {
        'ranked_offers': ranked_offers,
        'student_skills': student_skills,
        'applied_ids': applied_ids,
        'filters': {
            'location': location,
            'salary':   salary,
            'modality': modality,
            'skill':    skill,
        },
    })


@login_required
def student_profile(request):
    if request.user.role != 'student':
        return redirect('home')

    profile = StudentProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
    else:
        form = StudentProfileForm(instance=profile)

    return render(request, 'student_profile.html', {'form': form, 'profile': profile})


@login_required
def company_profile(request):
    if request.user.role != 'company':
        return redirect('home')

    profile = CompanyProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = CompanyProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
    else:
        form = CompanyProfileForm(instance=profile)

    return render(request, 'company_profile.html', {'form': form})


def home(request):
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            if user.role == 'student':
                StudentProfile.objects.create(user=user)
                return redirect('student_profile')
            elif user.role == 'company':
                CompanyProfile.objects.create(user=user)
                return redirect('company_profile')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.role == 'student':
                return redirect('student_profile')
            elif user.role == 'company':
                return redirect('company_profile')

    return render(request, 'registration/login.html')


# ----- Internship offer management -----

@login_required
def company_offers(request):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    offers = profile.offers.all().order_by('-created_at')
    return render(request, 'company_offers.html', {'offers': offers, 'profile': profile})


@login_required
def create_offer(request):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = InternshipOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.company = profile
            offer.save()
            return redirect('company_offers')
    else:
        form = InternshipOfferForm()
    return render(request, 'internship_form.html', {'form': form, 'action': 'Create'})


@login_required
def edit_offer(request, offer_id):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    offer = InternshipOffer.objects.get(id=offer_id, company=profile)
    if request.method == 'POST':
        form = InternshipOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            return redirect('company_offers')
    else:
        form = InternshipOfferForm(instance=offer)
    return render(request, 'internship_form.html', {'form': form, 'action': 'Edit'})


@login_required
def close_offer(request, offer_id):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    offer = InternshipOffer.objects.get(id=offer_id, company=profile)
    offer.status = 'closed'
    offer.closed_at = timezone.now()
    offer.save()
    return redirect('company_offers')


@login_required
def offer_detail(request, offer_id):
    if request.user.role != 'student':
        return redirect('home')

    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        return redirect('home')

    offer = get_object_or_404(InternshipOffer.objects.select_related('company'), id=offer_id, status='open')
    InternshipOfferView.objects.create(offer=offer, student=profile)
    applied = InternshipApplication.objects.filter(student=profile, offer=offer).exists()

    return render(request, 'offer_detail.html', {
        'offer': offer,
        'applied': applied,
    })


@login_required
def company_metrics_page(request, company_id):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    if profile.id != company_id:
        return redirect('home')
    return render(request, 'company_metrics.html', {'company': profile})


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


# ----- Application views (US-08) -----

@login_required
def apply_to_offer(request, offer_id):
    if request.user.role != 'student':
        return redirect('home')
    profile = StudentProfile.objects.get(user=request.user)
    offer = InternshipOffer.objects.get(id=offer_id, status='open')
    InternshipApplication.objects.get_or_create(student=profile, offer=offer)
    return redirect('student_applications')


@login_required
def student_applications(request):
    if request.user.role != 'student':
        return redirect('home')
    profile = StudentProfile.objects.get(user=request.user)
    applications = profile.applications.select_related('offer__company').order_by('-applied_at')
    return render(request, 'student_applications.html', {'applications': applications})


@login_required
def company_applications(request):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    applications = InternshipApplication.objects.filter(offer__company=profile).order_by('-applied_at')
    return render(request, 'company_applications.html', {'applications': applications})


@login_required
def update_application_status(request, application_id):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    application = InternshipApplication.objects.get(id=application_id, offer__company=profile)
    if application.status != 'pending':
        return redirect('company_applications')
    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            return redirect('company_applications')
    else:
        form = ApplicationStatusForm(instance=application)
    return render(request, 'application_status_form.html', {'form': form, 'application': application})


# US-10: Vista para subir/reemplazar CV en PDF
@login_required
def upload_cv(request):
    if request.user.role != 'student':
        return redirect('home')

    profile = StudentProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = StudentCVForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('student_profile')
    else:
        form = StudentCVForm(instance=profile)

    return render(request, 'upload_cv.html', {'form': form, 'profile': profile})


@login_required
def matching_offers(request):
    """
    FR-11 - Vista dedicada: muestra SOLO las ofertas con score > 0,
    ordenadas de mayor a menor compatibilidad. No aplica filtros adicionales.
    """
    if request.user.role != 'student':
        return redirect('home')

    try:
        profile = StudentProfile.objects.get(user=request.user)
        student_skills = profile.skills
    except StudentProfile.DoesNotExist:
        student_skills = ''

    offers = InternshipOffer.objects.filter(status='open')
    ranked_offers = annotate_offers_with_score(offers, student_skills)

    matched = [r for r in ranked_offers if r['score'] > 0]

    return render(request, 'matching_offers.html', {
        'ranked_offers': matched,
        'student_skills': student_skills,
    })