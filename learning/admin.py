from django.contrib import admin

from .models import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentQuestion,
    Course,
    CourseProgress,
    CourseSkill,
    Feedback,
    IndustrySkillRequirement,
    LearningPath,
    LearningPathItem,
    Resource,
    ResourceInteraction,
    Skill,
    StudentSkill,
)


class CourseSkillInline(admin.TabularInline):
    model = CourseSkill
    extra = 1


class LearningPathItemInline(admin.TabularInline):
    model = LearningPathItem
    extra = 0
    readonly_fields = ("relevance_score",)


class AssessmentAnswerInline(admin.TabularInline):
    model = AssessmentAnswer
    extra = 0
    readonly_fields = ("question", "selected_option", "is_correct")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name", "category", "description")
    list_filter = ("category",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "provider", "difficulty", "duration_hours", "rating", "is_active")
    list_filter = ("difficulty", "provider", "is_active")
    search_fields = ("title", "provider", "description")
    filter_horizontal = ("prerequisites",)
    inlines = [CourseSkillInline]


@admin.register(StudentSkill)
class StudentSkillAdmin(admin.ModelAdmin):
    list_display = ("student", "skill", "proficiency", "source", "assessed_at")
    list_filter = ("source", "skill")
    search_fields = ("student__username", "skill__name")


@admin.register(IndustrySkillRequirement)
class IndustrySkillRequirementAdmin(admin.ModelAdmin):
    list_display = ("target_role", "skill", "required_level")
    list_filter = ("target_role",)
    search_fields = ("target_role", "skill__name")


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ("skill", "difficulty", "prompt", "correct_option")
    list_filter = ("skill", "difficulty")
    search_fields = ("prompt", "skill__name")


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "score", "created_at")
    search_fields = ("student__username",)
    inlines = [AssessmentAnswerInline]


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ("student", "title", "target_role", "overall_progress", "updated_at")
    search_fields = ("student__username", "target_role")
    inlines = [LearningPathItemInline]


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "progress_percent", "last_activity_at")
    list_filter = ("status", "course")
    search_fields = ("student__username", "course__title")


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "platform", "resource_type", "rating", "course")
    list_filter = ("platform", "resource_type")
    search_fields = ("title", "platform", "description")


@admin.register(ResourceInteraction)
class ResourceInteractionAdmin(admin.ModelAdmin):
    list_display = ("student", "resource", "action", "score", "created_at")
    list_filter = ("action",)
    search_fields = ("student__username", "resource__title")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "sentiment_score", "created_at")
    search_fields = ("student__username", "course__title", "comment")
