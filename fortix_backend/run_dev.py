#!/usr/bin/env python3
"""
Development server runner for FortiX Backend.
This script starts the FastAPI development server with hot reload.
"""

import subprocess
import sys
import os


def main():
    """Run the development server."""
    
    # Change to the backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    print("🚀 Starting FortiX Backend Development Server...")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("🔄 Hot reload enabled")
    print("=" * 50)
    
    try:
        # Run uvicorn with development settings
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--log-level", "info"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

