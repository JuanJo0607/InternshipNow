from django.urls import path
from internshipApp import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='login'),
    path('register/', views.register, name='register'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/offers/', views.student_offers, name='student_offers'),
    path('student/upload-cv/', views.upload_cv, name='upload_cv'),
    path('student/matching/', views.matching_offers, name='matching_offers'),  # FR-11
    path('company/profile/', views.company_profile, name='company_profile'),
    path('company/offers/', views.company_offers, name='company_offers'),
    path('company/offers/new/', views.create_offer, name='create_offer'),
    path('company/offers/<int:offer_id>/edit/', views.edit_offer, name='edit_offer'),
    path('company/offers/<int:offer_id>/close/', views.close_offer, name='close_offer'),
    path('companies/<int:id>/metrics/', views.company_metrics_api, name='company_metrics_api'),
    path('company/<int:company_id>/metrics/dashboard/', views.company_metrics_page, name='company_metrics_page'),
    path('student/offers/<int:offer_id>/', views.offer_detail, name='offer_detail'),
    # US-08 student application URLs
    path('student/offers/<int:offer_id>/apply/', views.apply_to_offer, name='apply_to_offer'),
    path('student/applications/', views.student_applications, name='student_applications'),
    # US-08 company application management
    path('company/applications/', views.company_applications, name='company_applications'),
    path('company/applications/<int:application_id>/status/', views.update_application_status, name='update_application_status'),
    # US-14: Profile status API
    path('api/profile-status/', views.profile_status, name='profile_status'),
]
