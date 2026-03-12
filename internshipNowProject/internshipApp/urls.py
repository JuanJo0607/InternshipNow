from django.urls import path
from internshipApp import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='login'),
    path('register/', views.register, name='register'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/offers/', views.student_offers, name='student_offers'),
    path('student/upload-cv/', views.upload_cv, name='upload_cv'),
    path('company/profile/', views.company_profile, name='company_profile'),
    path('company/offers/', views.company_offers, name='company_offers'),
    path('company/offers/new/', views.create_offer, name='create_offer'),
    path('company/offers/<int:offer_id>/edit/', views.edit_offer, name='edit_offer'),
    path('company/offers/<int:offer_id>/close/', views.close_offer, name='close_offer'),
]