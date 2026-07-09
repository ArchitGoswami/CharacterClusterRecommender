// app.js - Character Cluster Recommender

// Global state
let indexData = null;
let currentCharacter = null;
let isShowMode = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing application...');
    await loadIndex();
    setupEventListeners();
});

// Load the index data
async function loadIndex() {
    try {
        const response = await fetch('web_data/index.json');
        indexData = await response.json();
        console.log('Character data loaded:', indexData);
    } catch (error) {
        console.error('Error loading index:', error);
        showError('Failed to load character database. Please ensure web_data/index.json exists.');
    }
}

// Setup event listeners
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const modeToggle = document.getElementById('modeToggle');

    if (!searchInput || !searchButton || !modeToggle) {
        console.error('Required elements not found!');
        return;
    }

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    searchButton.addEventListener('click', performSearch);
    modeToggle.addEventListener('click', toggleMode);

    console.log('Event listeners setup complete');
}

// Toggle between character and show mode
function toggleMode() {
    isShowMode = !isShowMode;
    const modeToggle = document.getElementById('modeToggle');
    const searchInput = document.getElementById('searchInput');
    
    if (isShowMode) {
        modeToggle.textContent = '🎭 Switch to Character Search';
        searchInput.placeholder = 'Search by show name...';
    } else {
        modeToggle.textContent = '📺 Switch to Show Search';
        searchInput.placeholder = 'Search by character name...';
    }
    
    searchInput.value = '';
    clearResults();
}

// Perform search
async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) {
        showError('Please enter a search term');
        return;
    }

    console.log('Searching for:', query, 'Mode:', isShowMode ? 'show' : 'character');
    showLoading();

    if (isShowMode) {
        await searchShow(query);
    } else {
        await searchCharacter(query);
    }
}

// Search for a character
async function searchCharacter(query) {
    const characterName = findBestMatch(query, Object.keys(indexData.characters));
    
    if (!characterName) {
        showError(`Character "${query}" not found. Try searching for a different character.`);
        return;
    }

    console.log('Found character:', characterName);
    const charInfo = indexData.characters[characterName];
    await loadCharacterDetails(characterName, charInfo.id);
}

// Search for a show
async function searchShow(query) {
    const showName = findBestMatch(query, Object.keys(indexData.shows));
    
    if (!showName) {
        showError(`Show "${query}" not found. Try searching for a different show.`);
        return;
    }

    console.log('Found show:', showName);
    displayShowCharacters(showName, indexData.shows[showName]);
}

// Find best match for query
function findBestMatch(query, options) {
    const queryLower = query.toLowerCase();
    
    // Exact match
    const exactMatch = options.find(opt => opt.toLowerCase() === queryLower);
    if (exactMatch) return exactMatch;
    
    // Contains match
    const containsMatch = options.find(opt => opt.toLowerCase().includes(queryLower));
    if (containsMatch) return containsMatch;
    
    // Fuzzy match
    const fuzzyMatches = options.filter(opt => {
        const optLower = opt.toLowerCase();
        return queryLower.split(' ').some(word => optLower.includes(word));
    });
    
    return fuzzyMatches[0] || null;
}

// Load character details from JSON file
async function loadCharacterDetails(characterName, characterId) {
    try {
        const fileName = findCharacterFile(characterName, characterId);
        console.log('Loading character file:', fileName);
        const response = await fetch(`web_data/characters/${fileName}`);
        const characterData = await response.json();
        
        currentCharacter = characterData;
        displayCharacterDetails(characterData);
        await findSimilarCharacters(characterData);
    } catch (error) {
        console.error('Error loading character:', error);
        showError(`Failed to load character details for "${characterName}"`);
    }
}

// Find character file name
function findCharacterFile(characterName, characterId) {
    const safeName = characterName
        .replace(/[^a-zA-Z0-9]/g, '_')
        .replace(/_+/g, '_')
        .toLowerCase()
        .substring(0, 50);
    return `${characterId}_${safeName}.json`;
}

