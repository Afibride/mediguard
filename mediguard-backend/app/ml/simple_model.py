import math


class SimpleSymptomModel:
    """Lightweight Naive Bayes style model for environments without sklearn."""

    def __init__(self, symptoms: list[str], classes: list[str], log_priors: dict, log_likelihoods: dict, variant: str):
        self.symptoms = symptoms
        self.classes_ = classes
        self.log_priors = log_priors
        self.log_likelihoods = log_likelihoods
        self.variant = variant

    def predict_ranked(self, selected_symptoms: list[str], top_k: int = 5) -> list[dict]:
        selected = {symptom.strip().lower() for symptom in selected_symptoms}
        scores = []
        for disease in self.classes_:
            score = self.log_priors[disease]
            likelihoods = self.log_likelihoods[disease]
            matched = []
            for symptom in self.symptoms:
                present = symptom.lower() in selected
                probability = likelihoods[symptom]
                if present:
                    score += math.log(probability)
                    matched.append(symptom)
                else:
                    score += math.log(1 - probability)
            scores.append((disease, score, matched))

        max_score = max(score for _, score, _ in scores)
        exp_scores = [(disease, math.exp(score - max_score), matched) for disease, score, matched in scores]
        total = sum(score for _, score, _ in exp_scores) or 1
        ranked = [
            {
                "disease": disease,
                "probability": round((score / total) * 100, 2),
                "matched_symptoms": matched,
            }
            for disease, score, matched in exp_scores
        ]
        return sorted(ranked, key=lambda item: item["probability"], reverse=True)[:top_k]


class SimpleLabelEncoder:
    def __init__(self, classes: list[str]):
        self.classes_ = classes

    def transform(self, labels: list[str]) -> list[int]:
        return [self.classes_.index(label) for label in labels]

    def inverse_transform(self, indexes: list[int]) -> list[str]:
        return [self.classes_[index] for index in indexes]
