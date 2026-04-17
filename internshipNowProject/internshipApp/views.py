from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, StudentProfileForm, CompanyProfileForm, InternshipOfferForm, StudentCVForm, ApplicationStatusForm
from .models import StudentProfile, CompanyProfile, InternshipOffer, InternshipApplication, Notification
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from .forms import CustomUserCreationForm, StudentProfileForm, CompanyProfileForm, InternshipOfferForm, StudentCVForm, ApplicationStatusForm
from .models import StudentProfile, CompanyProfile, InternshipOffer, InternshipApplication, InternshipOfferView
from .services import getViewsVsApplicationsPerJob, getAverageTimeToClose, getCandidatesByStatus
from django.contrib.auth import authenticate, login
from .matching import annotate_offers_with_score, get_suggestions, rank_candidates_for_offer
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from .services import is_profile_complete


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

        # Al final de student_offers, antes del return render:
    available_locations = list(
        InternshipOffer.objects.filter(status='open')
        .exclude(location='')
        .values_list('location', flat=True)
        .distinct()
    )

    return render(request, 'student_offers.html', {
        'ranked_offers': ranked_offers,
        'student_skills': student_skills,
        'applied_ids': applied_ids,
        'available_locations': available_locations,
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
        # Forzar universidad a 'Universidad EAFIT' siempre
        post_data = request.POST.copy()
        post_data['university'] = 'Universidad EAFIT'
        form = StudentProfileForm(post_data, instance=profile)
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

    return render(request, 'company_profile.html', {'form': form, 'profile': profile})


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

            # US-14: Check profile completeness for students
            if user.role == 'student':
                profile_status = is_profile_complete(user)
                if not profile_status['complete']:
                    missing = ', '.join(profile_status['missing_fields'])
                    messages.warning(request, f"Your profile is incomplete. Missing: {missing}. Please complete it to improve your opportunities.")

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
    if request.user.role != 'student':
        return redirect('home')

    try:
        profile = StudentProfile.objects.get(user=request.user)
        student_skills = profile.skills
        student_career = profile.career
    except StudentProfile.DoesNotExist:
        student_skills = ''
        student_career = ''

    offers = InternshipOffer.objects.filter(status='open')
    suggestions = get_suggestions(offers, student_skills, student_career)

    applied_ids = list(
        InternshipApplication.objects.filter(student__user=request.user).values_list('offer_id', flat=True)
    )

    return render(request, 'matching_offers.html', {
        'ranked_offers': suggestions['ranked_offers'],
        'student_skills': student_skills,
        'student_career': student_career,
        'mode': suggestions['mode'],
        'applied_ids': applied_ids,
    })


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def create_preselection_notification(user, vacancy_title, match_percentage):
    if match_percentage <= 85:
        return None

    subject = '¡Tu perfil coincide con una vacante urgente!'
    message = (
        f'Hola {user.first_name or user.username},\n\n'
        f'Tu perfil ha alcanzado un match del {match_percentage}% con la vacante "{vacancy_title}".\n'
        'Revisa la plataforma para más detalles.'
    )
    email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@internshipnow.local')

    if user.email:
        send_mail(subject, message, email_from, [user.email], fail_silently=True)

    notification = Notification.objects.create(
        user=user,
        title='Preselección de vacante',
        message=f'Tu perfil coincide en {match_percentage}% con "{vacancy_title}".',
        notification_type='preselection',
    )
    return notification


@login_required
def profile_status(request):
    status = is_profile_complete(request.user)
    return JsonResponse(status)


@login_required
def candidate_ranking(request, offer_id):
    """
    FR-13 - Candidate Recommendation for Companies.
    """
    if request.user.role != 'company':
        return redirect('home')

    profile = CompanyProfile.objects.get(user=request.user)
    offer = InternshipOffer.objects.get(id=offer_id, company=profile)

    applications = InternshipApplication.objects.filter(offer=offer).select_related('student__user')
    students = [app.student for app in applications]

    ranked = rank_candidates_for_offer(offer, students)

    return render(request, 'candidate_ranking.html', {
        'offer': offer,
        'ranked_candidates': ranked,
    })