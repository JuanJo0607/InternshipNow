from django.urls import path
from applications import views

urlpatterns = [
    path('student/offers/<int:offer_id>/apply/', views.apply_to_offer, name='apply_to_offer'),
    path('student/applications/', views.student_applications, name='student_applications'),
    path('company/applications/', views.company_applications, name='company_applications'),
    path('company/applications/<int:application_id>/status/', views.update_application_status, name='update_application_status'),
    path('company/offers/<int:offer_id>/candidates/', views.candidate_ranking, name='candidate_ranking'),
]
