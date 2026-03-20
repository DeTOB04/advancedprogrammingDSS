import subprocess
import sys
import os

ENV_NAME = "yelp_scraper"
PYTHON_VERSION = "3.11"

PACKAGES = [
    "selenium",
    "streamlit",
    "nltk",
    "spacy",
]

def run(cmd, check=True):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, check=check)
    return result.returncode

def main():
    print("=" * 50)
    print("   Yelp Review Analyzer - Environment Setup")
    print("=" * 50)

    # -------------------------
    # 1. Check conda is available
    # -------------------------
    print("\n[1/5] Checking conda...")
    if run("conda --version", check=False) != 0:
        print("❌ Conda not found. Please install Anaconda or Miniconda first.")
        print("   https://www.anaconda.com/download")
        sys.exit(1)
    print("✅ Conda found.")

    # -------------------------
    # 2. Create conda environment
    # -------------------------
    print(f"\n[2/5] Creating conda environment '{ENV_NAME}' (Python {PYTHON_VERSION})...")
    result = run(f"conda env list", check=False)

    # Check if env already exists
    env_check = subprocess.run("conda env list", shell=True, capture_output=True, text=True)
    if ENV_NAME in env_check.stdout:
        print(f"⚠️  Environment '{ENV_NAME}' already exists. Skipping creation.")
    else:
        run(f"conda create -n {ENV_NAME} python={PYTHON_VERSION} -y")
        print(f"Environment '{ENV_NAME}' created.")

    # -------------------------
    # 3. Install pip packages
    # -------------------------
    print(f"\n[3/5] Installing packages into '{ENV_NAME}'...")

    # Get the python executable path inside the env
    if sys.platform == "win32":
        python_path = f"conda run -n {ENV_NAME} python"
        pip_path = f"conda run -n {ENV_NAME} pip"
    else:
        python_path = f"conda run -n {ENV_NAME} python"
        pip_path = f"conda run -n {ENV_NAME} pip"

    for package in PACKAGES:
        print(f"\n  Installing {package}...")
        run(f"{pip_path} install {package}")

    print("All packages installed.")

    # -------------------------
    # 4. Download spaCy model
    # -------------------------
    print("\n[4/5] Downloading spaCy model (en_core_web_sm)...")
    run(f"{python_path} -m spacy download en_core_web_sm")
    print("spaCy model downloaded.")

    # -------------------------
    # 5. Download NLTK data
    # -------------------------
    print("\n[5/5] Downloading NLTK data...")
    run(f'{python_path} -c "import nltk; nltk.download(\'punkt\')"')
    print("NLTK data downloaded.")

    # -------------------------
    # Done
    # -------------------------
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)
    print(f"\nTo run the app:")
    print(f"   conda activate {ENV_NAME}")
    print(f"   streamlit run scraper_nlp_streamlit.py")
    print()

if __name__ == "__main__":
    main()
