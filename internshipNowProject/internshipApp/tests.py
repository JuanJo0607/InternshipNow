from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import User, CompanyProfile, InternshipOffer, StudentProfile, InternshipApplication, InternshipOfferView

from .matching import calculate_match_score, normalize_skills, annotate_offers_with_score




class InternshipOfferTests(TestCase):
    def setUp(self):
        # create a company user
        self.company_user = User.objects.create_user(username='comp', password='pass', role='company')
        self.company_profile = CompanyProfile.objects.create(user=self.company_user, company_name='CompCo', industry='Tech', description='Desc')
        self.client = Client()
        self.client.login(username='comp', password='pass')

    def test_create_offer(self):
        response = self.client.post(reverse('create_offer'), {
            'title': 'Internship 1',
            'description': 'Desc',
            'requirements': 'Reqs',
            'desired_skills': 'Skills',
            'location': 'City',
            'salary': '1000.00',
            'modality': 'presencial',
            'status': 'open',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(InternshipOffer.objects.filter(title='Internship 1').exists())

    def test_company_offers_page(self):
        InternshipOffer.objects.create(
            company=self.company_profile,
            title='Internship 2',
            description='Desc',
            requirements='Reqs',
            desired_skills='Skills',
            location='City',
            salary='1500.00',
            modality='virtual',
            status='open'
        )
        response = self.client.get(reverse('company_offers'))
        self.assertContains(response, 'Internship 2')


class CompanyMetricsTests(TestCase):
    def setUp(self):
        self.company_user = User.objects.create_user(username='comp', password='pass', role='company')
        self.company_profile = CompanyProfile.objects.create(user=self.company_user, company_name='CompCo', industry='Tech', description='Desc')
        self.offer = InternshipOffer.objects.create(
            company=self.company_profile,
            title='Internship 1',
            description='Desc',
            requirements='Reqs',
            desired_skills='Skills',
            location='City',
            salary='1000.00',
            modality='presencial',
            status='open'
        )
        self.student_user = User.objects.create_user(username='stud', password='pass', role='student')
        self.student_profile = StudentProfile.objects.create(user=self.student_user, university='U', career='C', skills='S')
        self.client = Client()

    def test_offer_detail_records_view(self):
        self.client.login(username='stud', password='pass')
        response = self.client.get(reverse('offer_detail', args=[self.offer.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(InternshipOfferView.objects.filter(offer=self.offer, student=self.student_profile).exists())

    def test_company_metrics_api_returns_counts(self):
        InternshipOfferView.objects.create(offer=self.offer, student=self.student_profile)
        InternshipApplication.objects.create(student=self.student_profile, offer=self.offer)
        self.offer.status = 'closed'
        self.offer.closed_at = timezone.now() + timedelta(days=4)
        self.offer.save()

        self.client.login(username='comp', password='pass')
        response = self.client.get(reverse('company_metrics_api', args=[self.company_profile.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['totals']['total_views'], 1)
        self.assertEqual(data['totals']['total_applications'], 1)
        self.assertGreaterEqual(data['totals']['average_time_to_close_days'], 4.0)


#US-11
class NormalizeSkillsTest(TestCase):
    def test_basic_normalization(self):
        result = normalize_skills("Python, Django, SQL")
        self.assertEqual(result, {"python", "django", "sql"})

    def test_empty_string(self):
        self.assertEqual(normalize_skills(""), set())

    def test_none_value(self):
        self.assertEqual(normalize_skills(None), set())

    def test_extra_spaces(self):
        result = normalize_skills("  Python ,  SQL  ")
        self.assertEqual(result, {"python", "sql"})

#US-11
class CalculateMatchScoreTest(TestCase):
    def test_perfect_match(self):
        score = calculate_match_score("Python, Django, SQL", "python, django, sql")
        self.assertEqual(score, 100)

    def test_partial_match(self):
        score = calculate_match_score("Python, Django", "python, django, sql")
        self.assertEqual(score, 66)

    def test_no_match(self):
        score = calculate_match_score("Java, Kotlin", "python, django")
        self.assertEqual(score, 0)

    def test_empty_offer_skills(self):
        score = calculate_match_score("Python", "")
        self.assertEqual(score, 0)

    def test_empty_student_skills(self):
        score = calculate_match_score("", "python, django")
        self.assertEqual(score, 0)

    def test_case_insensitive(self):
        score = calculate_match_score("PYTHON, DJANGO", "python, django")
        self.assertEqual(score, 100)

    def test_superset_student_skills(self):
        score = calculate_match_score("Python, Django, SQL, React, Docker", "python, django")
        self.assertEqual(score, 100)


#US-08
class InternshipApplicationTests(TestCase):
    def setUp(self):
        self.company_user = User.objects.create_user(username='comp', password='pass', role='company')
        self.company_profile = CompanyProfile.objects.create(user=self.company_user, company_name='CompCo', industry='Tech', description='Desc')
        self.offer = InternshipOffer.objects.create(
            company=self.company_profile,
            title='Internship 1',
            description='Desc',
            requirements='Reqs',
            desired_skills='Skills',
            location='City',
            salary='1000.00',
            modality='presencial',
            status='open'
        )
        self.student_user = User.objects.create_user(username='stud', password='pass', role='student')
        self.student_profile = StudentProfile.objects.create(user=self.student_user, university='U', career='C', skills='S')
        self.client = Client()

    def test_student_can_apply(self):
        self.client.login(username='stud', password='pass')
        response = self.client.post(reverse('apply_to_offer', args=[self.offer.id]))
        self.assertEqual(response.status_code, 302)
        from .models import InternshipApplication
        self.assertTrue(InternshipApplication.objects.filter(student=self.student_profile, offer=self.offer).exists())

    def test_student_applications_page_shows_entry(self):
        from .models import InternshipApplication
        InternshipApplication.objects.create(student=self.student_profile, offer=self.offer)
        self.client.login(username='stud', password='pass')
        response = self.client.get(reverse('student_applications'))
        self.assertContains(response, 'Internship 1')

    def test_company_applications_page_shows_entry(self):
        from .models import InternshipApplication
        InternshipApplication.objects.create(student=self.student_profile, offer=self.offer)
        self.client.login(username='comp', password='pass')
        response = self.client.get(reverse('company_applications'))
        self.assertContains(response, 'Internship 1')
        self.assertContains(response, 'stud')

    def test_student_cannot_apply_twice(self):
        from .models import InternshipApplication
        InternshipApplication.objects.create(student=self.student_profile, offer=self.offer)
        self.client.login(username='stud', password='pass')
        response = self.client.post(reverse('apply_to_offer', args=[self.offer.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(InternshipApplication.objects.filter(student=self.student_profile, offer=self.offer).count(), 1)

    def test_company_can_change_status_and_lock(self):
        from .models import InternshipApplication
        application = InternshipApplication.objects.create(student=self.student_profile, offer=self.offer)
        self.client.login(username='comp', password='pass')
        response = self.client.post(reverse('update_application_status', args=[application.id]), {'status': 'accepted'})
        self.assertEqual(response.status_code, 302)
        application.refresh_from_db()
        self.assertEqual(application.status, 'accepted')
        response = self.client.post(reverse('update_application_status', args=[application.id]), {'status': 'rejected'})
        application.refresh_from_db()
        self.assertEqual(application.status, 'accepted')