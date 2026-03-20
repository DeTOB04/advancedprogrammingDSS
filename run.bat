
@echo off
echo Starting Yelp Review Analyzer...
 
:: Find conda installation
if exist "%USERPROFILE%\anaconda3\condabin\conda.bat" (
    set CONDA_BAT=%USERPROFILE%\anaconda3\condabin\conda.bat
    set CONDA_ENVS=%USERPROFILE%\anaconda3\envs
) else if exist "%USERPROFILE%\miniconda3\condabin\conda.bat" (
    set CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat
    set CONDA_ENVS=%USERPROFILE%\miniconda3\envs
) else if exist "C:\ProgramData\anaconda3\condabin\conda.bat" (
    set CONDA_BAT=C:\ProgramData\anaconda3\condabin\conda.bat
    set CONDA_ENVS=C:\ProgramData\anaconda3\envs
) else if exist "C:\ProgramData\miniconda3\condabin\conda.bat" (
    set CONDA_BAT=C:\ProgramData\miniconda3\condabin\conda.bat
    set CONDA_ENVS=C:\ProgramData\miniconda3\envs
) else (
    echo Could not find Anaconda or Miniconda installation.
    pause
    exit /b 1
)
 
call "%CONDA_BAT%" activate base
 
:: Check if env exists
if exist "%CONDA_ENVS%\yelp_scraper" (
    echo Environment found. Skipping setup...
) else (
    echo Environment not found. Running setup...
    python setup.py
)
 
call "%CONDA_BAT%" activate yelp_scraper
streamlit run scraper_nlp_streamlit.py
pause