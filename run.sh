#!/bin/bash
echo "Starting Yelp Review Analyzer..."

# Find conda installation
if [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
    CONDA_ENVS="$HOME/anaconda3/envs"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    CONDA_ENVS="$HOME/miniconda3/envs"
elif [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
    source "/opt/anaconda3/etc/profile.d/conda.sh"
    CONDA_ENVS="/opt/anaconda3/envs"
elif [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/opt/miniconda3/etc/profile.d/conda.sh"
    CONDA_ENVS="/opt/miniconda3/envs"
else
    echo "Could not find Anaconda or Miniconda installation."
    exit 1
fi

conda activate base

# Check if env exists
if [ -d "$CONDA_ENVS/yelp_scraper" ]; then
    echo "Environment found. Skipping setup..."
else
    echo "Environment not found. Running setup..."
    python setup.py
fi

conda activate yelp_scraper
streamlit run scraper_nlp_streamlit.py
