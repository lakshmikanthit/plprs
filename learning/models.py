from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class Course(models.Model):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

    DIFFICULTY_CHOICES = [
        (BEGINNER, "Beginner"),
        (INTERMEDIATE, "Intermediate"),
        (ADVANCED, "Advanced"),
    ]

    title = models.CharField(max_length=180)
    provider = models.CharField(max_length=120, blank=True)
    description = models.TextField()
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default=BEGINNER,
    )
    url = models.URLField(blank=True)
    duration_hours = models.PositiveIntegerField(default=5)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    skills = models.ManyToManyField(Skill, through="CourseSkill", related_name="courses")
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="unlocks",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["difficulty", "title"]

    def __str__(self):
        return self.title


class CourseSkill(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    weight = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )

    class Meta:
        unique_together = ("course", "skill")

    def __str__(self):
        return f"{self.course} -> {self.skill}"


class StudentSkill(models.Model):
    SELF_REPORTED = "self_reported"
    ASSESSMENT = "assessment"
    ACTIVITY = "activity"

    SOURCE_CHOICES = [
        (SELF_REPORTED, "Self reported"),
        (ASSESSMENT, "Assessment"),
        (ACTIVITY, "Learning activity"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_skills",
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default=SELF_REPORTED)
    assessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "skill")
        ordering = ["skill__name"]

    def __str__(self):
        return f"{self.student} - {self.skill}: {self.proficiency}%"


class IndustrySkillRequirement(models.Model):
    target_role = models.CharField(max_length=120)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    required_level = models.PositiveIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    class Meta:
        unique_together = ("target_role", "skill")
        ordering = ["target_role", "skill__name"]

    def __str__(self):
        return f"{self.target_role}: {self.skill} {self.required_level}%"


class AssessmentQuestion(models.Model):
    OPTION_CHOICES = [
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ]

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    difficulty = models.CharField(
        max_length=20,
        choices=Course.DIFFICULTY_CHOICES,
        default=Course.BEGINNER,
    )

    class Meta:
        ordering = ["skill__name", "difficulty"]

    def __str__(self):
        return f"{self.skill}: {self.prompt[:60]}"

    def option_label(self, key):
        return {
            "A": self.option_a,
            "B": self.option_b,
            "C": self.option_c,
            "D": self.option_d,
        }[key]


class AssessmentAttempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assessment_attempts",
    )
    score = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} assessment {self.score}%"


class AssessmentAnswer(models.Model):
    attempt = models.ForeignKey(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1, choices=AssessmentQuestion.OPTION_CHOICES)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.question.skill}: {self.selected_option}"


class LearningPath(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learning_paths",
    )
    title = models.CharField(max_length=180, default="Personalized Learning Path")
    target_role = models.CharField(max_length=120, blank=True)
    overall_progress = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.student} - {self.title}"

    def recalculate_progress(self):
        items = list(self.items.all())
        if not items:
            self.overall_progress = 0
        else:
            completed = sum(1 for item in items if item.status == LearningPathItem.COMPLETED)
            self.overall_progress = round((completed / len(items)) * 100)
        self.save(update_fields=["overall_progress", "updated_at"])


class LearningPathItem(models.Model):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
    ]

    path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name="items",
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    reason = models.TextField(blank=True)
    relevance_score = models.FloatField(default=0.0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("path", "course")

    def __str__(self):
        return f"{self.order}. {self.course.title}"


class CourseProgress(models.Model):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    STATUS_CHOICES = [
        (NOT_STARTED, "Not Started"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_progress",
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NOT_STARTED)
    progress_percent = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    last_activity_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "course")
        ordering = ["-last_activity_at"]

    def __str__(self):
        return f"{self.student} - {self.course}: {self.progress_percent}%"


class Resource(models.Model):
    COURSE = "course"
    VIDEO = "video"
    ARTICLE = "article"
    PRACTICE = "practice"

    RESOURCE_TYPES = [
        (COURSE, "Course"),
        (VIDEO, "Video"),
        (ARTICLE, "Article"),
        (PRACTICE, "Practice"),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="resources",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=180)
    platform = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)

    class Meta:
        ordering = ["-rating", "title"]

    def __str__(self):
        return self.title


class ResourceInteraction(models.Model):
    VIEWED = "viewed"
    SAVED = "saved"
    COMPLETED = "completed"

    ACTION_CHOICES = [
        (VIEWED, "Viewed"),
        (SAVED, "Saved"),
        (COMPLETED, "Completed"),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    score = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} {self.action} {self.resource}"


class Feedback(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    comment = models.TextField()
    sentiment_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} feedback for {self.course}"
