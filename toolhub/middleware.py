from django.shortcuts import redirect
from django.urls import reverse

class SuperuserAdminOnlyMiddleware:
    """
    If a superuser attempts to visit any URL outside of /admin/,
    redirect them to the admin dashboard.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply if user is authenticated and is a superuser.
        if request.user.is_authenticated and request.user.is_superuser:
            if not request.path.startswith('/admin/') and not request.path.startswith('/static/') and not request.path.startswith('/media/'):
                return redirect(reverse('admin:index'))
        response = self.get_response(request)
        return response