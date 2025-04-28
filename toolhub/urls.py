from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from .views.home_views import home
from .views.profile_views import (
    profile_view,
    upload_picture,
    clear_profile_picture,
    update_profile,
    logout_view,
    search_users,
)
from .views.item_views import add_item, tools_page, edit_item, delete_item, view_item
from .views.collection_views import (
    add_collection,
    view_collection,
    edit_collection,
    delete_collection,
    collections_page,
)
from .views.borrow_views import (
    request_borrow,
    approve_borrow,
    deny_borrow,
    borrow_overview,
    borrow_request_detail,
    cancel_borrow_request,
    return_item,
    
)
from .views.api import search_items, search_users_collections

def access_denied(request):
    return render(request, "toolhub/access_denied.html")

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Authentication
    path("accounts/", include("allauth.urls")),

    # Home
    path("", home, name="home"),

    # Profile
    path("profile/", profile_view, name="profile"),
    path("profile/upload-profile-picture/", upload_picture, name="upload_profile_picture"),
    path("profile/clear-profile-picture/", clear_profile_picture, name="clear_profile_picture"),
    path("profile/update/", update_profile, name="update_profile"),
    path("logout/", logout_view, name="logout"),
    path("promote-user/", search_users, name="search_users"),

    # Items
    path("items/new/", add_item, name="add_item"),
    path("tools/", tools_page, name="tools_page"),
    path("items/<int:item_id>/edit/", edit_item, name="edit_item"),
    path("items/<int:item_id>/delete/", delete_item, name="delete_item"),
    path("items/<int:item_id>/", view_item, name="view_item"),

    # Collections
    path("collections/new/", add_collection, name="add_collection"),
    path("collections/<uuid:collection_uuid>/", view_collection, name="view_collection"),
    path("collections/<uuid:collection_uuid>/edit/", edit_collection, name="edit_collection"),
    path("collections/<uuid:collection_uuid>/delete/", delete_collection, name="delete_collection"),
    path("collections/", collections_page, name="collections_page"),
    path("api/search-items/", search_items, name="api_search_items"),
    path("api/search-users/", search_users_collections, name="api_search_users"),

    # Borrow
    path("borrow/request/<int:request_id>/", borrow_request_detail, name="borrow_request_detail"),
    
    # Borrow-Librarian
    path("borrow/approve/<int:request_id>/", approve_borrow, name="approve_borrow"),
    path("borrow/deny/<int:request_id>/", deny_borrow, name="deny_borrow"),

    # Borrow-Patron
    path("items/<int:item_id>/request-borrow/", request_borrow, name="request_borrow"),
    path("my-borrow-requests/", borrow_overview, name="my_borrow_requests"),
    path("borrow/cancel/<int:request_id>/", cancel_borrow_request, name="cancel_borrow_request"),

    # Access Denied
    path("access-denied/", access_denied, name="access_denied"),
    path("return_item/<int:item_id>/", return_item, name="return_item"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
