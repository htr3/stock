#!/usr/bin/env python3
"""
QUICKSTART: Stock Price Prediction ML Model
Execute this to get started in 2 minutes

Run: python quickstart.py
"""

import subprocess
import sys
import os
from pathlib import Path


def print_banner():
    """Print welcome banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║   🚀 STOCK PRICE PREDICTION ML MODEL - QUICKSTART 🚀            ║
    ║                                                                  ║
    ║   Predict if stock price goes UP (+70%) or DOWN (-30%)          ║
    ║   in the next 10 minutes using Machine Learning                 ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)


def step_1_install():
    """Step 1: Install dependencies"""
    print("\n" + "="*70)
    print("STEP 1: Installing Dependencies")
    print("="*70)
    print("This installs: pandas, sklearn, xgboost, lightgbm, matplotlib...")
    
    try:
        subprocess.check_call([sys.executable, 'setup.py'])
        print("✅ Dependencies installed successfully!")
        return True
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False


def step_2_generate_data():
    """Step 2: Generate sample data"""
    print("\n" + "="*70)
    print("STEP 2: Generating Sample Stock Data")
    print("="*70)
    print("Creating 2000 sample candles for testing...")
    
    try:
        subprocess.check_call([sys.executable, 'generate_sample_data.py'])
        print("✅ Sample data created: stock_data.csv")
        return True
    except Exception as e:
        print(f"❌ Data generation failed: {e}")
        return False


def step_3_train_models():
    """Step 3: Train models"""
    print("\n" + "="*70)
    print("STEP 3: Training ML Models")
    print("="*70)
    print("""
    This will:
    ✓ Generate 50+ ML features from technical analysis
    ✓ Train 5 different algorithms (Logistic, Random Forest, XGBoost, etc)
    ✓ Compare performance on test data
    ✓ Save the best model for predictions
    ✓ Plot feature importance
    
    This takes 2-5 minutes depending on data size...
    """)
    
    input("Press ENTER to start training... ")
    
    try:
        subprocess.check_call([sys.executable, 'main.py'])
        print("\n✅ Model training complete!")
        print("→ Check for: best_model_*.pkl (your trained model)")
        print("→ Check for: model_comparison.png (performance chart)")
        print("→ Check for: feature_importance_*.png (what matters most)")
        return True
    except Exception as e:
        print(f"❌ Training failed: {e}")
        return False


def step_4_explore():
    """Step 4: Explore results"""
    print("\n" + "="*70)
    print("STEP 4: Explore Results & Examples")
    print("="*70)
    print("""
    Files created:
    📊 best_model_xgboost_*.pkl     → Your trained model (ready to use!)
    📈 model_comparison.png          → Visual performance comparison
    🎯 feature_importance_*.png      → Top 20 important features
    
    Next steps:
    1. Open the PNG files to see results
    2. Load the model for predictions:
       
       import joblib
       model = joblib.load('best_model_xgboost_*.pkl')
       predictions = model.predict(new_features)
    
    3. Try examples:
       python examples.py
    
    4. Read detailed guide:
       - IMPLEMENTATION_GUIDE.md  (step-by-step)
       - README.md               (project overview)
       - PROJECT_SUMMARY.md      (what was created)
    """)
    
    print("\n" + "="*70)
    print("✅ QUICKSTART COMPLETE!")
    print("="*70)
    print("""
    You now have:
    ✓ Installed all dependencies
    ✓ Generated sample data
    ✓ Trained 5 ML models
    ✓ Identified best performing model
    ✓ Saved model ready for predictions
    
    🎯 Your trained model is ready to use!
    
    For predictions on new data:
    → Load the .pkl file
    → Generate features using FeatureEngineer
    → Call model.predict() or model.predict_proba()
    
    See examples.py for code examples!
    """)


def main():
    """Run quickstart steps"""
    
    print_banner()
    
    print("\nThis quickstart will:")
    print("  1. Install required Python packages (pandas, sklearn, xgboost, etc)")
    print("  2. Generate sample stock data (2000 candles)")
    print("  3. Train 5 ML models to predict UP/DOWN movement")
    print("  4. Show you the results and next steps")
    print("\nTotal time: ~5-10 minutes\n")
    
    start = input("Continue? (yes/no): ").strip().lower()
    if start not in ['yes', 'y']:
        print("Cancelled. Run: python quickstart.py")
        return
    
    # Run steps
    if not step_1_install():
        print("\n❌ Failed at installation step")
        return
    
    if not step_2_generate_data():
        print("\n❌ Failed at data generation step")
        # Continue anyway - user might have data
    
    if not step_3_train_models():
        print("\n❌ Failed at model training step")
        return
    
    step_4_explore()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✋ Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
