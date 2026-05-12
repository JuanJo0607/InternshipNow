from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from applications.models import InternshipApplication
from applications.forms import ApplicationStatusForm, ApplicationFeedbackForm
from offers.models import InternshipOffer
from accounts.models import StudentProfile, CompanyProfile
from notifications.models import Notification
from matching.matching_logic import normalize_skills, _score_label, _score_color, rank_candidates_for_offer


def _send_status_notification(application):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    student_user = application.student.user
    offer_title = application.offer.title

    if application.status == 'accepted':
        title = 'Application accepted'
        message = f'Congratulations! Your application for "{offer_title}" has been accepted.'
    else:
        title = 'Application update'
        message = f'Your application for "{offer_title}" has not moved forward this time.'

    notification = Notification.objects.create(
        user=student_user,
        title=title,
        message=message,
        notification_type='status_update',
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notifications_{student_user.id}",
        {
            "type": "notification_message",
            "notification_id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "created_at": notification.created_at.isoformat(),
        }
    )


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

    return render(request, 'applications/student_applications.html', {
        'applications': applications
    })


@login_required
def company_applications(request):
    if request.user.role != 'company':
        return redirect('home')

    profile = CompanyProfile.objects.get(user=request.user)

    raw_apps = InternshipApplication.objects.filter(
        offer__company=profile
    ).select_related('student__user', 'offer').order_by('-applied_at')

    applications = []

    for app in raw_apps:
        student_skills = normalize_skills(app.student.skills or '')
        offer_skills = normalize_skills(app.offer.desired_skills or '')
        matched = student_skills & offer_skills
        score = int((len(matched) / len(offer_skills)) * 100) if offer_skills else 0

        applications.append({
            'app': app,
            'score': score,
            'score_label': _score_label(score),
            'score_color': _score_color(score),
            'matched_skills': sorted(matched),
        })

    applications.sort(key=lambda x: x['score'], reverse=True)

    return render(request, 'applications/company_applications.html', {
        'applications': applications
    })


@login_required
def update_application_status(request, application_id):
    if request.user.role != 'company':
        return redirect('home')

    profile = CompanyProfile.objects.get(user=request.user)
    application = InternshipApplication.objects.get(
        id=application_id,
        offer__company=profile
    )

    if application.status != 'pending':
        return redirect('company_applications')

    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)

        if form.is_valid():
            form.save()
            _send_status_notification(application)
            return redirect('company_applications')
    else:
        form = ApplicationStatusForm(instance=application)

    return render(request, 'applications/application_status_form.html', {
        'form': form,
        'application': application
    })


@login_required
def update_application_feedback(request, application_id):
    if request.user.role != 'company':
        return redirect('home')

    profile = CompanyProfile.objects.get(user=request.user)
    application = InternshipApplication.objects.get(
        id=application_id,
        offer__company=profile
    )

    if application.status not in ['accepted', 'rejected']:
        return redirect('company_applications')

    if request.method == 'POST':
        form = ApplicationFeedbackForm(request.POST, instance=application)

        if form.is_valid():
            form.save()

    return redirect('company_applications')


@login_required
def candidate_ranking(request, offer_id):
    """
    FR-13 - Candidate Recommendation for Companies.
    """
    if request.user.role != 'company':
        return redirect('home')

    profile = CompanyProfile.objects.get(user=request.user)
    offer = InternshipOffer.objects.get(id=offer_id, company=profile)

    applications = InternshipApplication.objects.filter(
        offer=offer
    ).select_related('student__user')

    students = [app.student for app in applications]

    ranked = rank_candidates_for_offer(offer, students)

    return render(request, 'applications/candidate_ranking.html', {
        'offer': offer,
        'ranked_candidates': ranked,
    })