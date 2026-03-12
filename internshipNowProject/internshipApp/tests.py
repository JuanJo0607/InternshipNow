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


class InternshipApplicationTests(TestCase):
    def setUp(self):
        # create company and offer
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
        # student
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
        # company updates
        self.client.login(username='comp', password='pass')
        response = self.client.post(reverse('update_application_status', args=[application.id]), {'status': 'accepted'})
        self.assertEqual(response.status_code, 302)
        application.refresh_from_db()
        self.assertEqual(application.status, 'accepted')
        # try to change again (should redirect without changing)
        response = self.client.post(reverse('update_application_status', args=[application.id]), {'status': 'rejected'})
        application.refresh_from_db()
        self.assertEqual(application.status, 'accepted')

