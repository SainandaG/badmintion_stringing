import joblib
import numpy as np
from sklearn.linear_model import LinearRegression
import os

MODEL_PATH = "backend/services/models/eta_model.pkl"

class MLPredictor:
    def __init__(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
        else:
            self.model = LinearRegression()

    def predict_eta(self, features):
        """
        features: dict with keys like distance, traffic_level, agent_score
        """
        X = np.array([list(features.values())])
        return self.model.predict(X)[0]

    def update_model(self, X_train, y_train):
        self.model.fit(X_train, y_train)
        joblib.dump(self.model, MODEL_PATH)

ml_predictor = MLPredictor()
