class RiskClassifier:
    """
    Unified pure classifier to determine recommendation and ranking risk category.
    Ensures identical inputs map to identical risk category outputs deterministically.
    """
    def classify(self, confidence: float, volatility: str, reversibility: str) -> str:
        vol = volatility.upper()
        # High Risk: High volatility OR low confidence (< 0.60)
        if vol == "HIGH" or confidence < 0.60:
            return "High"
        # Medium Risk: Medium volatility OR moderate confidence (< 0.75)
        elif vol == "MEDIUM" or confidence < 0.75:
            return "Medium"
        # Low Risk: Low volatility AND high confidence (>= 0.75)
        return "Low"

risk_classifier = RiskClassifier()
