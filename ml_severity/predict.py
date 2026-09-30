"""ml_severity/predict.py -- loads trained model, predicts severity for new zones."""
import os
import joblib
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "severity_model.joblib")
_model = None


def _get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"No trained model at {MODEL_PATH} -- run train_model.py first.")
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_severity(incident_type, population_affected, prior_disaster_count):
    model = _get_model()
    row = pd.DataFrame([{"incident_type": incident_type, "population_affected": population_affected,
                          "prior_disaster_count": prior_disaster_count}])
    return float(model.predict(row)[0])


def make_severity_fn(incident_type, population_lookup=None, prior_disaster_lookup=None):
    def severity_fn(county):
        fips = county["fipsCountyCode"]
        population = (population_lookup or {}).get(fips, 50_000)
        prior_count = (prior_disaster_lookup or {}).get(fips, 1)
        return predict_severity(incident_type, population, prior_count)
    return severity_fn
