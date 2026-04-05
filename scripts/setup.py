"""
Setup and Installation Guide
Run this script to set up the environment
"""

import subprocess
import sys
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.7+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")


def install_dependencies():
    """Install required packages from requirements.txt"""
    print("\n" + "="*70)
    print("Installing Dependencies")
    print("="*70)
    
    requirements_file = Path(__file__).parent / 'requirements.txt'
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        sys.exit(1)
    
    try:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)]
        )
        print("\n✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False


def verify_installation():
    """Verify all packages are installed"""
    print("\n" + "="*70)
    print("Verifying Installation")
    print("="*70)
    
    packages = [
        'pandas', 'numpy', 'sklearn', 'xgboost', 'lightgbm',
        'matplotlib', 'seaborn', 'joblib'
    ]
    
    all_installed = True
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} not installed")
            all_installed = False
    
    return all_installed


def create_directories():
    """Create necessary directories"""
    print("\n" + "="*70)
    print("Creating Directories")
    print("="*70)
    
    dirs = ['data', 'models', 'outputs']
    
    for dir_name in dirs:
        dir_path = Path(__file__).parent / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"✓ {dir_name}/")


def main():
    """Run complete setup"""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║              Stock Price Prediction ML Model Setup               ║
    ║                     Predicting 10-min UP/DOWN                    ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Check Python version
    print("Checking Python version...")
    check_python_version()
    
    # Install dependencies
    if not install_dependencies():
        print("\n⚠️  Some dependencies failed to install")
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        print("\n⚠️  Some packages are not properly installed")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Done
    print("\n" + "="*70)
    print("✓ SETUP COMPLETE!")
    print("="*70)
    print("""
    Next steps:
    
    1. Generate sample data:
       python generate_sample_data.py
    
    2. Run the complete pipeline:
       python main.py
    
    3. Or explore examples:
       python examples.py
    
    4. Read the documentation:
       README.md
    """)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
