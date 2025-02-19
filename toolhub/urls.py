from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout', views.logoutView, name="logout"), # Allauth handles authentication
]