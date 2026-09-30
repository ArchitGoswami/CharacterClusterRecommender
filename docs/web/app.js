// app.js - Character Cluster Recommender

// Base URL for data files
const BASE_URL = 'web_data';

// Global state
let indexData = null;
let currentCharacter = null;

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
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
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
        meta.setAttribute('content', theme === 'light' ? '#ffffff' : '#000000');
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
        const response = await fetch(`${BASE_URL}/index.json`);
        indexData = await response.json();
        console.log('Character data loaded:', indexData);
    } catch (error) {
        console.error('Error loading index:', error);
        showError('Failed to load character database. Please try again later.');
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
            await searchCharacterById(randomChar.id);
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

function characterList() {
    if (!indexData || !indexData.characters) return [];
    if (Array.isArray(indexData.characters)) return indexData.characters;
    return Object.entries(indexData.characters).map(([name, info]) => ({
        name,
        show: info.show,
        trope_count: info.trope_count,
        id: info.id
    }));
}

function matchScore(query, name) {
    const q = query.toLowerCase().trim();
    const n = (name || '').toLowerCase();
    if (!q || !n) return 0;
    if (n === q) return 1000;
    if (n.startsWith(q)) return 800;
    if (n.includes(q)) return 600;
    const words = q.split(/\s+/).filter(Boolean);
    const hits = words.filter(word => n.includes(word)).length;
    if (!hits) return 0;
    return Math.round((hits / words.length) * 400);
}

// Get unified suggestions (both characters and shows)
function getUnifiedSuggestions(query) {
    const characters = characterList()
        .map(char => ({
            type: 'character',
            name: char.name,
            show: char.show,
            tropeCount: char.trope_count,
            id: char.id,
            score: matchScore(query, char.name)
        }))
        .filter(item => item.score > 0);

    const shows = Object.keys(indexData.shows || {}).map(showName => ({
        type: 'show',
        name: showName,
        charCount: indexData.shows[showName].length,
        score: matchScore(query, showName)
    })).filter(item => item.score > 0);

    return [...characters, ...shows]
        .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))
        .slice(0, 8);
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
                <div class="suggestion-item" data-type="character" data-id="${escapeAttr(item.id)}" data-name="${escapeAttr(item.name)}">
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
                await searchCharacterById(item.dataset.id);
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
    
    const characters = characterList();
    if (!characters.length) return null;
    return characters[Math.floor(Math.random() * characters.length)];
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

    const exactCharacters = characterList().filter(char => char.name.toLowerCase() === query.toLowerCase());
    if (exactCharacters.length > 1) {
        displayCharacterChoices(exactCharacters);
        return;
    }

    const matches = getUnifiedSuggestions(query);
    if (!matches.length) {
        showError(`"${query}" not found. Try searching for a different character or show.`);
        return;
    }

    const best = matches[0];
    if (best.type === 'character') {
        await searchCharacterById(best.id);
        return;
    }
    await searchShow(best.name);
}

function displayCharacterChoices(characters) {
    const resultsDiv = document.getElementById('results');
    let html = `
        <div class="show-header">
            <h2>${escapeHtml(characters[0].name)}</h2>
            <p>${characters.length} matching characters</p>
        </div>
        <div class="show-characters-grid">
    `;
    characters.forEach(char => {
        html += `
            <div class="character-card" onclick="searchCharacterById('${escapeAttr(char.id)}')">
                <h4>${escapeHtml(char.name)}</h4>
                <p class="show-name">${escapeHtml(char.show)}</p>
                <p class="trope-count">${char.trope_count} tropes</p>
            </div>
        `;
    });
    html += '</div>';
    resultsDiv.innerHTML = html;
    revealResults(resultsDiv);
}

async function searchCharacterById(id) {
    const char = characterList().find(item => item.id === id);
    if (!char) {
        showError('Character not found. Try searching for a different character.');
        return;
    }
    await loadCharacterDetails(char.name, char.id);
}

