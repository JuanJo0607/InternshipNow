from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.forms import CustomUserCreationForm, StudentProfileForm, CompanyProfileForm, StudentCVForm
from accounts.models import StudentProfile, CompanyProfile
from analytics.services import is_profile_complete


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name = form.cleaned_data.get('last_name', '')
            user.save()
            login(request, user)

            if user.role == 'student':
                cedula = form.cleaned_data.get('cedula', '')
                StudentProfile.objects.create(user=user, cedula=cedula)
                return redirect('student_offers')
            elif user.role == 'company':
                CompanyProfile.objects.create(user=user)
                return redirect('company_profile')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


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
                return redirect('student_offers')
            elif user.role == 'company':
                return redirect('company_profile')

    return render(request, 'registration/login.html')


@login_required
def student_profile(request):
    if request.user.role != 'student':
        return redirect('home')

    profile = StudentProfile.objects.get(user=request.user)

    if request.method == 'POST':
        # Force university to 'Universidad EAFIT' always
        post_data = request.POST.copy()
        post_data['university'] = 'Universidad EAFIT'
        form = StudentProfileForm(post_data, instance=profile)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.save(update_fields=['first_name', 'last_name'])
            profile.refresh_from_db()
            profile_status = is_profile_complete(request.user)
            if not profile_status['complete']:
                missing = ', '.join(profile_status['missing_fields'])
                messages.warning(request, f"Your profile is still incomplete. Missing: {missing}. Please complete it to improve your opportunities.")
    else:
        form = StudentProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        })

    return render(request, 'accounts/student_profile.html', {'form': form, 'profile': profile})


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

    return render(request, 'accounts/company_profile.html', {'form': form, 'profile': profile})


# US-10: View to upload/replace CV in PDF
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

    return render(request, 'accounts/upload_cv.html', {'form': form, 'profile': profile})
