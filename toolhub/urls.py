from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('logout', views.logoutView) # Allauth handles authentication
]