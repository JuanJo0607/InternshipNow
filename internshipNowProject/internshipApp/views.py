from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, StudentProfileForm, CompanyProfileForm, InternshipOfferForm, StudentCVForm, ApplicationStatusForm
from .models import StudentProfile, CompanyProfile, InternshipOffer, InternshipApplication
from django.contrib.auth import authenticate, login


@login_required
def student_offers(request):
    # list all open offers for students
    offers = InternshipOffer.objects.filter(status='open').order_by('-created_at')
    applied_ids = []
    if request.user.role == 'student':
        profile = StudentProfile.objects.get(user=request.user)
        applied_ids = list(profile.applications.values_list('offer_id', flat=True))
    return render(request, 'student_offers.html', {'offers': offers, 'applied_ids': applied_ids})


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
    # GET o fallo


# application views

@login_required
def apply_to_offer(request, offer_id):
    if request.user.role != 'student':
        return redirect('home')
    profile = StudentProfile.objects.get(user=request.user)
    offer = InternshipOffer.objects.get(id=offer_id, status='open')
    # ensure single application per student/offer
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
        # already decided, nothing to do
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
