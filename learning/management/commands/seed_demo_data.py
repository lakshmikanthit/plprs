from django.core.management.base import BaseCommand

from learning.models import (
    AssessmentQuestion,
    Course,
    CourseSkill,
    IndustrySkillRequirement,
    Resource,
    Skill,
)


class Command(BaseCommand):
    help = "Seed demo skills, courses, resources, and assessment questions for PLPRS."

    def handle(self, *args, **options):
        skills = {}
        for name, category in [
            ("Python Programming", "Programming"),
            ("Data Structures", "Computer Science"),
            ("Machine Learning", "Artificial Intelligence"),
            ("Deep Learning", "Artificial Intelligence"),
            ("Data Science", "Analytics"),
            ("Database Management", "Backend"),
        ]:
            skills[name], _ = Skill.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "description": f"Core competency for {name}.",
                },
            )

        courses_data = [
            (
                "Python Programming Basics",
                "Coursera",
                Course.BEGINNER,
                "Learn Python syntax, functions, loops, and problem solving.",
                ["Python Programming"],
            ),
            (
                "Data Structures in Python",
                "GeeksforGeeks",
                Course.INTERMEDIATE,
                "Understand arrays, stacks, queues, linked lists, trees, and hashing.",
                ["Python Programming", "Data Structures"],
            ),
            (
                "Machine Learning Fundamentals",
                "YouTube",
                Course.INTERMEDIATE,
                "Learn supervised learning, model evaluation, and feature engineering.",
                ["Python Programming", "Machine Learning", "Data Science"],
            ),
            (
                "Deep Learning Basics",
                "Coursera",
                Course.ADVANCED,
                "Introduction to neural networks, backpropagation, and embeddings.",
                ["Machine Learning", "Deep Learning"],
            ),
            (
                "Data Science with Python",
                "Coursera",
                Course.INTERMEDIATE,
                "Analyze data with pandas, NumPy, visualization, and statistics.",
                ["Python Programming", "Data Science"],
            ),
            (
                "PostgreSQL for Application Developers",
                "LeetCode",
                Course.INTERMEDIATE,
                "Design relational schemas, write SQL queries, and optimize indexes.",
                ["Database Management"],
            ),
        ]

        courses = {}
        for title, provider, difficulty, description, course_skills in courses_data:
            course, _ = Course.objects.get_or_create(
                title=title,
                defaults={
                    "provider": provider,
                    "difficulty": difficulty,
                    "description": description,
                    "duration_hours": 8,
                    "rating": 4.6,
                    "url": "https://example.com",
                },
            )
            courses[title] = course
            for skill_name in course_skills:
                CourseSkill.objects.get_or_create(
                    course=course,
                    skill=skills[skill_name],
                    defaults={"weight": 0.9},
                )

        prerequisites = [
            ("Data Structures in Python", "Python Programming Basics"),
            ("Machine Learning Fundamentals", "Python Programming Basics"),
            ("Deep Learning Basics", "Machine Learning Fundamentals"),
            ("Data Science with Python", "Python Programming Basics"),
        ]
        for course_title, prerequisite_title in prerequisites:
            courses[course_title].prerequisites.add(courses[prerequisite_title])

        for skill_name, required in [
            ("Python Programming", 80),
            ("Data Structures", 70),
            ("Machine Learning", 75),
            ("Deep Learning", 55),
            ("Data Science", 75),
            ("Database Management", 60),
        ]:
            IndustrySkillRequirement.objects.get_or_create(
                target_role="Data Scientist",
                skill=skills[skill_name],
                defaults={"required_level": required},
            )

        question_data = [
            (
                "Python Programming",
                "Which keyword defines a function in Python?",
                "func",
                "def",
                "lambda-only",
                "method",
                "B",
            ),
            (
                "Data Structures",
                "Which data structure follows first-in-first-out behavior?",
                "Stack",
                "Queue",
                "Tree",
                "Graph",
                "B",
            ),
            (
                "Machine Learning",
                "Which task predicts a continuous numeric value?",
                "Regression",
                "Clustering",
                "Tokenization",
                "Indexing",
                "A",
            ),
            (
                "Deep Learning",
                "Which component updates neural network weights?",
                "Backpropagation",
                "Normalization only",
                "Hashing",
                "SQL joins",
                "A",
            ),
            (
                "Data Science",
                "Which library is commonly used for tabular data analysis?",
                "NumPy only",
                "pandas",
                "Django ORM",
                "Bootstrap",
                "B",
            ),
            (
                "Database Management",
                "What does an index usually improve in a database?",
                "Query lookup speed",
                "Password strength",
                "HTML rendering",
                "Image compression",
                "A",
            ),
        ]
        for skill_name, prompt, a, b, c, d, answer in question_data:
            AssessmentQuestion.objects.get_or_create(
                skill=skills[skill_name],
                prompt=prompt,
                defaults={
                    "option_a": a,
                    "option_b": b,
                    "option_c": c,
                    "option_d": d,
                    "correct_option": answer,
                },
            )

        resource_data = [
            ("Data Structures in Python", "Data Structures in Python", "Coursera", Resource.COURSE),
            ("Data Structures in Python", "Data Structures Tutorial for Beginners", "YouTube", Resource.VIDEO),
            ("Data Structures in Python", "Data Structures Tutorial", "GeeksforGeeks", Resource.ARTICLE),
            ("Data Structures in Python", "Top Data Structures Problems", "LeetCode", Resource.PRACTICE),
            ("Machine Learning Fundamentals", "ML Beginner Roadmap", "Coursera", Resource.COURSE),
            ("Deep Learning Basics", "Neural Networks Explained", "YouTube", Resource.VIDEO),
        ]
        for course_title, title, platform, resource_type in resource_data:
            Resource.objects.get_or_create(
                course=courses[course_title],
                title=title,
                defaults={
                    "platform": platform,
                    "resource_type": resource_type,
                    "url": "https://example.com",
                    "description": f"{platform} resource for {course_title}.",
                    "rating": 4.7,
                },
            )

        self.stdout.write(self.style.SUCCESS("PLPRS demo data seeded."))
