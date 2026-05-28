from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import StudentProfile


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    target_role = forms.CharField(max_length=120, initial="Data Scientist")
    interests = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        help_text="Example: Python, machine learning, data structures",
    )
    experience_level = forms.ChoiceField(choices=StudentProfile.EXPERIENCE_LEVELS)
    weekly_learning_goal_hours = forms.IntegerField(min_value=1, max_value=40, initial=5)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "target_role",
            "interests",
            "experience_level",
            "weekly_learning_goal_hours",
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                target_role=self.cleaned_data["target_role"],
                interests=self.cleaned_data.get("interests", ""),
                experience_level=self.cleaned_data["experience_level"],
                weekly_learning_goal_hours=self.cleaned_data["weekly_learning_goal_hours"],
            )
        return user


class StudentProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = StudentProfile
        fields = [
            "headline",
            "target_role",
            "interests",
            "experience_level",
            "weekly_learning_goal_hours",
        ]
        widgets = {
            "interests": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = self.user.first_name
        self.fields["last_name"].initial = self.user.last_name
        self.fields["email"].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.first_name = self.cleaned_data.get("first_name", "")
        self.user.last_name = self.cleaned_data.get("last_name", "")
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save()
            profile.save()
        return profile
