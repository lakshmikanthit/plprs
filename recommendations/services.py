from collections import defaultdict
from math import pow
import random
import re

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.neighbors import NearestNeighbors
except Exception:  # pragma: no cover - used only before dependencies are installed.
    np = None
    TfidfVectorizer = None
    cosine_similarity = None
    NearestNeighbors = None

try:
    import spacy
except Exception:  # pragma: no cover
    spacy = None

from accounts.models import StudentProfile
from learning.models import (
    Course,
    CourseProgress,
    IndustrySkillRequirement,
    LearningPath,
    LearningPathItem,
    StudentSkill,
)


class RecommendationEngine:
    """Hybrid recommendation service for PLPRS learning paths."""

    WEIGHTS = {
        "content": 0.28,
        "skill_gap": 0.24,
        "collaborative": 0.15,
        "knn": 0.12,
        "nlp": 0.10,
        "adaptive": 0.08,
        "deep_learning": 0.03,
    }

    def __init__(self):
        self._nlp = None
        if spacy:
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except Exception:
                self._nlp = None

    def generate_learning_path(self, user, max_courses=5):
        courses = list(
            Course.objects.filter(is_active=True)
            .prefetch_related("skills", "prerequisites")
            .order_by("id")
        )
        if not courses:
            return LearningPath.objects.create(student=user, title="Personalized Learning Path")

        completed_ids = set(
            CourseProgress.objects.filter(
                student=user,
                status=CourseProgress.COMPLETED,
            ).values_list("course_id", flat=True)
        )
        candidates = [course for course in courses if course.id not in completed_ids]
        if not candidates:
            candidates = courses

        score_map = self.score_courses(user, candidates)
        ordered_courses = self.ant_colony_path(candidates, score_map, max_courses=max_courses)

        profile, _ = StudentProfile.objects.get_or_create(user=user)
        path = LearningPath.objects.create(
            student=user,
            title=f"{profile.target_role} Learning Path",
            target_role=profile.target_role,
        )
        LearningPathItem.objects.bulk_create(
            [
                LearningPathItem(
                    path=path,
                    course=course,
                    order=index,
                    status=self._initial_status(user, course),
                    relevance_score=round(score_map.get(course.id, 0), 4),
                    reason=self._reason_for_course(user, course),
                )
                for index, course in enumerate(ordered_courses, start=1)
            ]
        )
        path.recalculate_progress()

        LearningPath.objects.filter(student=user).exclude(id=path.id).delete()
        return path

    def score_courses(self, user, courses):
        scores = defaultdict(float)
        signals = {
            "content": self.content_based_scores(user, courses),
            "skill_gap": self.skill_gap_scores(user, courses),
            "collaborative": self.collaborative_scores(user, courses),
            "knn": self.knn_scores(user, courses),
            "nlp": self.nlp_scores(user, courses),
            "adaptive": self.adaptive_scores(user, courses),
            "deep_learning": self.deep_learning_scores(user, courses),
        }

        for signal_name, signal_scores in signals.items():
            weight = self.WEIGHTS[signal_name]
            for course in courses:
                scores[course.id] += weight * signal_scores.get(course.id, 0)
        return dict(scores)

    def content_based_scores(self, user, courses):
        learner_text = self._learner_text(user)
        course_texts = [self._course_text(course) for course in courses]
        if TfidfVectorizer and cosine_similarity:
            corpus = [learner_text] + course_texts
            matrix = TfidfVectorizer(stop_words="english").fit_transform(corpus)
            similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
            return {
                course.id: float(score)
                for course, score in zip(courses, similarities)
            }
        return {
            course.id: self._keyword_overlap(learner_text, self._course_text(course))
            for course in courses
        }

    def skill_gap_scores(self, user, courses):
        profile, _ = StudentProfile.objects.get_or_create(user=user)
        current = {
            row.skill_id: row.proficiency
            for row in StudentSkill.objects.filter(student=user).select_related("skill")
        }
        requirements = IndustrySkillRequirement.objects.filter(
            target_role__iexact=profile.target_role
        ).select_related("skill")
        gaps = {
            requirement.skill_id: max(requirement.required_level - current.get(requirement.skill_id, 0), 0)
            for requirement in requirements
        }
        max_gap = max(gaps.values(), default=1)

        scores = {}
        for course in courses:
            covered_gap = sum(gaps.get(skill.id, 0) for skill in course.skills.all())
            scores[course.id] = covered_gap / max_gap if max_gap else 0
        return self._normalize(scores)

    def collaborative_scores(self, user, courses):
        similar_students = self._similar_students(user)
        if not similar_students:
            return {course.id: 0 for course in courses}

        progress_rows = CourseProgress.objects.filter(
            student_id__in=similar_students,
            course__in=courses,
        )
        scores = defaultdict(float)
        for row in progress_rows:
            if row.status == CourseProgress.COMPLETED:
                scores[row.course_id] += 1.0
            elif row.status == CourseProgress.IN_PROGRESS:
                scores[row.course_id] += 0.5
        return self._normalize({course.id: scores[course.id] for course in courses})

    def knn_scores(self, user, courses):
        if np is None or NearestNeighbors is None:
            return self.collaborative_scores(user, courses)

        skill_ids = list(
            StudentSkill.objects.values_list("skill_id", flat=True).distinct().order_by("skill_id")
        )
        student_ids = list(
            StudentSkill.objects.values_list("student_id", flat=True).distinct().order_by("student_id")
        )
        if user.id not in student_ids or len(student_ids) < 2 or not skill_ids:
            return {course.id: 0 for course in courses}

        matrix = np.zeros((len(student_ids), len(skill_ids)))
        student_index = {student_id: idx for idx, student_id in enumerate(student_ids)}
        skill_index = {skill_id: idx for idx, skill_id in enumerate(skill_ids)}

        for row in StudentSkill.objects.all():
            matrix[student_index[row.student_id], skill_index[row.skill_id]] = row.proficiency / 100

        neighbors_count = min(4, len(student_ids))
        model = NearestNeighbors(n_neighbors=neighbors_count, metric="cosine")
        model.fit(matrix)
        user_row = student_index[user.id]
        _, indices = model.kneighbors(matrix[user_row].reshape(1, -1))
        neighbor_ids = [student_ids[index] for index in indices.flatten() if student_ids[index] != user.id]

        scores = defaultdict(float)
        for progress in CourseProgress.objects.filter(student_id__in=neighbor_ids, course__in=courses):
            scores[progress.course_id] += progress.progress_percent / 100
        return self._normalize({course.id: scores[course.id] for course in courses})

    def nlp_scores(self, user, courses):
        learner_keywords = self._keywords(self._learner_text(user))
        scores = {}
        for course in courses:
            course_keywords = self._keywords(self._course_text(course))
            if not learner_keywords or not course_keywords:
                scores[course.id] = 0
            else:
                scores[course.id] = len(learner_keywords & course_keywords) / len(
                    learner_keywords | course_keywords
                )
        return scores

    def adaptive_scores(self, user, courses):
        skills = list(StudentSkill.objects.filter(student=user))
        average_skill = (
            sum(skill.proficiency for skill in skills) / len(skills)
            if skills
            else 20
        )
        preferred_difficulty = Course.BEGINNER
        if average_skill >= 70:
            preferred_difficulty = Course.ADVANCED
        elif average_skill >= 40:
            preferred_difficulty = Course.INTERMEDIATE

        difficulty_score = {
            Course.BEGINNER: 0.35,
            Course.INTERMEDIATE: 0.65,
            Course.ADVANCED: 1.0,
        }
        preferred_value = difficulty_score[preferred_difficulty]

        scores = {}
        for course in courses:
            distance = abs(difficulty_score[course.difficulty] - preferred_value)
            scores[course.id] = max(1 - distance, 0)
        return scores

    def deep_learning_scores(self, user, courses):
        # Hook for a trained neural ranking model. Return neutral scores until real data exists.
        return {course.id: 0 for course in courses}

    def ant_colony_path(self, courses, score_map, max_courses=5, ants=20, iterations=25):
        if not courses:
            return []

        course_ids = [course.id for course in courses]
        course_by_id = {course.id: course for course in courses}
        pheromone = {course.id: 1.0 for course in courses}
        best_route = []
        best_quality = -1

        for _ in range(iterations):
            routes = []
            for _ant in range(ants):
                available = set(course_ids)
                route = []
                while available and len(route) < max_courses:
                    eligible = [
                        course_id
                        for course_id in available
                        if self._prerequisites_satisfied(course_by_id[course_id], route)
                    ]
                    if not eligible:
                        eligible = list(available)
                    selected = self._weighted_choice(eligible, pheromone, score_map)
                    route.append(selected)
                    available.remove(selected)

                quality = self._route_quality(route, score_map)
                routes.append((route, quality))
                if quality > best_quality:
                    best_route = route
                    best_quality = quality

            for course_id in pheromone:
                pheromone[course_id] *= 0.85
            for route, quality in routes:
                for index, course_id in enumerate(route):
                    pheromone[course_id] += quality / (index + 1)

        return [course_by_id[course_id] for course_id in best_route]

    def _learner_text(self, user):
        profile, _ = StudentProfile.objects.get_or_create(user=user)
        skills = " ".join(
            f"{student_skill.skill.name} {student_skill.proficiency}"
            for student_skill in StudentSkill.objects.filter(student=user).select_related("skill")
        )
        completed = " ".join(
            progress.course.title
            for progress in CourseProgress.objects.filter(
                student=user,
                status=CourseProgress.COMPLETED,
            ).select_related("course")
        )
        return " ".join(
            [
                profile.target_role,
                profile.interests,
                profile.experience_level,
                skills,
                completed,
            ]
        )

    def _course_text(self, course):
        skills = " ".join(skill.name for skill in course.skills.all())
        return " ".join(
            [
                course.title,
                course.provider,
                course.description,
                course.difficulty,
                skills,
            ]
        )

    def _keywords(self, text):
        if self._nlp:
            doc = self._nlp(text.lower())
            return {
                token.lemma_
                for token in doc
                if token.is_alpha and not token.is_stop and len(token.text) > 2
            }
        return {
            token
            for token in re.findall(r"[a-zA-Z]{3,}", text.lower())
            if token not in {"and", "the", "for", "with", "from"}
        }

    def _keyword_overlap(self, left, right):
        left_words = self._keywords(left)
        right_words = self._keywords(right)
        if not left_words or not right_words:
            return 0
        return len(left_words & right_words) / len(left_words | right_words)

    def _similar_students(self, user):
        user_skills = {
            row.skill_id: row.proficiency
            for row in StudentSkill.objects.filter(student=user)
        }
        if not user_skills:
            return []

        similarities = defaultdict(float)
        for row in StudentSkill.objects.exclude(student=user):
            if row.skill_id in user_skills:
                similarities[row.student_id] += 1 - abs(user_skills[row.skill_id] - row.proficiency) / 100
        return [
            student_id
            for student_id, _score in sorted(
                similarities.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:5]
        ]

    def _initial_status(self, user, course):
        progress = CourseProgress.objects.filter(student=user, course=course).first()
        if progress and progress.status == CourseProgress.COMPLETED:
            return LearningPathItem.COMPLETED
        if progress and progress.status == CourseProgress.IN_PROGRESS:
            return LearningPathItem.IN_PROGRESS
        return LearningPathItem.PENDING

    def _reason_for_course(self, user, course):
        profile, _ = StudentProfile.objects.get_or_create(user=user)
        skill_names = ", ".join(skill.name for skill in course.skills.all()[:3])
        return (
            f"Recommended for {profile.target_role} because it strengthens "
            f"{skill_names or 'your target skills'}."
        )

    def _prerequisites_satisfied(self, course, selected_course_ids):
        prerequisite_ids = set(course.prerequisites.values_list("id", flat=True))
        return prerequisite_ids.issubset(set(selected_course_ids))

    def _weighted_choice(self, eligible, pheromone, score_map):
        alpha = 1.0
        beta = 2.0
        weights = [
            pow(pheromone[course_id], alpha) * pow(score_map.get(course_id, 0.01) + 0.01, beta)
            for course_id in eligible
        ]
        total = sum(weights)
        if total <= 0:
            return random.choice(eligible)

        threshold = random.uniform(0, total)
        running = 0
        for course_id, weight in zip(eligible, weights):
            running += weight
            if running >= threshold:
                return course_id
        return eligible[-1]

    def _route_quality(self, route, score_map):
        if not route:
            return 0
        return sum(score_map.get(course_id, 0) / (index + 1) for index, course_id in enumerate(route))

    def _normalize(self, scores):
        max_score = max(scores.values(), default=0)
        if max_score == 0:
            return {key: 0 for key in scores}
        return {key: value / max_score for key, value in scores.items()}