// Display character details
function displayCharacterDetails(character) {
    const resultsDiv = document.getElementById('results');
    
    let html = `
        <div class="character-card main-character">
            <h2>${escapeHtml(character.name)}</h2>
            <p class="show-name">From: ${escapeHtml(character.show)}</p>
            <p class="trope-count">${character.trope_count} tropes</p>
        </div>

        <div class="tropes-section">
            <h3>Character Tropes</h3>
    `;

    // Display tropes by category
    if (character.tropes_by_category && Object.keys(character.tropes_by_category).length > 0) {
        for (const [category, tropes] of Object.entries(character.tropes_by_category)) {
            if (tropes.length > 0) {
                html += `
                    <div class="trope-category">
                        <h4>${escapeHtml(category)}</h4>
                        <div class="tropes-list">
                            ${tropes.map(trope => `<span class="trope-tag">${escapeHtml(trope)}</span>`).join('')}
                        </div>
                    </div>
                `;
            }
        }
    } else if (character.tropes) {
        // Fallback: display all tropes without categories
        html += `
            <div class="tropes-list">
                ${character.tropes.map(trope => `<span class="trope-tag">${escapeHtml(trope)}</span>`).join('')}
            </div>
        `;
    }

    html += `</div>`;
    html += `<div id="similar-characters"><div class="loading">Finding similar characters...</div></div>`;
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

// Find similar characters using Jaccard similarity
async function findSimilarCharacters(targetCharacter) {
    const targetTropes = new Set(targetCharacter.tropes);
    const similarities = [];

    let processed = 0;
    const maxToProcess = 200; // Limit for faster initial results

    // Calculate similarity with other characters
    for (const [charName, charInfo] of Object.entries(indexData.characters)) {
        if (charName === targetCharacter.name) continue;
        if (processed++ >= maxToProcess) break;

        try {
            const fileName = findCharacterFile(charName, charInfo.id);
            const response = await fetch(`web_data/characters/${fileName}`);
            const otherChar = await response.json();
            
            const otherTropes = new Set(otherChar.tropes);
            const similarity = jaccardSimilarity(targetTropes, otherTropes);
            
            if (similarity > 0.1) { // Only include if at least 10% similar
                similarities.push({
                    name: charName,
                    show: charInfo.show,
                    similarity: similarity,
                    sharedTropes: intersection(targetTropes, otherTropes).size,
                    tropeCount: charInfo.trope_count
                });
            }
        } catch (error) {
            console.error(`Error loading character ${charName}:`, error);
        }
    }

    // Sort by similarity and take top 10
    similarities.sort((a, b) => b.similarity - a.similarity);
    const topSimilar = similarities.slice(0, 10);

    displaySimilarCharacters(topSimilar);
}

// Calculate Jaccard similarity
function jaccardSimilarity(set1, set2) {
    const intersectionSize = intersection(set1, set2).size;
    const unionSize = union(set1, set2).size;
    return unionSize > 0 ? intersectionSize / unionSize : 0;
}

// Set intersection
function intersection(set1, set2) {
    return new Set([...set1].filter(x => set2.has(x)));
}

// Set union
function union(set1, set2) {
    return new Set([...set1, ...set2]);
}

// Display similar characters
function displaySimilarCharacters(similarChars) {
    const container = document.getElementById('similar-characters');
    
    if (!container) {
        console.error('Similar characters container not found');
        return;
    }
    
    if (similarChars.length === 0) {
        container.innerHTML = '<p>No similar characters found.</p>';
        return;
    }

    let html = '<h3>Similar Characters</h3><div class="similar-characters-grid">';
    
    similarChars.forEach(char => {
        const percentage = (char.similarity * 100).toFixed(1);
        const safeName = escapeHtml(char.name).replace(/'/g, '&apos;');
        html += `
            <div class="character-card similar-card" onclick="searchCharacterByName('${safeName}')">
                <h4>${escapeHtml(char.name)}</h4>
                <p class="show-name">${escapeHtml(char.show)}</p>
                <div class="similarity-bar">
                    <div class="similarity-fill" style="width: ${percentage}%"></div>
                </div>
                <p class="similarity-text">${percentage}% similar (${char.sharedTropes} shared tropes)</p>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Search character by name (for clicking similar characters)
async function searchCharacterByName(name) {
    // Decode HTML entities
    const textarea = document.createElement('textarea');
    textarea.innerHTML = name;
    const decodedName = textarea.value;
    
    document.getElementById('searchInput').value = decodedName;
    if (isShowMode) {
        toggleMode();
    }
    await searchCharacter(decodedName);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Display show characters
function displayShowCharacters(showName, characters) {
    const resultsDiv = document.getElementById('results');
    
    characters.sort((a, b) => b.trope_count - a.trope_count);
    
    let html = `
        <div class="show-header">
            <h2>${escapeHtml(showName)}</h2>
            <p>${characters.length} characters</p>
        </div>
        <div class="show-characters-grid">
    `;
    
    characters.forEach(char => {
        const safeName = escapeHtml(char.name).replace(/'/g, '&apos;');
        html += `
            <div class="character-card" onclick="searchCharacterByName('${safeName}')">
                <h4>${escapeHtml(char.name)}</h4>
                <p class="trope-count">${char.trope_count} tropes</p>
            </div>
        `;
    });
    
    html += '</div>';
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

// Show loading state
function showLoading() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="loading">Loading...</div>';
    resultsDiv.style.display = 'block';
}

// Show error message
function showError(message) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `<div class="error-message">${escapeHtml(message)}</div>`;
    resultsDiv.style.display = 'block';
}

// Clear results
function clearResults() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';
    resultsDiv.style.display = 'none';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}