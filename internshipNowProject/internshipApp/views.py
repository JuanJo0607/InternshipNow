from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, StudentProfileForm, CompanyProfileForm
from .models import StudentProfile, CompanyProfile
from django.contrib.auth import authenticate, login


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Crear perfil automáticamente
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

    return render(request, 'student_profile.html', {'form': form})


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

            # 🔥 Redirección según rol
            if user.role == 'student':
                return redirect('student_profile')
            elif user.role == 'company':
                return redirect('company_profile')

    # GET o fallo
    return render(request, 'registration/login.html')
