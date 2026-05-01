# shared/config.py
"""
Global configuration for the character recommender project.
"""

import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MATRICES_DIR = DATA_DIR / "matrices"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Create directories if they don't exist
for dir_path in [RAW_DIR / "tvtropes", RAW_DIR / "fandom", RAW_DIR / "imdb",
                 PROCESSED_DIR, MATRICES_DIR, OUTPUTS_DIR / "insights",
                 OUTPUTS_DIR / "visualizations", OUTPUTS_DIR / "evaluation"]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Crawling settings
CRAWL_DELAY = 1.0  # seconds between requests
MAX_RETRIES = 3
TIMEOUT = 30

# User agent for crawling
USER_AGENT = "CharacterRecommenderBot/1.0 (Academic Project; Contact: team@university.edu)"

# SVD settings
SVD_COMPONENTS = 100  # Number of latent dimensions to keep

# Clustering settings
N_CLUSTERS = 50  # For k-means

# File paths
TITLES_MASTER_FILE = DATA_DIR / "titles_master.json"
TITLES_MASTER_TEST_FILE = DATA_DIR / "titles_master_test.json"
CHARACTERS_FILE = PROCESSED_DIR / "characters.json"
ACTORS_FILE = PROCESSED_DIR / "actors.json"
TRAIT_MATRIX_FILE = MATRICES_DIR / "trait_matrix.npy"
TROPE_MATRIX_FILE = MATRICES_DIR / "trope_matrix.npy"
SVD_MATRIX_FILE = MATRICES_DIR / "svd_reduced.npy"