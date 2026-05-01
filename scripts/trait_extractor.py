# scripts/trait_extractor.py
"""
Trait extraction pipeline: extract 638-dim trait vectors from text descriptions.

Phase: 2 (Day 3)

Methods:
1. Direct keyword matching
2. Synonym expansion (WordNet)
3. Negation handling
4. TF-IDF weighting

Output: trait_scores dict and trait_vector for each character
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))

from traits import ALL_TRAITS, TRAIT_TO_INDEX, TRAIT_CATEGORY, POSITIVE_TRAITS, NEGATIVE_TRAITS
# Try to import NLTK for synonym expansion
try:
    import nltk
    from nltk.corpus import wordnet
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class TraitExtractor:
    """
    Extract personality traits from character descriptions.
    """
    
    def __init__(self, use_synonyms: bool = True, use_negation: bool = True):
        """
        Initialize trait extractor.
        
        Args:
            use_synonyms: Whether to use WordNet synonym expansion
            use_negation: Whether to handle negation (e.g., "not brave")
        """
        self.use_synonyms = use_synonyms and NLTK_AVAILABLE
        self.use_negation = use_negation
        
        # Build trait matching patterns
        self.trait_patterns = self._build_patterns()
        
        # Precompute synonyms for each trait
        if self.use_synonyms:
            self.trait_synonyms = self._build_synonym_map()
        else:
            self.trait_synonyms = {t.lower(): [t.lower()] for t in ALL_TRAITS}
        
        # Negation words
        self.negation_words = {
            'not', 'never', 'no', 'neither', 'nobody', 'nothing',
            'nowhere', 'hardly', 'barely', 'scarcely', "doesn't",
            "don't", "didn't", "won't", "wouldn't", "couldn't",
            "isn't", "aren't", "wasn't", "weren't"
        }
        
        # IDF scores (to be computed from corpus)
        self.trait_idf = None
    
    def _build_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for each trait."""
        patterns = {}
        for trait in ALL_TRAITS:
            # Match trait as whole word, case insensitive
            pattern = re.compile(r'\b' + re.escape(trait.lower()) + r'\b', re.IGNORECASE)
            patterns[trait.lower()] = pattern
        return patterns
    
    def _build_synonym_map(self) -> Dict[str, List[str]]:
        """Build synonym map using WordNet."""
        synonym_map = {}
        
        for trait in ALL_TRAITS:
            trait_lower = trait.lower()
            synonyms = {trait_lower}
            
            # Get WordNet synonyms
            for syn in wordnet.synsets(trait_lower, pos=wordnet.ADJ):
                for lemma in syn.lemmas():
                    synonyms.add(lemma.name().lower().replace('_', '-'))
            
            synonym_map[trait_lower] = list(synonyms)
        
        return synonym_map
    
    def _check_negation(self, text: str, match_start: int, window: int = 5) -> bool:
        """
        Check if a match is negated by looking at preceding words.
        
        Args:
            text: Full text
            match_start: Start position of the match
            window: Number of words to look back
        
        Returns:
            True if negated, False otherwise
        """
        if not self.use_negation:
            return False
        
        # Get preceding text
        preceding = text[:match_start].lower()
        words = preceding.split()[-window:]
        
        return any(word in self.negation_words for word in words)
    
    def extract_traits(self, text: str) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Extract trait vector and scores from text.
        
        Args:
            text: Character description text
        
        Returns:
            Tuple of (638-dim numpy array, dict of trait->score)
        """
        text_lower = text.lower()
        trait_vector = np.zeros(638)
        trait_scores = {}
        
        for trait in ALL_TRAITS:
            trait_lower = trait.lower()
            idx = TRAIT_TO_INDEX[trait_lower]
            
            # Check for trait and its synonyms
            synonyms = self.trait_synonyms.get(trait_lower, [trait_lower])
            
            score = 0.0
            for synonym in synonyms:
                pattern = re.compile(r'\b' + re.escape(synonym) + r'\b', re.IGNORECASE)
                matches = list(pattern.finditer(text_lower))
                
                for match in matches:
                    # Check for negation
                    if self._check_negation(text_lower, match.start()):
                        # Negated mention - could reduce score or skip
                        continue
                    else:
                        score += 1.0
            
            # Normalize score (cap at 1.0 for now, can adjust)
            score = min(score, 3.0) / 3.0  # Normalize 0-3 mentions to 0-1
            
            if score > 0:
                trait_vector[idx] = score
                trait_scores[trait] = score
        
        return trait_vector, trait_scores
    
    def compute_idf(self, all_descriptions: List[str]) -> None:
        """
        Compute IDF scores for each trait across a corpus.
        
        Args:
            all_descriptions: List of all character descriptions
        """
        n_docs = len(all_descriptions)
        doc_freq = np.zeros(638)
        
        for text in all_descriptions:
            _, trait_scores = self.extract_traits(text)
            for trait in trait_scores:
                idx = TRAIT_TO_INDEX[trait.lower()]
                doc_freq[idx] += 1
        
        # Compute IDF: log(N / (df + 1))
        self.trait_idf = np.log(n_docs / (doc_freq + 1))
    
    def extract_traits_tfidf(self, text: str) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Extract traits with TF-IDF weighting.
        
        Args:
            text: Character description
        
        Returns:
            TF-IDF weighted trait vector and scores
        """
        trait_vector, trait_scores = self.extract_traits(text)
        
        if self.trait_idf is not None:
            trait_vector = trait_vector * self.trait_idf
            
            # Update scores dict
            for trait, score in list(trait_scores.items()):
                idx = TRAIT_TO_INDEX[trait.lower()]
                trait_scores[trait] = score * self.trait_idf[idx]
        
        return trait_vector, trait_scores


