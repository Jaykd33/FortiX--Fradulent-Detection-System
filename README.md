# FortiX: AI-Powered Fraud Detection Platform

## 1. Project Overview

FortiX is a web-based platform designed to analyze and detect fraudulent digital transactions. The system is built on a modern tech stack that separates the backend (the "brain") from the frontend (the "face").

The platform's workflow is built for **batch analysis**. A user uploads a dataset of new transactions, which are then scored against a pre-trained machine learning model. The results are then displayed in a rich, interactive dashboard with multiple pages for analysis.

## 2. Technology Stack

### Backend (The "Brain")
* **Framework:** **FastAPI**. A high-performance Python framework for building the API.
* **Server:** **Uvicorn**. The server that runs the FastAPI application.
* **Database:** **PostgreSQL**. A powerful, professional-grade SQL database to store all transactions, alerts, and user feedback.
* **ORM:** **SQLAlchemy (Async)**. The Python "translator" that lets our app talk to the PostgreSQL database using Python code instead of raw SQL.

### Frontend (The "Face")
* **Framework:** **React (with TypeScript/Vite)**. A modern JavaScript library for building interactive, component-based user interfaces.
* **Routing:** **React Router (`react-router-dom`)**. Used to create a multi-page experience.
* **Charts:** **Recharts**. A declarative charting library for building visualizations.
* **Package Manager:** **NPM (Node Package Manager)**. Used to install frontend libraries and run the development server.

### Machine Learning (The "Intelligence")
* **Library:** **Scikit-learn (sklearn)**. The most popular Python library for all-purpose machine learning.
* **Data Handling:** **Pandas**. Used to read, clean, and manipulate the transaction data.
* **Model Storage:** **Joblib**. Used to save our trained model to a file (`fraud_model.joblib`).

---
## 3. Project Pipeline (How it Works)

1.  **Startup:** The FastAPI backend server starts and loads the pre-trained `fraud_model.joblib` into memory. It also connects to the PostgreSQL database.
2.  **Upload:** A user visits the dashboard and uploads a `test.csv` file containing new transactions.
3.  **Analysis (Backend):**
    * The backend receives this file at the `POST /api/dataset/analyze` endpoint.
    * It **clears all old data** from the `Transaction` and `Alert` tables to start a fresh analysis.
    * It reads the CSV and iterates through every single row.
    * For each transaction, it uses the loaded ML model to predict a `risk_score` (0-100).
    * It saves the transaction *and* its new risk score to the `Transaction` table.
    * If a transaction's score is high (e.g., > 70), it also creates a new record in the `Alert` table.
4.  **View (Frontend):**
    * After the upload is complete, the user is redirected to the **Analytics** page.
    * This page (and all other pages) makes new API calls (e.g., `GET /api/analytics/kpis`) to fetch the analysis results that were just saved to the database.
    * The charts and tables are then populated with this data.

---
## 4. The Machine Learning Model

### What Model is Used?
We are using a **`RandomForestClassifier`**.

### Why This Model?
This was a deliberate choice for this project:

* **It's Powerful:** A Random Forest is an "ensemble" model, meaning it's a team of hundreds of small "decision trees" that all vote on the final answer. This makes it highly accurate.
* **It's Good with Your Data:** It's excellent at handling tabular (Excel-like) data and doesn't require as much fine-tuning as other models.
* **It's Explainable:** We can easily extract "feature importances" (e.g., "transaction `amount` was the most important factor"). This is critical for the "Risk Analysis" page.
* **It's Balanced:** It's the perfect balance of power and explainability, avoiding "black box" models like Neural Networks which are much harder to interpret.

### Key Performance Metrics
(Note: These are example metrics. You should replace these with the *actual* metrics from your `train_evaluate_model.py` script's output.)

* **Accuracy:** 99.8%
* **Precision (for "Fraud"):** 0.88
* **Recall (for "Fraud"):** 0.91
* **F1-Score (for "Fraud"):** 0.89

---
## 5. How to Run the Project

1.  **Terminal 1 (Backend):**
    * `cd fortix-guard-engine`
    * `source .venv/Scripts/activate`
    * `cd fortix_backend`
    * `python -m uvicorn app.main:app --reload`
    * (Leave this running)

2.  **Terminal 2 (Frontend):**
    * `cd path/to/frontend_folder`
    * `npm install` (only run this once)
    * `npm run dev` (this starts the server)
    * (Leave this running)

3.  **Access:** Open the `http://localhost:5173` (or whatever URL `npm` gives you) in your browser.