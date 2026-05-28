from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import StudentProfileForm, StudentRegistrationForm
from .models import StudentProfile


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to PLPRS. Start with your skill assessment.")
            return redirect("skill_assessment")
    else:
        form = StudentRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    profile_obj, _ = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = StudentProfileForm(request.POST, instance=profile_obj, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
    else:
        form = StudentProfileForm(instance=profile_obj, user=request.user)

    return render(request, "accounts/profile.html", {"form": form})
