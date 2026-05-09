from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from offers.models import InternshipOffer, InternshipOfferView
from offers.forms import InternshipOfferForm
from accounts.models import StudentProfile, CompanyProfile
from applications.models import InternshipApplication
from matching.matching_logic import annotate_offers_with_score


@login_required
def student_offers(request):
    """
    FR-07 + FR-11: List of open offers with filters and compatibility score.
    Offers are sorted from highest to lowest score when the student has
    skills registered in their profile.
    """
    if request.user.role != 'student':
        return redirect('home')

    offers = InternshipOffer.objects.filter(status='open').order_by('-created_at')

    location = request.GET.get('location', '').strip()
    salary   = request.GET.get('salary', '').strip()
    modality = request.GET.get('modality', '').strip()
    skills_param = request.GET.get('skills', '').strip()
    careers_param = request.GET.get('careers', '').strip()
    skills_list = [s.strip() for s in skills_param.split(',') if s.strip()]
    careers_list = [c.strip() for c in careers_param.split(',') if c.strip()]

    if location:
        offers = offers.filter(location__icontains=location)
    if salary:
        offers = offers.filter(salary__gte=salary)
    if modality:
        offers = offers.filter(modality=modality)
    for skill in skills_list:
        offers = offers.filter(desired_skills__icontains=skill)
    
    # Filter by careers - show offers that include at least one of the selected careers
    if careers_list:
        from accounts.models import Career
        career_objects = Career.objects.filter(name__in=careers_list)
        if career_objects.exists():
            offers = offers.filter(careers__in=career_objects).distinct()

    # FR-11 – calculate compatibility score
    try:
        profile = StudentProfile.objects.get(user=request.user)
        student_skills = profile.skills
        student_careers = profile.careers.all()
    except StudentProfile.DoesNotExist:
        student_skills = ''
        student_careers = None

    ranked_offers = annotate_offers_with_score(offers, student_skills, student_careers)

    # US-08 – IDs of already applied offers
    applied_ids = list(
        InternshipApplication.objects.filter(student__user=request.user).values_list('offer_id', flat=True)
    )

    available_locations = list(
        InternshipOffer.objects.filter(status='open')
        .exclude(location='')
        .values_list('location', flat=True)
        .distinct()
    )

    # Banner de perfil incompleto: calcular progreso y campos
    from analytics.services import is_profile_complete
    profile_status = is_profile_complete(request.user)
    profile_missing = profile_status['missing_fields']
    total_fields = 5
    missing_count = len(profile_missing)
    completed_count = total_fields - missing_count
    profile_percent = round((completed_count / total_fields) * 100) if total_fields > 0 else 0

    # Dynamic message for the banner
    dynamic_message = ""
    if profile_missing:
        field_map = {
            'National ID': 'Add your national ID',
            'Career': 'Complete your career',
            'Bio': 'Complete your Bio to gain 20% more visibility',
            'Skills': 'Add your skills',
            'CV': 'Upload your CV',
        }
        dynamic_message = field_map.get(profile_missing[0], 'Complete your profile to improve your opportunities')

    from accounts.models import Career

    careers_data = [{'id': c.id, 'name': c.name} for c in Career.objects.all().order_by('name')]

    return render(request, 'offers/student_offers.html', {
        'ranked_offers': ranked_offers,
        'student_skills': student_skills,
        'applied_ids': applied_ids,
        'available_locations': available_locations,
        'careers_data': careers_data,
        'filters': {
            'location': location,
            'salary':   salary,
            'modality': modality,
            'skills':   skills_param,
            'careers':  careers_param,
        },
        'profile_missing': profile_missing,
        'profile_percent': profile_percent,
        'completed_count': completed_count,
        'total_fields': total_fields,
        'dynamic_message': dynamic_message,
    })


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

    return render(request, 'offers/offer_detail.html', {
        'offer': offer,
        'applied': applied,
    })


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
            form.save_m2m()  # Save careers M2M relationship
            return redirect('company_offers')
    else:
        form = InternshipOfferForm()
    
    from accounts.models import Career
    careers_data = [{'id': c.id, 'name': c.name} for c in Career.objects.all()]
    
    return render(request, 'offers/internship_form.html', {
        'form': form,
        'action': 'Create',
        'careers_data': careers_data,
        'offer_careers_str': '',
    })


@login_required
def edit_offer(request, offer_id):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    offer = InternshipOffer.objects.get(id=offer_id, company=profile)
    offer_careers_str = ''  # Default to empty
    
    if request.method == 'POST':
        form = InternshipOfferForm(request.POST, instance=offer)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.company = profile
            offer.save()
            form.save_m2m()  # Save careers M2M relationship
            return redirect('company_offers')
        # POST with error: don't pass offer_careers_str to avoid autocomplete
    else:
        form = InternshipOfferForm(instance=offer)
        # GET: populate offer_careers_str from DB
        offer_careers_str = ', '.join([career.name for career in offer.careers.all()])
    
    from accounts.models import Career
    careers_data = [{'id': c.id, 'name': c.name} for c in Career.objects.all()]
    
    return render(request, 'offers/internship_form.html', {
        'form': form,
        'action': 'Edit',
        'careers_data': careers_data,
        'offer_careers_str': offer_careers_str,
    })


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
def reopen_offer(request, offer_id):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    offer = InternshipOffer.objects.get(id=offer_id, company=profile)
    offer.status = 'open'
    offer.closed_at = None
    offer.save()
    return redirect('company_offers')


@login_required
def delete_offer(request, offer_id):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    offer = InternshipOffer.objects.get(id=offer_id, company=profile)
    offer.delete()
    return redirect('company_offers')


@login_required
def company_offers(request):
    if request.user.role != 'company':
        return redirect('home')
    profile = CompanyProfile.objects.get(user=request.user)
    offers = profile.offers.all().order_by('-created_at')
    return render(request, 'offers/company_offers.html', {'offers': offers, 'profile': profile})
