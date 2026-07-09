// This will load your character_index.json
let characterData = null;
let currentSearchMode = 'character';

// Load the character index
async function loadCharacterIndex() {
    try {
        const response = await fetch('character_index.json');
        characterData = await response.json();
        console.log('Character data loaded:', characterData);
    } catch (error) {
        console.error('Error loading character data:', error);
    }
}

// Initialize
loadCharacterIndex();

// Tab switching
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentSearchMode = tab.dataset.tab;
        document.getElementById('searchInput').value = '';
        document.getElementById('suggestions').classList.remove('active');
        document.getElementById('searchInput').placeholder = 
            currentSearchMode === 'character' 
                ? 'Start typing a character name...' 
                : 'Start typing a show name...';
    });
});

// Search functionality
const searchInput = document.getElementById('searchInput');
const suggestionsDiv = document.getElementById('suggestions');

searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    
    if (query.length < 2) {
        suggestionsDiv.classList.remove('active');
        return;
    }
    
    if (!characterData) {
        suggestionsDiv.innerHTML = '<div class="suggestion-item">Loading data...</div>';
        suggestionsDiv.classList.add('active');
        return;
    }
    
    const results = searchCharacters(query);
    displaySuggestions(results);
});

function searchCharacters(query) {
    if (!characterData || !characterData.characters) return [];
    
    const results = [];
    
    if (currentSearchMode === 'character') {
        // Search by character name
        for (const [charName, charInfo] of Object.entries(characterData.characters)) {
            if (charName.toLowerCase().includes(query)) {
                results.push({
                    name: charName,
                    show: charInfo.media_title,
                    tropeCount: charInfo.trope_count,
                    file: charInfo.source_file
                });
            }
            if (results.length >= 10) break;
        }
    } else {
        // Search by show
        const shows = new Set();
        for (const charInfo of Object.values(characterData.characters)) {
            if (charInfo.media_title.toLowerCase().includes(query)) {
                shows.add(charInfo.media_title);
            }
        }
        
        Array.from(shows).slice(0, 10).forEach(show => {
            const charCount = Object.values(characterData.characters)
                .filter(c => c.media_title === show).length;
            results.push({
                show: show,
                characterCount: charCount
            });
        });
    }
    
    return results;
}

function displaySuggestions(results) {
    if (results.length === 0) {
        suggestionsDiv.innerHTML = '<div class="suggestion-item">No results found</div>';
        suggestionsDiv.classList.add('active');
        return;
    }
    
    suggestionsDiv.innerHTML = results.map(result => {
        if (currentSearchMode === 'character') {
            return `
                <div class="suggestion-item" onclick="selectCharacter('${escapeHtml(result.name)}')">
                    <div class="character-name">${escapeHtml(result.name)}</div>
                    <div class="show-name">${escapeHtml(result.show)}</div>
                    <div class="trope-count">${result.tropeCount} tropes</div>
                </div>
            `;
        } else {
            return `
                <div class="suggestion-item" onclick="selectShow('${escapeHtml(result.show)}')">
                    <div class="character-name">${escapeHtml(result.show)}</div>
                    <div class="trope-count">${result.characterCount} characters</div>
                </div>
            `;
        }
    }).join('');
    
    suggestionsDiv.classList.add('active');
}

async function selectCharacter(characterName) {
    suggestionsDiv.classList.remove('active');
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="loading">Loading character details...</div>';
    resultsDiv.classList.add('active');
    
    // Load the character's full data from their JSON file
    const charInfo = characterData.characters[characterName];
    if (!charInfo) {
        resultsDiv.innerHTML = '<div class="loading">Character not found</div>';
        return;
    }
    
    try {
        const response = await fetch(`data/${charInfo.source_file}`);
        const fullData = await response.json();
        displayCharacterDetails(characterName, fullData);
    } catch (error) {
        resultsDiv.innerHTML = '<div class="loading">Error loading character data</div>';
        console.error(error);
    }
}

function displayCharacterDetails(characterName, data) {
    const resultsDiv = document.getElementById('results');
    
    // This is a simplified version - you'll need to adapt based on your actual data structure
    const html = `
        <div class="character-detail">
            <div class="character-header">
                <h2>${escapeHtml(characterName)}</h2>
                <p>${escapeHtml(data.media_title || 'Unknown Show')}</p>
                <p>${data.tropes?.length || 0} tropes</p>
            </div>
            
            <div class="trope-categories">
                ${displayTropeCategories(data.tropes || [])}
            </div>
            
            <div class="similar-characters">
                <h3>Similar Characters</h3>
                ${displaySimilarCharacters(characterName, data)}
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
}

function displayTropeCategories(tropes) {
    // Group tropes by category - you'll need to adapt this based on your clustering
    const categories = {};
    
    tropes.forEach(trope => {
        const category = trope.category || 'Uncategorized';
        if (!categories[category]) {
            categories[category] = [];
        }
        categories[category].push(trope.name || trope);
    });
    
    return Object.entries(categories).map(([category, tropeList]) => `
        <div class="category">
            <h4>${escapeHtml(category)}</h4>
            <ul class="trope-list">
                ${tropeList.slice(0, 5).map(t => `<li>• ${escapeHtml(t)}</li>`).join('')}
                ${tropeList.length > 5 ? `<li>... and ${tropeList.length - 5} more</li>` : ''}
            </ul>
        </div>
    `).join('');
}

function displaySimilarCharacters(characterName, characterData) {
    // Calculate similarity scores - simplified version
    // You'll need to implement your actual similarity algorithm
    const similarChars = findSimilarCharacters(characterName, characterData);
    
    return similarChars.map((char, index) => `
        <div class="character-card">
            <span class="rank">#${index + 1}</span>
            <h4>${escapeHtml(char.name)}</h4>
            <p>from ${escapeHtml(char.show)}</p>
            <p class="score">Similarity Score: ${char.score}</p>
            <div class="common-tropes">
                <strong>Common tropes:</strong> ${char.commonTropes.join(', ')}
            </div>
        </div>
    `).join('');
}

function findSimilarCharacters(characterName, characterData) {
    // Placeholder - implement your actual similarity algorithm here
    // This should calculate similarity based on shared tropes and categories
    return [
        { name: 'Example Character', show: 'Example Show', score: 85, commonTropes: ['Trope1', 'Trope2'] }
    ];
}

function selectShow(showName) {
    // Implement show selection logic
    console.log('Selected show:', showName);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close suggestions when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-container')) {
        suggestionsDiv.classList.remove('active');
    }
});