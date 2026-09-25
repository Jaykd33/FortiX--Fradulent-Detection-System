#!/usr/bin/env python3
"""
Verification script to ensure all components are properly set up.
This script checks database connection, imports, and basic functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))


async def verify_database_connection():
    """Verify database connection works."""
    print("🔍 Verifying database connection...")
    
    try:
        from app.core.db import async_session_factory
        from app.models.transaction import Transaction
        from sqlalchemy import select
        
        async with async_session_factory() as session:
            # Try to query the database
            result = await session.execute(select(Transaction).limit(1))
            transactions = result.scalars().all()
            print(f"✅ Database connection successful. Found {len(transactions)} transactions.")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def verify_imports():
    """Verify all required imports work."""
    print("🔍 Verifying imports...")
    
    try:
        # Core imports
        from app.core.config import get_settings
        from app.core.db import Base, async_engine
        from app.models.transaction import Transaction, Alert, Feedback
        from app.schemas.transaction import TransactionCreate, TransactionRead
        from app.services.fraud_engine import fraud_engine
        
        print("✅ Core application imports successful")
        
        # ML imports
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import classification_report
        import joblib
        
        print("✅ ML library imports successful")
        
        # FastAPI imports
        from fastapi import FastAPI
        from app.main import app
        
        print("✅ FastAPI imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def verify_configuration():
    """Verify configuration is properly set up."""
    print("🔍 Verifying configuration...")
    
    try:
        from app.core.config import get_settings
        
        settings = get_settings()
        print(f"✅ App name: {settings.APP_NAME}")
        print(f"✅ Database URL configured: {settings.DATABASE_URL[:20]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration verification failed: {e}")
        return False


def verify_file_structure():
    """Verify all required files exist."""
    print("🔍 Verifying file structure...")
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/core/config.py",
        "app/core/db.py",
        "app/models/transaction.py",
        "app/schemas/transaction.py",
        "app/services/fraud_engine.py",
        "app/api/v1/endpoints/transactions.py",
        "scripts/train_evaluate_model.py",
        "scripts/ingest_real_data.py",
        "scripts/test_training.py",
        "pyproject.toml",
        "README.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = Path(__file__).parent.parent / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True


async def main():
    """Main verification function."""
    print("🚀 FortiX Backend Setup Verification")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run all verification checks
    checks = [
        ("File Structure", verify_file_structure),
        ("Configuration", verify_configuration),
        ("Imports", verify_imports),
        ("Database Connection", verify_database_connection),
    ]
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name} Check:")
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            if not result:
                all_checks_passed = False
                
        except Exception as e:
            print(f"❌ {check_name} check failed with exception: {e}")
            all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 ALL VERIFICATIONS PASSED!")
        print("✅ FortiX Backend is ready for development")
        print("\n💡 Next steps:")
        print("   1. Run: poetry install")
        print("   2. Configure your .env file with database credentials")
        print("   3. Run: poetry run python scripts/test_training.py")
        print("   4. Run: poetry run python scripts/train_evaluate_model.py")
        print("   5. Start the API: poetry run python run_dev.py")
    else:
        print("❌ SOME VERIFICATIONS FAILED!")
        print("Please fix the issues above before proceeding.")
    
    return all_checks_passed


if __name__ == "__main__":
    asyncio.run(main())
