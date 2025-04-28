from django.http import JsonResponse
from django.db.models import Q
from ..models import Item, CustomUser

def search_items(request):
    q = request.GET.get("q", "")
    items = Item.objects.filter(name__icontains=q)[:10]

    data = [
        {
            "id":     i.id,
            "name":   i.name,
            "title":  i.name,
            "status": i.status,
            "status_display": i.get_status_display(),
        }
        for i in items
    ]
    return JsonResponse(data, safe=False)


def search_users_collections(request):
    q = request.GET.get("q", "")
    users = CustomUser.objects.filter(
        Q(username__icontains=q) | Q(email__icontains=q)
    )[:10]

    data = [
        {
            "id":    u.id,
            "name":  u.full_name or u.username,
            "email": u.email,
        }
        for u in users
    ]
    return JsonResponse(data, safe=False)