def main():
    """Test the trait extractor."""
    extractor = TraitExtractor(use_synonyms=False)  # Start without synonyms for speed
    
    # Test descriptions
    test_cases = [
        ("Jake Peralta", "Jake is fun-loving, childish, and loyal. He's clever but immature, "
         "often acting goofy. Despite his playful nature, he's brave and dedicated to his work."),
        
        ("George Costanza", "George is cowardly, dishonest, and petty. He's insecure and neurotic, "
         "constantly lying to get ahead. Not brave at all, he avoids confrontation."),
        
        ("Leslie Knope", "Leslie is enthusiastic, hardworking, and passionate about her work. "
         "She's optimistic, caring, and incredibly loyal to her friends.")
    ]
    
    print("Trait Extraction Test Results")
    print("=" * 60)
    
    for name, description in test_cases:
        vector, scores = extractor.extract_traits(description)
        
        print(f"\n{name}:")
        print(f"  Traits found: {len(scores)}")
        
        # Sort by score
        sorted_traits = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        print("  Top traits:")
        for trait, score in sorted_traits[:10]:
            category = TRAIT_CATEGORY[trait.lower()]
            print(f"    - {trait}: {score:.2f} ({category})")


if __name__ == "__main__":
    main()# Try to import NLTK for synonym expansion
