from django.urls import path

from . import views


urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("skill-assessment/", views.skill_assessment, name="skill_assessment"),
    path("learning-path/", views.learning_path, name="learning_path"),
    path("resources/", views.resource_recommender, name="resource_recommender"),
    path("progress/", views.progress_tracking, name="progress_tracking"),
]
