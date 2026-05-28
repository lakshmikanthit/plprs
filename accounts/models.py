from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

    EXPERIENCE_LEVELS = [
        (BEGINNER, "Beginner"),
        (INTERMEDIATE, "Intermediate"),
        (ADVANCED, "Advanced"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    headline = models.CharField(max_length=140, blank=True)
    target_role = models.CharField(max_length=120, default="Data Scientist")
    interests = models.TextField(
        blank=True,
        help_text="Comma separated skills, topics, or career interests.",
    )
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVELS,
        default=BEGINNER,
    )
    weekly_learning_goal_hours = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_username()} profile"
