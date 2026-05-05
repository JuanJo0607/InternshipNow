from django.urls import path
from matching import views

urlpatterns = [
    path('student/matching/', views.matching_offers, name='matching_offers'),
]
