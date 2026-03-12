from django.urls import path
from . import views
from internshipApp import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='login'),
    path('register/', views.register, name='register'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('company/profile/', views.company_profile, name='company_profile'),
]


