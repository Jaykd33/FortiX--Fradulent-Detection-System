#!/usr/bin/env python3
"""
FortiX Fraud Detection Model Training and Evaluation Script

This script performs comprehensive ML pipeline:
1. Load data from PostgreSQL
2. Exploratory Data Analysis (EDA)
3. Data preprocessing and feature engineering
4. Model training with Random Forest
5. Model evaluation with detailed metrics
6. Save trained model for production use

Usage:
    python scripts/train_evaluate_model.py
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    confusion_matrix, 
    classification_report, 
    roc_auc_score, 
    roc_curve,
    precision_recall_curve,
    auc
)
import joblib
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add the parent directory to Python path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.db import async_session_factory
from app.models.transaction import Transaction


class FraudDetectionTrainer:
    """Main class for training and evaluating fraud detection models."""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns = []
        self.results = {}
        
    async def load_data(self) -> pd.DataFrame:
        """
        Load credit card transactions from PostgreSQL database.
        
        Returns:
            pd.DataFrame: Loaded transaction data
        """
        print("🔄 Loading data from PostgreSQL database...")
        
        async with async_session_factory() as session:
            # Query for credit card transactions only
            query = select(Transaction).where(Transaction.transaction_type == 'CREDIT_CARD')
            result = await session.execute(query)
            transactions = result.scalars().all()
            
            if not transactions:
                print("⚠️  No credit card transactions found in database!")
                print("💡 Run scripts/ingest_real_data.py first to populate sample data")
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for tx in transactions:
                data.append({
                    'id': str(tx.id),
                    'created_at': tx.created_at,
                    'amount': tx.amount,
                    'currency': tx.currency,
                    'transaction_type': tx.transaction_type,
                    'sender_id': tx.sender_id,
                    'receiver_id': tx.receiver_id,
                    'device_fingerprint': tx.device_fingerprint,
                    'ip_address': tx.ip_address,
                    'geo_location': tx.geo_location,
                    'risk_score': tx.risk_score,
                    'status': tx.status
                })
            
            df = pd.DataFrame(data)
            print(f"✅ Loaded {len(df)} credit card transactions")
            return df
    
    def exploratory_data_analysis(self, df: pd.DataFrame) -> None:
        """
        Perform comprehensive Exploratory Data Analysis.
        
        Args:
            df: Transaction DataFrame
        """
        print("\n" + "="*60)
        print("📊 EXPLORATORY DATA ANALYSIS")
        print("="*60)
        
        # Basic dataset information
        print("\n📋 Dataset Information:")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Data types and info
        print("\n📋 Data Types and Info:")
        df.info()
        
        # Statistical description
        print("\n📋 Statistical Description:")
        print(df.describe())
        
        # Missing values analysis
        print("\n📋 Missing Values Analysis:")
        missing_values = df.isnull().sum()
        missing_percentage = (missing_values / len(df)) * 100
        missing_df = pd.DataFrame({
            'Missing Count': missing_values,
            'Missing Percentage': missing_percentage
        })
        print(missing_df[missing_df['Missing Count'] > 0])
        
        # Class imbalance analysis
        print("\n📋 Class Distribution Analysis:")
        status_counts = df['status'].value_counts()
        status_percentages = (df['status'].value_counts(normalize=True) * 100).round(2)
        
        print("Transaction Status Distribution:")
        for status, count in status_counts.items():
            percentage = status_percentages[status]
            print(f"  {status}: {count} transactions ({percentage}%)")
        
        # Determine fraud class
        fraud_status = 'flagged' if 'flagged' in status_counts.index else status_counts.index[0]
        legitimate_count = len(df) - status_counts[fraud_status]
        fraud_percentage = (status_counts[fraud_status] / len(df)) * 100
        
        print(f"\n🎯 Fraud Detection Target:")
        print(f"  Fraudulent transactions: {status_counts[fraud_status]} ({fraud_percentage:.2f}%)")
        print(f"  Legitimate transactions: {legitimate_count} ({100-fraud_percentage:.2f}%)")
        
        self.results['fraud_percentage'] = fraud_percentage
        self.results['total_transactions'] = len(df)
        
        # Visualizations
        self._create_visualizations(df)
    
    def _create_visualizations(self, df: pd.DataFrame) -> None:
        """Create and save visualization plots."""
        print("\n📊 Creating visualizations...")
        
        # Set up the plotting style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('FortiX Fraud Detection - Data Analysis', fontsize=16, fontweight='bold')
        
        # 1. Amount distribution histogram
        axes[0, 0].hist(df['amount'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].set_title('Transaction Amount Distribution')
        axes[0, 0].set_xlabel('Amount')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Class imbalance count plot
        status_counts = df['status'].value_counts()
        colors = ['lightgreen', 'lightcoral']
        bars = axes[0, 1].bar(status_counts.index, status_counts.values, color=colors)
        axes[0, 1].set_title('Class Distribution (Fraud vs Legitimate)')
        axes[0, 1].set_xlabel('Transaction Status')
        axes[0, 1].set_ylabel('Count')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            axes[0, 1].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{int(height)}', ha='center', va='bottom')
        
        # 3. Amount by status (box plot)
        df.boxplot(column='amount', by='status', ax=axes[1, 0])
        axes[1, 0].set_title('Transaction Amount by Status')
        axes[1, 0].set_xlabel('Status')
        axes[1, 0].set_ylabel('Amount')
        
        # 4. Risk score distribution (if available)
        if 'risk_score' in df.columns and df['risk_score'].notna().sum() > 0:
            risk_scores = df['risk_score'].dropna()
            axes[1, 1].hist(risk_scores, bins=20, alpha=0.7, color='orange', edgecolor='black')
            axes[1, 1].set_title('Risk Score Distribution')
            axes[1, 1].set_xlabel('Risk Score')
            axes[1, 1].set_ylabel('Frequency')
        else:
            axes[1, 1].text(0.5, 0.5, 'No Risk Scores Available', 
                           ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 1].set_title('Risk Score Distribution (No Data)')
        
        plt.tight_layout()
        
        # Save the plot
        output_dir = Path(__file__).parent.parent / 'ml_models'
        output_dir.mkdir(exist_ok=True)
        plot_path = output_dir / 'eda_analysis.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"✅ EDA plots saved to: {plot_path}")
        
        plt.show()
    
    def preprocess_data(self, df: pd.DataFrame) -> tuple:
        """
        Preprocess data and create feature matrix and target vector.
        
        Args:
            df: Raw transaction DataFrame
            
        Returns:
            tuple: (X, y) feature matrix and target vector
        """
        print("\n" + "="*60)
        print("🔧 DATA PREPROCESSING & FEATURE ENGINEERING")
        print("="*60)
        
        # Create a copy for preprocessing
        df_processed = df.copy()
        
        # Feature engineering
        print("\n🔧 Creating features...")
        
        # 1. Numerical features
        numerical_features = ['amount']
        
        # 2. Categorical features (encoded)
        categorical_features = []
        
        # Encode categorical variables
        if 'currency' in df_processed.columns:
            df_processed['currency_encoded'] = self.label_encoder.fit_transform(df_processed['currency'].fillna('unknown'))
            categorical_features.append('currency_encoded')
        
        # 3. Derived features
        # Amount-based features
        df_processed['amount_log'] = np.log1p(df_processed['amount'])  # Log transform for skewed data
        df_processed['amount_sqrt'] = np.sqrt(df_processed['amount'])
        
        # Time-based features (if created_at is available)
        if 'created_at' in df_processed.columns:
            df_processed['hour'] = pd.to_datetime(df_processed['created_at']).dt.hour
            df_processed['day_of_week'] = pd.to_datetime(df_processed['created_at']).dt.dayofweek
            df_processed['is_weekend'] = (df_processed['day_of_week'] >= 5).astype(int)
            categorical_features.extend(['hour', 'day_of_week', 'is_weekend'])
        
        # Binary features for missing values
        df_processed['has_device_fingerprint'] = df_processed['device_fingerprint'].notna().astype(int)
        df_processed['has_ip_address'] = df_processed['ip_address'].notna().astype(int)
        df_processed['has_geo_location'] = df_processed['geo_location'].notna().astype(int)
        
        binary_features = ['has_device_fingerprint', 'has_ip_address', 'has_geo_location']
        
        # Combine all feature columns
        self.feature_columns = numerical_features + ['amount_log', 'amount_sqrt'] + categorical_features + binary_features
        
        # Create feature matrix X
        X = df_processed[self.feature_columns].fillna(0)
        
        # Create target vector y (binary: 1 for fraud, 0 for legitimate)
        y = (df_processed['status'] == 'flagged').astype(int)
        
        print(f"✅ Created feature matrix with {X.shape[1]} features")
        print(f"✅ Features used: {self.feature_columns}")
        print(f"✅ Target distribution: {y.value_counts().to_dict()}")
        
        return X, y
    
    def train_model(self, X: pd.DataFrame, y: pd.Series) -> None:
        """
        Train the Random Forest fraud detection model.
        
        Args:
            X: Feature matrix
            y: Target vector
        """
        print("\n" + "="*60)
        print("🤖 MODEL TRAINING")
        print("="*60)
        
        # Split the data
        print("\n🔄 Splitting data into training and testing sets...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        print(f"✅ Training set: {X_train.shape[0]} samples")
        print(f"✅ Testing set: {X_test.shape[0]} samples")
        
        # Scale features
        print("\n🔄 Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Initialize and train Random Forest model
        print("\n🔄 Training Random Forest Classifier...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight='balanced'  # Handle class imbalance
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        print("✅ Model training completed!")
        
        # Store test data for evaluation
        self.X_test_scaled = X_test_scaled
        self.y_test = y_test
        
        self.results['training_samples'] = len(X_train)
        self.results['testing_samples'] = len(X_test)
    
    def evaluate_model(self) -> None:
        """Evaluate the trained model with comprehensive metrics."""
        print("\n" + "="*60)
        print("📊 MODEL EVALUATION")
        print("="*60)
        
        # Make predictions
        y_pred = self.model.predict(self.X_test_scaled)
        y_pred_proba = self.model.predict_proba(self.X_test_scaled)[:, 1]
        
        # Print algorithm name
        print("\n🤖 Random Forest Classifier Evaluation")
        print("-" * 50)
        
        # Confusion Matrix
        print("\n📊 Confusion Matrix:")
        cm = confusion_matrix(self.y_test, y_pred)
        print("Confusion Matrix:")
        print("                 Predicted")
        print("               0      1")
        print(f"Actual 0    {cm[0,0]:4d}   {cm[0,1]:4d}   (True Negatives, False Positives)")
        print(f"       1    {cm[1,0]:4d}   {cm[1,1]:4d}   (False Negatives, True Positives)")
        
        # Calculate and display metrics
        tn, fp, fn, tp = cm.ravel()
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"\n📊 Key Metrics:")
        print(f"  Accuracy:  {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1-Score:  {f1_score:.4f}")
        
        # Classification Report
        print("\n📊 Detailed Classification Report:")
        print(classification_report(self.y_test, y_pred, 
                                  target_names=['Legitimate', 'Fraud'],
                                  digits=4))
        
        # AUC-ROC Score
        auc_score = roc_auc_score(self.y_test, y_pred_proba)
        print(f"\n📊 AUC-ROC Score: {auc_score:.4f}")
        
        # Additional metrics for imbalanced data
        print(f"\n📊 Additional Metrics for Imbalanced Data:")
        
        # Precision-Recall AUC
        precision_vals, recall_vals, _ = precision_recall_curve(self.y_test, y_pred_proba)
        pr_auc = auc(recall_vals, precision_vals)
        print(f"  Precision-Recall AUC: {pr_auc:.4f}")
        
        # Specificity (True Negative Rate)
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        print(f"  Specificity: {specificity:.4f}")
        
        # Store results
        self.results.update({
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'auc_roc': auc_score,
            'pr_auc': pr_auc,
            'specificity': specificity
        })
        
        # Feature importance
        self._display_feature_importance()
        
        # ROC Curve visualization
        self._plot_roc_curve(self.y_test, y_pred_proba, auc_score)
    
    def _display_feature_importance(self) -> None:
        """Display feature importance from the trained model."""
        print("\n📊 Feature Importance (Top 10):")
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(feature_importance.head(10).to_string(index=False))
        
        # Store feature importance
        self.results['top_features'] = feature_importance.head(10).to_dict('records')
    
    def _plot_roc_curve(self, y_true, y_pred_proba, auc_score) -> None:
        """Plot ROC curve and save it."""
        print("\n📊 Creating ROC curve visualization...")
        
        fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2, 
                label=f'ROC Curve (AUC = {auc_score:.4f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', 
                label='Random Classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic (ROC) Curve')
        plt.legend(loc="lower right")
        plt.grid(True, alpha=0.3)
        
        # Save the plot
        output_dir = Path(__file__).parent.parent / 'ml_models'
        roc_path = output_dir / 'roc_curve.png'
        plt.savefig(roc_path, dpi=300, bbox_inches='tight')
        print(f"✅ ROC curve saved to: {roc_path}")
        
        plt.show()
    
    def save_model(self) -> None:
        """Save the trained model and preprocessing objects."""
        print("\n" + "="*60)
        print("💾 SAVING MODEL")
        print("="*60)
        
        # Create models directory
        output_dir = Path(__file__).parent.parent / 'ml_models'
        output_dir.mkdir(exist_ok=True)
        
        # Save model
        model_path = output_dir / 'fraud_model.joblib'
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'feature_columns': self.feature_columns,
            'training_metadata': {
                'timestamp': datetime.now().isoformat(),
                'algorithm': 'RandomForestClassifier',
                'results': self.results
            }
        }, model_path)
        
        print(f"✅ Model saved to: {model_path}")
        
        # Save feature importance
        importance_path = output_dir / 'feature_importance.csv'
        feature_importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        feature_importance_df.to_csv(importance_path, index=False)
        
        print(f"✅ Feature importance saved to: {importance_path}")
        
        # Save evaluation summary
        summary_path = output_dir / 'model_evaluation_summary.txt'
        with open(summary_path, 'w') as f:
            f.write("FortiX Fraud Detection Model - Evaluation Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Algorithm: Random Forest Classifier\n\n")
            
            f.write("Dataset Information:\n")
            f.write(f"  Total transactions: {self.results.get('total_transactions', 'N/A')}\n")
            f.write(f"  Fraud percentage: {self.results.get('fraud_percentage', 'N/A'):.2f}%\n")
            f.write(f"  Training samples: {self.results.get('training_samples', 'N/A')}\n")
            f.write(f"  Testing samples: {self.results.get('testing_samples', 'N/A')}\n\n")
            
            f.write("Model Performance:\n")
            f.write(f"  Accuracy: {self.results.get('accuracy', 'N/A'):.4f}\n")
            f.write(f"  Precision: {self.results.get('precision', 'N/A'):.4f}\n")
            f.write(f"  Recall: {self.results.get('recall', 'N/A'):.4f}\n")
            f.write(f"  F1-Score: {self.results.get('f1_score', 'N/A'):.4f}\n")
            f.write(f"  AUC-ROC: {self.results.get('auc_roc', 'N/A'):.4f}\n")
            f.write(f"  PR-AUC: {self.results.get('pr_auc', 'N/A'):.4f}\n")
            f.write(f"  Specificity: {self.results.get('specificity', 'N/A'):.4f}\n\n")
            
            f.write("Top 5 Most Important Features:\n")
            for i, feature in enumerate(self.results.get('top_features', [])[:5], 1):
                f.write(f"  {i}. {feature['feature']}: {feature['importance']:.4f}\n")
        
        print(f"✅ Evaluation summary saved to: {summary_path}")
    
    async def run_complete_pipeline(self) -> None:
        """Run the complete ML pipeline from data loading to model saving."""
        print("🚀 Starting FortiX Fraud Detection Model Training Pipeline")
        print("=" * 70)
        
        try:
            # 1. Load data
            df = await self.load_data()
            if df.empty:
                print("❌ No data available for training. Exiting.")
                return
            
            # 2. Exploratory Data Analysis
            self.exploratory_data_analysis(df)
            
            # 3. Data preprocessing
            X, y = self.preprocess_data(df)
            
            # 4. Model training
            self.train_model(X, y)
            
            # 5. Model evaluation
            self.evaluate_model()
            
            # 6. Save model
            self.save_model()
            
            print("\n" + "="*70)
            print("🎉 MODEL TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*70)
            print(f"📊 Final Model Performance:")
            print(f"  Accuracy: {self.results.get('accuracy', 'N/A'):.4f}")
            print(f"  AUC-ROC: {self.results.get('auc_roc', 'N/A'):.4f}")
            print(f"  F1-Score: {self.results.get('f1_score', 'N/A'):.4f}")
            print("\n💡 The trained model is ready for production use!")
            print("📁 Check the ml_models/ directory for saved files.")
            
        except Exception as e:
            print(f"\n❌ Error in training pipeline: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """Main function to run the training pipeline."""
    trainer = FraudDetectionTrainer()
    await trainer.run_complete_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
