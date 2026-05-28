from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import redirect, render
from django.utils import timezone

from recommendations.services import RecommendationEngine

from .forms import SkillAssessmentForm
from .models import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentQuestion,
    CourseProgress,
    LearningPath,
    LearningPathItem,
    Resource,
    StudentSkill,
)


def _get_engine():
    return RecommendationEngine()


def _get_or_create_path(user):
    path = (
        LearningPath.objects.filter(student=user)
        .prefetch_related("items__course", "items__course__skills")
        .first()
    )
    if path:
        return path
    return _get_engine().generate_learning_path(user)


@login_required
def dashboard(request):
    path = _get_or_create_path(request.user)
    student_skills = StudentSkill.objects.filter(student=request.user).select_related("skill")
    completed_courses = CourseProgress.objects.filter(
        student=request.user,
        status=CourseProgress.COMPLETED,
    ).count()
    active_courses = CourseProgress.objects.filter(
        student=request.user,
        status=CourseProgress.IN_PROGRESS,
    ).count()
    avg_progress = (
        CourseProgress.objects.filter(student=request.user).aggregate(avg=Avg("progress_percent"))[
            "avg"
        ]
        or path.overall_progress
    )
    recent_activity = CourseProgress.objects.filter(student=request.user).select_related("course")[:5]

    context = {
        "path": path,
        "student_skills": student_skills,
        "skills_count": student_skills.count(),
        "completed_courses": completed_courses,
        "active_courses": active_courses,
        "overall_progress": round(avg_progress),
        "recent_activity": recent_activity,
    }
    return render(request, "learning/dashboard.html", context)


@login_required
def skill_assessment(request):
    questions = AssessmentQuestion.objects.select_related("skill").order_by("skill__name", "id")[:12]
    student_skills = StudentSkill.objects.filter(student=request.user).select_related("skill")

    if request.method == "POST":
        form = SkillAssessmentForm(request.POST, questions=questions)
        if form.is_valid():
            score, skill_scores, answers = form.grade()
            attempt = AssessmentAttempt.objects.create(student=request.user, score=score)
            AssessmentAnswer.objects.bulk_create(
                [
                    AssessmentAnswer(
                        attempt=attempt,
                        question=answer["question"],
                        selected_option=answer["selected_option"],
                        is_correct=answer["is_correct"],
                    )
                    for answer in answers
                ]
            )
            for skill, proficiency in skill_scores.items():
                StudentSkill.objects.update_or_create(
                    student=request.user,
                    skill=skill,
                    defaults={
                        "proficiency": proficiency,
                        "source": StudentSkill.ASSESSMENT,
                    },
                )
            _get_engine().generate_learning_path(request.user)
            messages.success(request, "Assessment submitted. Your learning path was refreshed.")
            return redirect("learning_path")
    else:
        form = SkillAssessmentForm(questions=questions)

    return render(
        request,
        "learning/skill_assessment.html",
        {
            "form": form,
            "questions_available": questions.exists(),
            "student_skills": student_skills,
        },
    )


@login_required
def learning_path(request):
    path = _get_or_create_path(request.user)

    if request.method == "POST":
        item_id = request.POST.get("item_id")
        action = request.POST.get("action")
        item = path.items.select_related("course").filter(id=item_id).first()
        if item and action == "start":
            item.status = LearningPathItem.IN_PROGRESS
            item.started_at = timezone.now()
            item.save(update_fields=["status", "started_at"])
            CourseProgress.objects.update_or_create(
                student=request.user,
                course=item.course,
                defaults={"status": CourseProgress.IN_PROGRESS, "progress_percent": 25},
            )
        elif item and action == "complete":
            item.status = LearningPathItem.COMPLETED
            item.completed_at = timezone.now()
            item.save(update_fields=["status", "completed_at"])
            CourseProgress.objects.update_or_create(
                student=request.user,
                course=item.course,
                defaults={"status": CourseProgress.COMPLETED, "progress_percent": 100},
            )
        path.recalculate_progress()
        messages.success(request, "Learning path progress updated.")
        return redirect("learning_path")

    return render(request, "learning/learning_path.html", {"path": path})


@login_required
def resource_recommender(request):
    path = _get_or_create_path(request.user)
    next_item = (
        path.items.exclude(status=LearningPathItem.COMPLETED)
        .select_related("course")
        .order_by("order")
        .first()
    )
    if next_item:
        resources = Resource.objects.filter(course=next_item.course)[:8]
    else:
        resources = Resource.objects.all()[:8]

    return render(
        request,
        "learning/resource_recommender.html",
        {
            "path": path,
            "next_item": next_item,
            "resources": resources,
        },
    )


@login_required
def progress_tracking(request):
    path = _get_or_create_path(request.user)
    progress = CourseProgress.objects.filter(student=request.user).select_related("course")
    status_counts = progress.values("status").annotate(total=Count("id"))

    return render(
        request,
        "learning/progress.html",
        {
            "path": path,
            "progress": progress,
            "status_counts": status_counts,
        },
    )
