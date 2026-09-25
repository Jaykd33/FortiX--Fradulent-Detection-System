# app/scripts/prepare_model.py

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ---------------------------------------------
# Robust path setup
# ---------------------------------------------
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent                     # fortix_backend/scripts
PROJECT_ROOT = SCRIPT_DIR.parent                    # fortix_backend

# Always import from project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Now this works even when running from project root
from app.services.feature_engineering import engineer_features


# ---------------------------------------------
# Utility functions
# ---------------------------------------------
def detect_feature_types(df: pd.DataFrame, target: str) -> Tuple[List[str], List[str]]:
    """Separate numeric and categorical columns automatically."""
    numeric_cols, categorical_cols = [], []
    for col in df.columns:
        if col == target:
            continue
        if pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique(dropna=True) > 2:
            numeric_cols.append(col)
        else:
            categorical_cols.append(col)
    return numeric_cols, categorical_cols


def build_pipeline(X: pd.DataFrame, y: pd.Series) -> Tuple[Pipeline, List[str], List[str]]:
    """Build preprocessing + RandomForest pipeline."""
    numeric_cols, categorical_cols = detect_feature_types(X, y.name)
    print(f"\nDetected {len(numeric_cols)} numeric features: {numeric_cols}")
    print(f"Detected {len(categorical_cols)} categorical features: {categorical_cols}\n")

    try:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            ("cat", ohe, categorical_cols),
        ],
        remainder="drop",
    )

    clf = RandomForestClassifier(
        n_estimators=200,
        n_jobs=-1,
        random_state=42,
        class_weight="balanced",
    )

    pipe = Pipeline(steps=[("pre", preprocessor), ("rf", clf)])
    return pipe, numeric_cols, categorical_cols


def resolve_input_path(arg_path: str | None) -> Path:
    """Find the dataset file regardless of where the script is executed."""
    # If user passed an absolute path, use it
    if arg_path:
        path = Path(arg_path)
        if path.is_absolute() and path.exists():
            return path
        # Check multiple relative locations
        for base in [Path.cwd(), PROJECT_ROOT, SCRIPT_DIR]:
            candidate = base / path
            if candidate.exists():
                return candidate.resolve()

    # Default: same directory as this script
    default = SCRIPT_DIR / "fraud_training_base.csv"
    if default.exists():
        return default.resolve()

    # If not found anywhere, raise
    raise FileNotFoundError(
        f"Dataset not found. Expected at least one of:\n"
        f" - {SCRIPT_DIR / 'fraud_training_base.csv'}\n"
        f" - {PROJECT_ROOT / 'fortix_backend/scripts/fraud_training_base.csv'}\n"
        f" - (or provide --data-path with full absolute path)"
    )


def resolve_output_path(arg_path: str | None, default_rel: str) -> Path:
    """Resolve output paths (always relative to project root if not absolute)."""
    if arg_path:
        p = Path(arg_path)
        if p.is_absolute():
            return p
        return (PROJECT_ROOT / p).resolve()
    return (PROJECT_ROOT / default_rel).resolve()


# ---------------------------------------------
# Main script
# ---------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Prepare fraud model: feature engineer, train, evaluate, save.")
    parser.add_argument("--data-path", type=str, default=None, help="Path to training CSV.")
    parser.add_argument("--target", type=str, default="Fraud_Label", help="Target column name.")
    parser.add_argument("--output-model", type=str, default=None, help="Output model path (default: ml_models/fraud_model.joblib).")
    parser.add_argument("--feature-importance", type=str, default=None, help="Feature importance CSV path (default: ml_models/feature_importance.csv).")
    args = parser.parse_args()

    # Resolve paths
    data_path = resolve_input_path(args.data_path)
    model_out = resolve_output_path(args.output_model, "ml_models/fraud_model.joblib")
    fi_out = resolve_output_path(args.feature_importance, "ml_models/feature_importance.csv")

    print("======== Path Resolution ========")
    print(f" Script file      : {SCRIPT_PATH}")
    print(f" Project root     : {PROJECT_ROOT}")
    print(f" Training dataset : {data_path}")
    print(f" Model output     : {model_out}")
    print(f" Feature import.  : {fi_out}")
    print("=================================\n")

    # Load dataset
    print(f"Loading dataset from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Loaded shape: {df.shape}")

    if args.target not in df.columns:
        raise ValueError(f"Target column '{args.target}' not found. Columns: {list(df.columns)}")

    # Feature engineering
    print("Engineering features...")
    df_fe = engineer_features(df)

    y = df_fe[args.target].astype(int)
    cols_to_drop = [
        args.target, "Risk_Score", "Transaction_ID", "User_ID",
        "Timestamp", "Transaction_Timestamp"
    ]
    X = df_fe.drop(columns=cols_to_drop, errors="ignore").copy()

    print("\n--- Model Training Setup ---")
    print(f"Dropped columns: {[c for c in cols_to_drop if c in df_fe.columns]}")
    print(f"Total features used: {len(X.columns)}")
    print("----------------------------\n")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Train model
    print("Building and training pipeline...")
    pipe, num_cols, cat_cols = build_pipeline(X_train, y_train)
    pipe.fit(X_train, y_train)

    # Evaluate
    print("\nEvaluating on test set...")
    y_pred = pipe.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred, digits=4))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Feature importances
    fi_df: pd.DataFrame
    try:
        rf: RandomForestClassifier = pipe.named_steps["rf"]
        pre: ColumnTransformer = pipe.named_steps["pre"]
        ohe = pre.named_transformers_["cat"]
        try:
            ohe_feature_names = ohe.get_feature_names_out(cat_cols).tolist()
        except Exception:
            ohe_feature_names = []
            if hasattr(ohe, "categories_"):
                for col, cats in zip(cat_cols, ohe.categories_):
                    ohe_feature_names += [f"{col}_{c}" for c in cats]
        transformed_names = num_cols + ohe_feature_names
        fi_df = pd.DataFrame({
            "feature": transformed_names,
            "importance": rf.feature_importances_[: len(transformed_names)],
        }).sort_values("importance", ascending=False)
    except Exception as e:
        print(f"\nCould not compute feature importances: {e}")
        fi_df = pd.DataFrame({"feature": ["unavailable"], "importance": [0.0]})

    # Save results
    fi_out.parent.mkdir(parents=True, exist_ok=True)
    fi_df.to_csv(fi_out, index=False)
    print(f"\nSaved feature importances to: {fi_out}")

    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_out)
    print(f"Saved trained model to: {model_out}")


if __name__ == "__main__":
    main()
