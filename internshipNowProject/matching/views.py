from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import StudentProfile
from offers.models import InternshipOffer
from applications.models import InternshipApplication
from matching.matching_logic import get_suggestions


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

    return render(request, 'matching/matching_offers.html', {
        'ranked_offers': suggestions['ranked_offers'],
        'student_skills': student_skills,
        'student_career': student_career,
        'mode': suggestions['mode'],
        'applied_ids': applied_ids,
    })
