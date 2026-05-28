from collections import defaultdict

from django import forms

from .models import AssessmentQuestion


class SkillAssessmentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.questions = list(kwargs.pop("questions", AssessmentQuestion.objects.none()))
        super().__init__(*args, **kwargs)
        for question in self.questions:
            self.fields[f"question_{question.id}"] = forms.ChoiceField(
                label=question.prompt,
                choices=[
                    ("A", question.option_a),
                    ("B", question.option_b),
                    ("C", question.option_c),
                    ("D", question.option_d),
                ],
                widget=forms.RadioSelect,
            )

    def grade(self):
        by_skill = defaultdict(lambda: {"correct": 0, "total": 0})
        answers = []
        correct = 0

        for question in self.questions:
            selected = self.cleaned_data.get(f"question_{question.id}")
            is_correct = selected == question.correct_option
            if is_correct:
                correct += 1
            by_skill[question.skill]["total"] += 1
            by_skill[question.skill]["correct"] += int(is_correct)
            answers.append(
                {
                    "question": question,
                    "selected_option": selected,
                    "is_correct": is_correct,
                }
            )

        total = len(self.questions) or 1
        score = round((correct / total) * 100)
        skill_scores = {
            skill: round((values["correct"] / values["total"]) * 100)
            for skill, values in by_skill.items()
        }
        return score, skill_scores, answers
