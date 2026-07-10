// app.js - Character Cluster Recommender

// Global state
let indexData = null;
let currentCharacter = null;

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
    }
}

// Initialize theme on load
initTheme();

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
    const themeToggle = document.getElementById('themeToggle');

    if (!searchInput || !searchButton || !themeToggle) {
        console.error('Required elements not found!');
        return;
    }

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    searchInput.addEventListener('input', debounce(showSuggestions, 200));
    searchInput.addEventListener('focus', (e) => {
        if (e.target.value.trim().length >= 2) {
            showSuggestions(e);
        }
    });

    searchButton.addEventListener('click', performSearch);
    themeToggle.addEventListener('click', toggleTheme);

    // Lucky button event listener
    const luckyBtn = document.getElementById('luckyBtn');
    if (luckyBtn) {
        luckyBtn.addEventListener('click', async () => {
            const randomChar = getRandomCharacter();
            if (!randomChar) {
                alert('Unable to load character data. Please try again.');
                return;
            }
            
            // Update search input to show selected character
            searchInput.value = randomChar.name;
            hideSuggestions();
            
            // Load and display the character
            await searchCharacter(randomChar.name);
        });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            hideSuggestions();
        }
    });

    console.log('Event listeners setup complete');
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Show search suggestions
function showSuggestions(e) {
    const query = e.target.value.trim().toLowerCase();
    if (query.length < 2) {
        hideSuggestions();
        return;
    }

    const suggestions = getUnifiedSuggestions(query);
    displaySuggestions(suggestions);
}

// Get unified suggestions (both characters and shows)
function getUnifiedSuggestions(query) {
    const suggestions = [];
    const maxResults = 10;

    // Search characters
    Object.keys(indexData.characters).forEach(charName => {
        if (suggestions.length >= maxResults) return;
        
        if (charName.toLowerCase().includes(query)) {
            const charInfo = indexData.characters[charName];
            suggestions.push({
                type: 'character',
                name: charName,
                show: charInfo.show,
                tropeCount: charInfo.trope_count,
                id: charInfo.id
            });
        }
    });

    // Search shows
    Object.keys(indexData.shows).forEach(showName => {
        if (suggestions.length >= maxResults) return;
        
        if (showName.toLowerCase().includes(query)) {
            const charCount = indexData.shows[showName].length;
            suggestions.push({
                type: 'show',
                name: showName,
                charCount: charCount
            });
        }
    });

    // Sort: exact matches first, then by relevance
    suggestions.sort((a, b) => {
        const aExact = a.name.toLowerCase() === query;
        const bExact = b.name.toLowerCase() === query;
        if (aExact && !bExact) return -1;
        if (!aExact && bExact) return 1;
        
        const aStarts = a.name.toLowerCase().startsWith(query);
        const bStarts = b.name.toLowerCase().startsWith(query);
        if (aStarts && !bStarts) return -1;
        if (!aStarts && bStarts) return 1;
        
        return a.name.localeCompare(b.name);
    });

    return suggestions.slice(0, maxResults);
}

// Display suggestions dropdown
function displaySuggestions(suggestions) {
    let dropdown = document.getElementById('suggestions-dropdown');
    
    if (!dropdown) {
        dropdown = document.createElement('div');
        dropdown.id = 'suggestions-dropdown';
        dropdown.className = 'suggestions-dropdown';
        document.querySelector('.search-container').appendChild(dropdown);
    }

    if (suggestions.length === 0) {
        hideSuggestions();
        return;
    }

    dropdown.innerHTML = suggestions.map(item => {
        if (item.type === 'character') {
            return `
                <div class="suggestion-item" data-type="character" data-name="${escapeAttr(item.name)}">
                    <div class="suggestion-icon">👤</div>
                    <div class="suggestion-content">
                        <div class="suggestion-name">${escapeHtml(item.name)}</div>
                        <div class="suggestion-meta">From: ${escapeHtml(item.show)} • ${item.tropeCount} tropes</div>
                    </div>
                </div>
            `;
        } else {
            return `
                <div class="suggestion-item" data-type="show" data-name="${escapeAttr(item.name)}">
                    <div class="suggestion-icon">📺</div>
                    <div class="suggestion-content">
                        <div class="suggestion-name">${escapeHtml(item.name)}</div>
                        <div class="suggestion-meta">${item.charCount} characters</div>
                    </div>
                </div>
            `;
        }
    }).join('');

    dropdown.style.display = 'block';

    // Add click handlers
    dropdown.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', async () => {
            const name = item.dataset.name;
            const type = item.dataset.type;
            
            document.getElementById('searchInput').value = name;
            hideSuggestions();
            
            if (type === 'character') {
                await searchCharacter(name);
            } else {
                await searchShow(name);
            }
        });
    });
}


function getRandomCharacter() {
    if (!indexData || !indexData.characters) {
        return null;
    }
    
    const characterNames = Object.keys(indexData.characters);
    const randomIndex = Math.floor(Math.random() * characterNames.length);
    const randomName = characterNames[randomIndex];
    const characterData = indexData.characters[randomName];
    
    return {
        name: randomName,
        show: characterData.show,
        id: characterData.id
    };
}