try:
    import nltk
    from nltk.corpus import wordnet
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class TraitExtractor:
    """
    Extract personality traits from character descriptions.
    """
    
    def __init__(self, use_synonyms: bool = True, use_negation: bool = True):
        """
        Initialize trait extractor.
        
        Args:
            use_synonyms: Whether to use WordNet synonym expansion
            use_negation: Whether to handle negation (e.g., "not brave")
        """
        self.use_synonyms = use_synonyms and NLTK_AVAILABLE
        self.use_negation = use_negation
        
        # Build trait matching patterns
        self.trait_patterns = self._build_patterns()
        
        # Precompute synonyms for each trait
        if self.use_synonyms:
            self.trait_synonyms = self._build_synonym_map()
        else:
            self.trait_synonyms = {t.lower(): [t.lower()] for t in ALL_TRAITS}
        
        # Negation words
        self.negation_words = {
            'not', 'never', 'no', 'neither', 'nobody', 'nothing',
            'nowhere', 'hardly', 'barely', 'scarcely', "doesn't",
            "don't", "didn't", "won't", "wouldn't", "couldn't",
            "isn't", "aren't", "wasn't", "weren't"
        }
        
        # IDF scores (to be computed from corpus)
        self.trait_idf = None
    
    def _build_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for each trait."""
        patterns = {}
        for trait in ALL_TRAITS:
            # Match trait as whole word, case insensitive
            pattern = re.compile(r'\b' + re.escape(trait.lower()) + r'\b', re.IGNORECASE)
            patterns[trait.lower()] = pattern
        return patterns
    
    def _build_synonym_map(self) -> Dict[str, List[str]]:
        """Build synonym map using WordNet."""
        synonym_map = {}
        
        for trait in ALL_TRAITS:
            trait_lower = trait.lower()
            synonyms = {trait_lower}
            
            # Get WordNet synonyms
            for syn in wordnet.synsets(trait_lower, pos=wordnet.ADJ):
                for lemma in syn.lemmas():
                    synonyms.add(lemma.name().lower().replace('_', '-'))
            
            synonym_map[trait_lower] = list(synonyms)
        
        return synonym_map
    
    def _check_negation(self, text: str, match_start: int, window: int = 5) -> bool:
        """
        Check if a match is negated by looking at preceding words.
        
        Args:
            text: Full text
            match_start: Start position of the match
            window: Number of words to look back
        
        Returns:
            True if negated, False otherwise
        """
        if not self.use_negation:
            return False
        
        # Get preceding text
        preceding = text[:match_start].lower()
        words = preceding.split()[-window:]
        
        return any(word in self.negation_words for word in words)
    
    def extract_traits(self, text: str) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Extract trait vector and scores from text.
        
        Args:
            text: Character description text
        
        Returns:
            Tuple of (638-dim numpy array, dict of trait->score)
        """
        text_lower = text.lower()
        trait_vector = np.zeros(638)
        trait_scores = {}
        
        for trait in ALL_TRAITS:
            trait_lower = trait.lower()
            idx = TRAIT_TO_INDEX[trait_lower]
            
            # Check for trait and its synonyms
            synonyms = self.trait_synonyms.get(trait_lower, [trait_lower])
            
            score = 0.0
            for synonym in synonyms:
                pattern = re.compile(r'\b' + re.escape(synonym) + r'\b', re.IGNORECASE)
                matches = list(pattern.finditer(text_lower))
                
                for match in matches:
                    # Check for negation
                    if self._check_negation(text_lower, match.start()):
                        # Negated mention - could reduce score or skip
                        continue
                    else:
                        score += 1.0
            
            # Normalize score (cap at 1.0 for now, can adjust)
            score = min(score, 3.0) / 3.0  # Normalize 0-3 mentions to 0-1
            
            if score > 0:
                trait_vector[idx] = score
                trait_scores[trait] = score
        
        return trait_vector, trait_scores
    
    def compute_idf(self, all_descriptions: List[str]) -> None:
        """
        Compute IDF scores for each trait across a corpus.
        
        Args:
            all_descriptions: List of all character descriptions
        """
        n_docs = len(all_descriptions)
        doc_freq = np.zeros(638)
        
        for text in all_descriptions:
            _, trait_scores = self.extract_traits(text)
            for trait in trait_scores:
                idx = TRAIT_TO_INDEX[trait.lower()]
                doc_freq[idx] += 1
        
        # Compute IDF: log(N / (df + 1))
        self.trait_idf = np.log(n_docs / (doc_freq + 1))
    
    def extract_traits_tfidf(self, text: str) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Extract traits with TF-IDF weighting.
        
        Args:
            text: Character description
        
        Returns:
            TF-IDF weighted trait vector and scores
        """
        trait_vector, trait_scores = self.extract_traits(text)
        
        if self.trait_idf is not None:
            trait_vector = trait_vector * self.trait_idf
            
            # Update scores dict
            for trait, score in list(trait_scores.items()):
                idx = TRAIT_TO_INDEX[trait.lower()]
                trait_scores[trait] = score * self.trait_idf[idx]
        
        return trait_vector, trait_scores


def main():
    """Test the trait extractor."""
    extractor = TraitExtractor(use_synonyms=False)  # Start without synonyms for speed
    
    # Test descriptions
    test_cases = [
        ("Jake Peralta", "Jake is fun-loving, childish, and loyal. He's clever but immature, "
         "often acting goofy. Despite his playful nature, he's brave and dedicated to his work."),
        
        ("George Costanza", "George is cowardly, dishonest, and petty. He's insecure and neurotic, "
         "constantly lying to get ahead. Not brave at all, he avoids confrontation."),
        
        ("Leslie Knope", "Leslie is enthusiastic, hardworking, and passionate about her work. "
         "She's optimistic, caring, and incredibly loyal to her friends.")
    ]
    
    print("Trait Extraction Test Results")
    print("=" * 60)
    
    for name, description in test_cases:
        vector, scores = extractor.extract_traits(description)
        
        print(f"\n{name}:")
        print(f"  Traits found: {len(scores)}")
        
        # Sort by score
        sorted_traits = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        print("  Top traits:")
        for trait, score in sorted_traits[:10]:
            category = TRAIT_CATEGORY[trait.lower()]
