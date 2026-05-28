from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("learning.urls")),
]