// Hide suggestions
function hideSuggestions() {
    const dropdown = document.getElementById('suggestions-dropdown');
    if (dropdown) {
        dropdown.style.display = 'none';
    }
}

// Perform search (unified)
async function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    if (!query) {
        showError('Please enter a search term');
        return;
    }

    hideSuggestions();
    showLoading();

    // Try to find as character first
    const characterName = findBestMatch(query, Object.keys(indexData.characters));
    if (characterName) {
        await searchCharacter(characterName);
        return;
    }

    // If not found, try as show
    const showName = findBestMatch(query, Object.keys(indexData.shows));
    if (showName) {
        await searchShow(showName);
        return;
    }

    showError(`"${query}" not found. Try searching for a different character or show.`);
}

// Search for a character
async function searchCharacter(query) {
    const characterName = typeof query === 'string' ? 
        findBestMatch(query, Object.keys(indexData.characters)) : query;
    
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
    const showName = typeof query === 'string' ? 
        findBestMatch(query, Object.keys(indexData.shows)) : query;
    
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

// Find character file name - must match prepare_web_data.py logic exactly
function findCharacterFile(characterName, characterId) {
    // This must match the Python script's logic:
    // safe_char_name = re.sub(r'[^a-zA-Z0-9]', '_', char_name)
    // safe_char_name = re.sub(r'_+', '_', safe_char_name).lower()[:50]
    // filename = f"{char_id}_{safe_char_name}.json"
    
    const safeName = characterName
        .replace(/[^a-zA-Z0-9]/g, '_')  // Replace non-alphanumeric with underscore
        .replace(/_+/g, '_')             // Replace multiple underscores with single
        .replace(/^_|_$/g, '')           // Remove leading/trailing underscores
        .toLowerCase()
        .substring(0, 50);
    
    return `${characterId}_${safeName}.json`;
}

// Display character details
function displayCharacterDetails(character) {
    const resultsDiv = document.getElementById('results');
    
    console.log('Displaying character:', character);
    console.log('Tropes:', character.tropes);
    console.log('Tropes by category:', character.tropes_by_category);
    
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
        console.log('Displaying tropes by category');
        for (const [category, tropes] of Object.entries(character.tropes_by_category)) {
            if (tropes && tropes.length > 0) {
                html += `
                    <div class="trope-category">
                        <h4>${escapeHtml(category)}</h4>
                        <div class="tropes-list">
                            ${tropes.map(trope => createTropeLink(trope)).join('')}
                        </div>
                    </div>
                `;
            }
        }
    } else if (character.tropes && character.tropes.length > 0) {
        // Fallback: display all tropes without categories
        console.log('Displaying tropes without categories');
        html += `
            <div class="tropes-list">
                ${character.tropes.map(trope => createTropeLink(trope)).join('')}
            </div>
        `;
    } else {
        console.log('No tropes found!');
        html += `<p>No tropes available for this character.</p>`;
    }

    html += `</div>`;
    html += `<div id="similar-characters"><div class="loading">Finding similar characters...</div></div>`;
    
    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
}

// Create a clickable trope link
function createTropeLink(trope) {
    const tropeUrl = `https://tvtropes.org/pmwiki/pmwiki.php/Main/${trope}`;
    return `<a href="${tropeUrl}" target="_blank" rel="noopener noreferrer" class="trope-tag">${escapeHtml(trope)}</a>`;
}

// Find similar characters using Jaccard similarity
async function findSimilarCharacters(targetCharacter) {
    const targetTropes = new Set(targetCharacter.tropes);
    const similarities = [];

    let processed = 0;
    let successful = 0;
    const maxToProcess = 500; // Check more characters
    const maxSuccessful = 100; // But only process 100 successfully

    // Calculate similarity with other characters
    for (const [charName, charInfo] of Object.entries(indexData.characters)) {
        if (charName === targetCharacter.name) continue;
        if (processed++ >= maxToProcess) break;
        if (successful >= maxSuccessful) break;

        try {
            const fileName = findCharacterFile(charName, charInfo.id);
            const response = await fetch(`web_data/characters/${fileName}`);
            
            if (!response.ok) {
                // File not found, skip silently
                continue;
            }
            
            const otherChar = await response.json();
            successful++;
            
            const otherTropes = new Set(otherChar.tropes);
            const similarity = jaccardSimilarity(targetTropes, otherTropes);
            
            if (similarity > 0.05) { // Lower threshold to get more results
                similarities.push({
                    name: charName,
                    show: charInfo.show,
                    similarity: similarity,
                    sharedTropes: intersection(targetTropes, otherTropes).size,
                    tropeCount: charInfo.trope_count
                });
            }
        } catch (error) {
            // Skip characters that fail to load
            continue;
        }
    }

    // Sort by similarity and take top 10
    similarities.sort((a, b) => b.similarity - a.similarity);
    const topSimilar = similarities.slice(0, 10);

    console.log(`Processed ${processed} characters, ${successful} successful, found ${similarities.length} similar`);
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
        const safeName = escapeAttr(char.name);
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
        const safeName = escapeAttr(char.name);
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

// Escape attribute values
function escapeAttr(text) {
    return text.replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}