from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.home, name='home'),
    path('logout', views.logoutView, name="logout"), # Allauth handles authentication
    path('profile/', views.profileView, name="profile"),
    path("profile/upload-profile-picture/", views.uploadPicture, name="upload_profile_picture"),
]

# Needed in development (DEBUG=True) because Django does not serve media files automatically.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)