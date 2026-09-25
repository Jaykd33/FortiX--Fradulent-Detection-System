# FortiX --- Fraud Detection System

FortiX is a full-stack machine-learning-based fraud detection system for
analyzing financial transactions, assigning risk scores, and presenting
fraud insights through an interactive dashboard.

## Features

-   ML-based fraud prediction
-   Low / Medium / High risk classification
-   Transaction monitoring and analytics
-   Fraud alerts
-   Geographic fraud visualization
-   Dataset upload
-   REST API backend
-   React dashboard

## Tech Stack

**Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, React
Query, Recharts, React Simple Maps

**Backend:** Python, FastAPI, Uvicorn, Scikit-learn, Pandas, NumPy,
Joblib, SQLAlchemy, SQLite/aiosqlite

## ML Pipeline

``` text
Transaction Data
      ↓
ColumnTransformer
  ├── Numerical → StandardScaler
  └── Categorical → OneHotEncoder
      ↓
Random Forest Classifier
      ↓
Prediction / Risk Score
      ↓
Low / Medium / High Risk
```

The saved model uses 18 original transaction features and produces 42
features after preprocessing.

### Random Forest Configuration

-   `n_estimators=100`
-   `criterion="gini"`
-   `max_features="sqrt"`
-   `bootstrap=True`
-   `class_weight="balanced"`
-   `random_state=42`
-   `n_jobs=-1`

Model file:

``` text
fortix_backend/ml_models/fraud_model.joblib
```

## Project Structure

``` text
fortix-guard-engine/
├── fortix_backend/
│   ├── app/
│   ├── ml_models/
│   │   └── fraud_model.joblib
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── ...
└── README.md
```

## Run Locally

### 1. Clone the repository

``` bash
git clone https://github.com/Jaykd33/FortiX--Fradulent-Detection-System.git
cd FortiX--Fradulent-Detection-System
```

### 2. Start the backend

In a terminal:

``` powershell
cd fortix_backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### 3. Start the frontend

Open a second terminal:

``` powershell
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite, normally `http://localhost:5173`.

Keep both terminals running while using FortiX.

## Risk Classification

    Risk Score Classification
  ------------ ----------------
        `< 30` Low Risk
       `30–69` Medium Risk
        `≥ 70` High Risk

These thresholds are application-level business rules, not parameters
learned by the Random Forest.

## Current Status

FortiX currently provides a functional full-stack fraud detection
dashboard with ML model integration, backend APIs, transaction
monitoring, risk classification, KPIs, analytics, alerts, and geographic
visualization.

Areas requiring further production-level work include fully consistent
alert persistence, comprehensive model-performance evaluation, dataset
validation, true real-time processing, authentication, and production
deployment.

## Future Improvements

-   Connect high-risk predictions to persistent alert creation
-   Add comprehensive model evaluation and monitoring
-   Add explainable fraud-risk factors
-   Strengthen dataset/schema validation
-   Add model versioning and drift monitoring
-   Introduce event-driven real-time processing
-   Add authentication and production security

