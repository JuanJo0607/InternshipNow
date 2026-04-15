from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, StudentProfileForm, CompanyProfileForm, InternshipOfferForm, StudentCVForm, ApplicationStatusForm
from .models import StudentProfile, CompanyProfile, InternshipOffer, InternshipApplication
from django.contrib.auth import authenticate, login
from .matching import annotate_offers_with_score, get_suggestions, rank_candidates_for_offer



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
    return render(request, 'company_offers.html', {'offers': offers})


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
    offer.save()
    return redirect('company_offers')


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
def candidate_ranking(request, offer_id):
    """
    FR-13 - Candidate Recommendation for Companies.
    Muestra el ranking de estudiantes que aplicaron a la oferta,
    ordenados por compatibilidad con las habilidades requeridas.
    """
    if request.user.role != 'company':
        return redirect('home')

    profile = CompanyProfile.objects.get(user=request.user)
    offer = InternshipOffer.objects.get(id=offer_id, company=profile)

    # Solo estudiantes que aplicaron a esta oferta específica
    applications = InternshipApplication.objects.filter(offer=offer).select_related('student__user')
    students = [app.student for app in applications]

    ranked = rank_candidates_for_offer(offer, students)

    return render(request, 'candidate_ranking.html', {
        'offer': offer,
        'ranked_candidates': ranked,
    })