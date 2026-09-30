"""ml_severity/train_model.py -- predicts zone severity from features (the "Intelligent" part)."""
import sys, os, random
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

INCIDENT_TYPES = ["Hurricane", "Flood", "Fire", "Tornado", "Severe Storm", "Earthquake"]
INCIDENT_BASE_SEVERITY = {"Hurricane": 7.5, "Flood": 6.5, "Fire": 5.0, "Tornado": 5.5, "Severe Storm": 4.0, "Earthquake": 8.0}


def generate_synthetic_training_data(n_samples=2000, seed=42):
    rng = random.Random(seed)
    rows = []
    for _ in range(n_samples):
        incident_type = rng.choice(INCIDENT_TYPES)
        population_affected = rng.randint(500, 200_000)
        prior_disaster_count = rng.randint(0, 10)
        base = INCIDENT_BASE_SEVERITY[incident_type]
        pop_effect = min(population_affected / 40_000, 3.0)
        prior_effect = prior_disaster_count * 0.1
        noise = rng.gauss(0, 0.7)
        severity = max(0.0, min(10.0, base + pop_effect + prior_effect + noise))
        rows.append({"incident_type": incident_type, "population_affected": population_affected,
                      "prior_disaster_count": prior_disaster_count, "severity": severity})
    return pd.DataFrame(rows)


def build_pipeline():
    preprocessor = ColumnTransformer(transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["incident_type"]),
    ], remainder="passthrough")
    return Pipeline(steps=[("preprocess", preprocessor), ("model", RandomForestRegressor(n_estimators=200, random_state=42))])


def train_and_evaluate(df, model_out_path=None):
    X = df[["incident_type", "population_affected", "prior_disaster_count"]]
    y = df["severity"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    mae = mean_absolute_error(y_test, pipeline.predict(X_test))
    if model_out_path:
        joblib.dump(pipeline, model_out_path)
    return pipeline, mae


if __name__ == "__main__":
    df = generate_synthetic_training_data()
    model_path = os.path.join(os.path.dirname(__file__), "severity_model.joblib")
    pipeline, mae = train_and_evaluate(df, model_out_path=model_path)
    print(f"Trained on {len(df)} synthetic samples. MAE: {mae:.3f} (0-10 scale)")
