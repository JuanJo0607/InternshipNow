from django.urls import path
from offers import views

urlpatterns = [
    path('student/offers/', views.student_offers, name='student_offers'),
    path('student/offers/<int:offer_id>/', views.offer_detail, name='offer_detail'),
    path('company/offers/', views.company_offers, name='company_offers'),
    path('company/offers/new/', views.create_offer, name='create_offer'),
    path('company/offers/<int:offer_id>/edit/', views.edit_offer, name='edit_offer'),
    path('company/offers/<int:offer_id>/close/', views.close_offer, name='close_offer'),
    path('company/offers/<int:offer_id>/reopen/', views.reopen_offer, name='reopen_offer'),
    path('company/offers/<int:offer_id>/delete/', views.delete_offer, name='delete_offer'),
]
