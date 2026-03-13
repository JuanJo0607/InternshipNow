from django.test import TestCase, Client
from django.urls import reverse
from .models import User, CompanyProfile, InternshipOffer

from django.test import TestCase #US-11
from .matching import calculate_match_score, normalize_skills, annotate_offers_with_score #US-11




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
        # El estudiante tiene más skills de las requeridas → 100%
        score = calculate_match_score("Python, Django, SQL, React, Docker", "python, django")
        self.assertEqual(score, 100)