from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, StudentProfileForm, CompanyProfileForm
from .models import StudentProfile, CompanyProfile, Notification
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
from django.utils import timezone


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

            if user.role == 'student':
                return redirect('student_profile')
            elif user.role == 'company':
                return redirect('company_profile')

    # GET o fallo
    return render(request, 'registration/login.html')


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
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'notifications_{user.id}',
        {
            'type': 'notification_message',
            'notification_id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at.isoformat(),
        }
    )
    
    return notification
