from django.test import TestCase, Client
from django.urls import reverse
from .models import User, CompanyProfile, InternshipOffer


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
            status='open'
        )
        response = self.client.get(reverse('company_offers'))
        self.assertContains(response, 'Internship 2')

