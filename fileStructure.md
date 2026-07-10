character-recommender/
│
├── PROJECT_CONTEXT.md          # Master context file (READ FIRST)
├── requirements.txt            # Python dependencies
├── traits.py                   # Cleaned 638 trait taxonomy
│
├── data/
│   ├── titles_master.json      # Master list of 2000+ titles
│   ├── raw/                    # Raw crawled data
│   │   ├── tvtropes/
│   │   ├── fandom/
│   │   └── imdb/
│   ├── processed/              # Cleaned character data
│   │   ├── characters.json
│   │   └── actors.json
│   └── matrices/               # Feature matrices
│       ├── trait_matrix.npy
│       ├── trope_matrix.npy
│       └── svd_reduced.npy
│
├── scripts                    
│   ├── crawler_tvtropes.py
│   ├── crawler_fandom.py
│   ├── trait_extractor.py
│   └── tests/                
│   ├── crawler_imdb.py
│   ├── vectorizer.py
│   ├── svd_analysis.py
│   ├── recommender.py                  # Shared utilities
│   ├── schemas.py              # Data schemas
│   ├── utils.py                # Common utilities
│   └── config.py               # Configuration
│
├── outputs/                    # Generated outputs
│   ├── insights/
│   ├── visualizations/
│   └── evaluation/
│
└── writeup/
    └── final_report.pdf

    