// Search for a character
async function searchCharacter(query) {
    const matches = characterList()
        .map(char => ({ char, score: matchScore(query, char.name) }))
        .filter(item => item.score > 0)
        .sort((a, b) => b.score - a.score || b.char.trope_count - a.char.trope_count);

    if (!matches.length) {
        showError(`Character "${query}" not found. Try searching for a different character.`);
        return;
    }

    const exact = matches.filter(item => item.score === 1000);
    if (exact.length > 1) {
        displayCharacterChoices(exact.map(item => item.char));
        return;
    }

    const chosen = matches[0].char;
    console.log('Found character:', chosen.name, chosen.show);
    await loadCharacterDetails(chosen.name, chosen.id);
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
        const fileName = `${characterId}.json`;
        console.log('Loading character file:', fileName);
        const response = await fetch(`${BASE_URL}/characters/${fileName}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const characterData = await response.json();
        
        currentCharacter = characterData;
        displayCharacterDetails(characterData);
        await findSimilarCharacters(characterData);
    } catch (error) {
        console.error('Error loading character:', error);
        showError(`Failed to load character details for "${characterName}"`);
    }
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
        ${renderTraitSection(character)}

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
    revealResults(resultsDiv);
}

function renderTraitSection(character) {
    const traits = character.traits || [];
    if (!traits.length) {
        return '';
    }
    const pills = traits.map(trait =>
        `<span class="trait-tag">${escapeHtml(trait.name)}</span>`
    ).join('');
    return `
        <div class="traits-section">
            <h3>Traits</h3>
            <p class="traits-note">Inferred from tropes. Similarity uses this vector, not the raw trope names.</p>
            <div class="traits-list">${pills}</div>
        </div>
    `;
}

// Create a clickable trope link
function createTropeLink(trope) {
    const tropeUrl = `https://tvtropes.org/pmwiki/pmwiki.php/Main/${trope}`;
    return `<a href="${tropeUrl}" target="_blank" rel="noopener noreferrer" class="trope-tag">${escapeHtml(trope)}</a>`;
}

// Find similar characters using Jaccard similarity
async function findSimilarCharacters(targetCharacter) {
    if (targetCharacter.similar && targetCharacter.similar.length) {
        displaySimilarCharacters(targetCharacter.similar.map(item => ({
            name: item.name,
            show: item.show,
            id: item.id,
            similarity: item.similarity,
            sharedTropes: item.shared_tropes,
            sharedTraits: item.shared_traits || [],
            tropeCount: item.trope_count
        })));
        return;
    }

    const targetTropes = new Set(targetCharacter.tropes);
    const similarities = [];

    let processed = 0;
    let successful = 0;
    const maxToProcess = 500; // Check more characters
    const maxSuccessful = 100; // But only process 100 successfully

    // Calculate similarity with other characters
    for (const charInfo of characterList()) {
        const charName = charInfo.name;
        if (charInfo.id === targetCharacter.id || charName === targetCharacter.name) continue;
        if (processed++ >= maxToProcess) break;
        if (successful >= maxSuccessful) break;

        try {
            const fileName = `${charInfo.id}.json`;
            const response = await fetch(`${BASE_URL}/characters/${fileName}`);
            
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
                    id: charInfo.id,
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
        const sharedTraits = char.sharedTraits || [];
        const detail = sharedTraits.length
            ? `${percentage}% similar · ${sharedTraits.slice(0, 3).map(escapeHtml).join(', ')}`
            : `${percentage}% similar (${char.sharedTropes} shared tropes)`;
        html += `
            <div class="character-card similar-card" onclick="searchCharacterById('${escapeAttr(char.id)}')">
                <h4>${escapeHtml(char.name)}</h4>
                <p class="show-name">${escapeHtml(char.show)}</p>
                <div class="similarity-bar">
                    <div class="similarity-fill" style="width: ${Math.min(percentage, 100)}%"></div>
                </div>
                <p class="similarity-text">${detail}</p>
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
            <div class="character-card" onclick="searchCharacterById('${escapeAttr(char.id)}')">
                <h4>${escapeHtml(char.name)}</h4>
                <p class="trope-count">${char.trope_count} tropes</p>
            </div>
        `;
    });
    
    html += '</div>';
    resultsDiv.innerHTML = html;
    revealResults(resultsDiv);
}

// Show loading state
function showLoading() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="loading">Loading...</div>';
    revealResults(resultsDiv);
}

// Show error message
function showError(message) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `<div class="error-message">${escapeHtml(message)}</div>`;
    revealResults(resultsDiv);
}

// Clear results
function revealResults(resultsDiv) {
    resultsDiv.style.display = 'block';
    document.body.classList.add('has-results');
}

function clearResults() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';
    resultsDiv.style.display = 'none';
    document.body.classList.remove('has-results');
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
