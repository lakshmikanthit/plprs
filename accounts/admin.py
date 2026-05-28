from django.contrib import admin

from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "target_role",
        "experience_level",
        "weekly_learning_goal_hours",
        "updated_at",
    )
    search_fields = ("user__username", "user__email", "target_role", "interests")
    list_filter = ("experience_level", "target_role")
