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
                # Guardar los campos faltantes en la sesión para el banner de ofertas
                request.session['profile_missing'] = profile_status['missing_fields']
                if not profile_status['complete']:
                    missing = ', '.join(profile_status['missing_fields'])
                    messages.warning(request, f"Tu perfil está incompleto. Faltan: {missing}. Completa tu perfil para mejorar tus oportunidades.")

            if user.role == 'student':
                return redirect('student_offers')
            elif user.role == 'company':
                return redirect('company_profile')

    return render(request, 'registration/login.html')


@login_required
def student_profile(request):
    from analytics.services import is_profile_complete
    from accounts.models import Career
    if request.user.role != 'student':
        return redirect('home')

    profile = StudentProfile.objects.get(user=request.user)

    if request.method == 'POST':
        # Force university to 'Universidad EAFIT' always
        post_data = request.POST.copy()
        post_data['university'] = 'Universidad EAFIT'
        post_data['first_name'] = request.POST.get('first_name', '')
        post_data['last_name'] = request.POST.get('last_name', '')
        form = StudentProfileForm(post_data, instance=profile)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data.get('first_name', '') or ''
            request.user.last_name = form.cleaned_data.get('last_name', '') or ''
            request.user.save(update_fields=['first_name', 'last_name'])
            profile.refresh_from_db()
            profile_status = is_profile_complete(request.user)
            request.session['profile_missing'] = profile_status['missing_fields']
            # No mostrar mensaje de alerta superior, solo el banner central
    else:
        form = StudentProfileForm(instance=profile, initial={
            'first_name': request.user.first_name or '',
            'last_name': request.user.last_name or '',
        })

    # Banner logic (same as offers)
    profile_status = is_profile_complete(request.user)
    profile_missing = profile_status['missing_fields']
    total_fields = 5
    missing_count = len(profile_missing)
    completed_count = total_fields - missing_count
    profile_percent = round((completed_count / total_fields) * 100) if total_fields > 0 else 0
    field_map = {
        'National ID': 'Add your national ID',
        'Career': 'Complete your career',
        'Bio': 'Complete your Bio to gain 20% more visibility',
        'Skills': 'Add your skills',
        'CV': 'Upload your CV',
    }
    dynamic_message = field_map.get(profile_missing[0], 'Complete your profile to improve your opportunities') if profile_missing else ''

    # Get careers as JSON for template (ID and name)
    profile_careers_str = ', '.join([career.name for career in profile.careers.all()])
    careers_data = [{'id': c.id, 'name': c.name} for c in Career.objects.all().order_by('name')]

    return render(request, 'accounts/student_profile.html', {
        'form': form,
        'profile': profile,
        'profile_careers_str': profile_careers_str,
        'careers_data': careers_data,
        'profile_missing': profile_missing,
        'profile_percent': profile_percent,
        'dynamic_message': dynamic_message,
    })


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
            # Actualizar los campos faltantes en la sesión
            from analytics.services import is_profile_complete
            profile_status = is_profile_complete(request.user)
            request.session['profile_missing'] = profile_status['missing_fields']
            return redirect('student_profile')
    else:
        form = StudentCVForm(instance=profile)

    return render(request, 'accounts/upload_cv.html', {'form': form, 'profile': profile})
