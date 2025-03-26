from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("", views.home, name="home"),
    path("logout", views.logoutView, name="logout"),  # Allauth handles authentication
    path("profile/", views.profileView, name="profile"),
    path(
        "profile/upload-profile-picture/",
        views.uploadPicture,
        name="upload_profile_picture",
    ),
    path("profile/update/", views.update_profile, name="update_profile"),
    path(
        "profile/clear-profile-picture/",
        views.clear_profile_picture,
        name="clear_profile_picture",
    ),
    path("items/new/", views.add_item, name="add_item"),
    path("collections/new/", views.add_collection, name="add_collection"),
    path(
        "collections/<uuid:collection_uuid>/",
        views.view_collection,
        name="view_collection",
    ),
    path("access-denied/", views.access_denied, name="access_denied"),
]

# Needed in development (DEBUG=True) because Django does not serve media files automatically.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
