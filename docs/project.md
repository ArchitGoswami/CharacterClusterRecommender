# Character-Based TV/Movie Recommender System
## Project Context Document

**Team Members:** Alison, Archit
**Timeline:** 5 Days
**Due Date:** [INSERT DATE]

---

## 1. PROJECT SUMMARY

We are building a recommender system that suggests TV shows and movies based on 
**character personality similarity**, not genre or plot. 

**Core Insight:** If you love Jake Peralta (Brooklyn 99), you'll love Jessica Day 
(New Girl) because they share traits like "Fun-loving", "Clever", "Loyal", and 
"Childish" — NOT because both shows are sitcoms.

**Novel Features:**
- 638-dimensional personality trait vectors for characters
- Actor analysis (actor = centroid of their character roles)
- SVD-reduced latent character space
- Explainable recommendations ("Similar because both are X, Y, Z")
- Surprise findings (unexpected character similarities)

---

## 2. TIMELINE OVERVIEW

| Day | Phase | Alison Focus | Archit Focus |
|-----|-------|--------------|--------------|
| 1 | Setup + Crawling | TVTropes crawler | IMDb crawler + title list |
| 2 | Crawling | Fandom crawler | Continue IMDb + schema validation |
| 3 | Extraction | Trait extraction pipeline | Vectorization + matrix building |
| 4 | Analysis | Trope extraction + merging | SVD + clustering + actor analysis |
| 5 | Integration | Evaluation + insights | Recommender engine + explanations |

---

## 3. DATA TARGETS

| Metric | Target | Minimum |
|--------|--------|---------|
| Titles (shows/movies) | 3000+ | 2000 |
| Characters | 10000+ | 5000 |
| Actors | 5000+ | 2000 |
| Trait coverage | 638 dims | 638 dims |
| Tropes | 500+ unique | 200 |

---

## 4. PHASE BREAKDOWN

### PHASE 1: DATA COLLECTION (Days 1-2)

**Goal:** Crawl and store raw data for 2000+ titles

#### ALISON - TVTropes + Fandom Crawling

**Day 1: TVTropes Crawler**
- Target: Character pages with trope tags
- Extract: Character name, show/movie, tropes, description
- Output: `data/raw/tvtropes/{title_slug}.json`

**Day 2: Fandom Crawler**
- Target: Character wiki pages
- Extract: Personality sections, relationships, actor
- Output: `data/raw/fandom/{title_slug}.json`

#### ARCHIT - IMDb + Title List

**Day 1: IMDb Crawler + Master Title List**
- Build master list of 2000+ titles (TV + Movies)
- Extract: Title, year, genre, cast, character names
- Output: `data/titles_master.json`, `data/raw/imdb/{title_id}.json`

**Day 2: Continue + Validation**
- Continue crawling
- Build schema validation scripts
- Ensure data quality

**SYNC POINT (End of Day 2):**
- Both share raw data files
- Validate overlap (same characters from different sources)
- Create unified character ID system

---

### PHASE 2: PROCESSING + VECTORIZATION (Days 3-4)

**Goal:** Build 638-dim trait vectors + trope vectors for all characters

#### ALISON - Trait + Trope Extraction

**Day 3: Trait Extraction Pipeline**
- Input: Raw descriptions from TVTropes + Fandom
- Process: Keyword matching → Synonym expansion → Scoring
- Output: `trait_scores` dict per character

**Day 4: Trope Processing + Data Merging**
- Standardize trope names from TVTropes
- Merge data from all sources into unified character records
- Output: `data/processed/characters.json`

#### ARCHIT - Vectorization + SVD

**Day 3: Vectorization**
- Build trait matrix (N characters × 638 traits)
- Build trope matrix (N characters × T tropes)
- Combine into unified feature matrix
- Output: `data/matrices/trait_matrix.npy`, `data/matrices/trope_matrix.npy`

**Day 4: SVD + Clustering + Actor Analysis**
- Apply SVD to reduce dimensions
- Cluster characters (k-means, hierarchical)
- Build actor vectors (centroid of roles)
- Output: `data/matrices/svd_reduced.npy`, `data/processed/actors.json`

**SYNC POINT (End of Day 4):**
- Unified `characters.json` with both trait vectors and trope tags
- SVD-reduced matrix ready
- Actor vectors ready

---

### PHASE 3: RECOMMENDATION + EVALUATION (Day 5)

**Goal:** Build recommender, generate insights, write evaluation

#### ALISON - Evaluation + Insights

**Day 5:**
- Design evaluation methodology
- Run correlation analysis (trait-trait, trope-trope)
- Identify surprise findings
- Generate visualizations (dendrograms, heatmaps)
- Write insights section of report

#### ARCHIT - Recommender Engine

**Day 5:**
- Implement search modes (character, actor, media)
- Implement explanation generation
- Implement disambiguation
- Build simple CLI interface
- Write technical sections of report

**FINAL SYNC (End of Day 5):**
- Merge code
- Finalize writeup
- Package submission

---

## 5. DATA SCHEMAS

### Character Schema
```json
{
  "id": "brooklyn99_jake_peralta",
  "name": "Jake Peralta",
  "media_id": "brooklyn99",
  "media_title": "Brooklyn Nine-Nine",
  "media_type": "TV",
  "media_year": 2013,
  "genres": ["Sitcom", "Comedy", "Crime"],
  "actor_id": "andy_samberg",
  "actor_name": "Andy Samberg",
  "trait_vector": [0.0, 0.95, ...],
  "trait_scores": {
    "Fun-loving": 0.95,
    "Childish": 0.80
  },
  "tropes": ["BunnyEarsLawyer", "ManChild"],
  "description": "A talented but immature detective...",
  "sources": ["tvtropes", "fandom", "imdb"]
}

## Daily Task Checklist

### Day 1
- [ ] **Archit:** Run `crawler_tvtropes.py` on seed titles
- [ ] **Archit:** Run `crawler_imdb.py` to build master title list + crawl IMDb

### Day 2
- [ ] **Archit:** Run `crawler_fandom.py` on master title list
- [ ] **Alison:** Continue IMDb crawling, validate data quality

### Day 3
- [ ] **Alison:** Run `trait_extractor.py` on all crawled descriptions
- [ ] **Archit:** Run `vectorizer.py` to build matrices

### Day 4
- [ ] **Alison:** Merge all data into `characters.json`, extract tropes
- [ ] **Archit:** Run `svd_analysis.py` for SVD + clustering + actor vectors

### Day 5
- [ ] **Alison:** Run evaluation, generate insights, visualizations
- [ ] **Archit:** Finalize `recommender.py`, test end-to-end
- [ ] **Both:** Write report, package submission