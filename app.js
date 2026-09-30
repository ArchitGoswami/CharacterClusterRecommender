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
        const response = await fetch(`${BASE_URL}/index.json?v=3`);
        indexData = await response.json();
        dropLetterBuckets(indexData);
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

    const resultsDiv = document.getElementById('results');
    if (resultsDiv) {
        resultsDiv.addEventListener('click', (event) => {
            const showLink = event.target.closest('.show-link');
            if (!showLink) return;
            event.preventDefault();
            event.stopPropagation();
            openShow(showLink.dataset.show);
        }, true);
        resultsDiv.addEventListener('click', (event) => {
            const button = event.target.closest('.tropes-toggle');
            if (!button) return;
            const section = button.closest('.tropes-section');
            const collapsed = section.classList.toggle('is-collapsed');
            button.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
            button.textContent = collapsed ? 'Show all' : 'Show less';
        });
    }

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

function isLetterBucket(name) {
    const text = String(name || '').trim().replace(/\s+/g, ' ');
    if (/^[A-Z](?:\s*[-–—]\s*[A-Z])?$/.test(text)) return true;
    if (/^#\s*[-–—]\s*[A-Z]$/.test(text)) return true;
    if (/^[#A-Z]\s+to\s+[A-Z]$/i.test(text)) return true;
    if (/tropes\s+(?:#\s*)?(?:[a-z]\s*)?(?:to|[-–—])\s*[a-z]/i.test(text)) return true;
    return false;
}

function dropLetterBuckets(index) {
    if (!index) return;
    if (Array.isArray(index.characters)) {
        index.characters = index.characters.filter(character => !isLetterBucket(character.name));
    }
    if (!index.shows) return;
    for (const show of Object.keys(index.shows)) {
        index.shows[show] = (index.shows[show] || []).filter(character => !isLetterBucket(character.name));
        if (!index.shows[show].length) delete index.shows[show];
    }
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

async function openShow(showName) {
    if (!showName) return;
    const input = document.getElementById('searchInput');
    if (input) input.value = showName;
    hideSuggestions();
    await searchShow(showName);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showLinkHtml(show) {
    const name = show || '';
    return `<a class="show-link" href="#" data-show="${escapeAttr(name)}">${escapeHtml(name)}</a>`;
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
                <p class="show-name">${showLinkHtml(char.show)}</p>
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

const mediaImageCache = new Map();

function mediaLookupTitle(show) {
    let name = String(show || '').trim().replace(/\s*\([^)]*\)\s*$/, '').trim();
    const commaArticle = name.match(/^(.*?),\s*(the|a|an)$/i);
    if (commaArticle) {
        const article = commaArticle[2].toLowerCase();
        name = `${article.charAt(0).toUpperCase()}${article.slice(1)} ${commaArticle[1].trim()}`;
    }
    return name;
}

function cachedLookup(key, loader) {
    if (!mediaImageCache.has(key)) {
        mediaImageCache.set(key, Promise.resolve().then(loader).catch(() => null));
    }
    return mediaImageCache.get(key);
}

function namesMatch(found, wanted) {
    const normalize = value => String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
    const a = normalize(found);
    const b = normalize(wanted);
    return Boolean(a && b && (a === b || a.includes(b) || b.includes(a)));
}

async function wikipediaSummary(title) {
    return cachedLookup(`wiki:${title.toLowerCase()}`, async () => {
        const slug = encodeURIComponent(title.replace(/ /g, '_'));
        const response = await fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${slug}`);
        if (!response.ok) return null;
        const data = await response.json();
        if (!data || data.type === 'disambiguation') return null;
        const src = (data.thumbnail && data.thumbnail.source) || (data.originalimage && data.originalimage.source) || '';
        const extract = data.extract || '';
        const description = data.description || '';
        if (!src && !extract && !description) return null;
        const desktop = data.content_urls && data.content_urls.desktop;
        return {
            src,
            title: data.title || title,
            description,
            extract,
            page: (desktop && desktop.page) || ''
        };
    });
}

function plainText(html) {
    const node = document.createElement('div');
    node.innerHTML = html || '';
    return (node.textContent || '').replace(/\s+/g, ' ').trim();
}

function clipContext(text) {
    const clean = String(text || '').replace(/\s+/g, ' ').trim();
    const limit = 520;
    if (clean.length <= limit) return clean;
    const slice = clean.slice(0, limit);
    const end = Math.max(slice.lastIndexOf('. '), slice.lastIndexOf('! '), slice.lastIndexOf('? '));
    if (end > 160) return slice.slice(0, end + 1);
    return `${slice.trimEnd()}…`;
}

async function tvmazePoster(title) {
    const response = await fetch(`https://api.tvmaze.com/singlesearch/shows?q=${encodeURIComponent(title)}`);
    if (!response.ok) return null;
    const data = await response.json();
    if (!namesMatch(data.name, title)) return null;
    const src = (data.image && (data.image.medium || data.image.original)) || '';
    const extract = plainText(data.summary);
    if (!src && !extract) return null;
    return {
        src,
        title: data.name || title,
        page: data.url || '',
        description: '',
        extract
    };
}

async function showImage(show) {
    const title = mediaLookupTitle(show);
    if (!title) return null;
    const poster = await cachedLookup(`tv:${title.toLowerCase()}`, () => tvmazePoster(title));
    if (poster) return poster;
    return wikipediaSummary(title);
}

function pageMatchesCharacter(page, name) {
    const title = page.title.toLowerCase();
    const parts = name.toLowerCase().split(/\s+/).filter(part => part.length > 1);
    return parts.length > 0 && parts.every(part => title.includes(part));
}

function pageMentionsShow(page, media) {
    const blob = `${page.title} ${page.description} ${page.extract}`.toLowerCase();
    const core = media.toLowerCase().replace(/^(the|a|an)\s+/, '');
    const skip = new Set(['series', 'show', 'film', 'movie', 'story', 'from', 'with']);
    const tokens = core.split(/[^a-z0-9]+/).filter(word => word.length > 3 && !skip.has(word));
    if (!tokens.length) return blob.includes(core);
    tokens.sort((a, b) => b.length - a.length);
    return blob.includes(tokens[0]);
}

function isCharacterArticle(page) {
    const title = (page.title || '').toLowerCase();
    if (title.startsWith('list of ')) return false;
    const description = (page.description || '').toLowerCase();
    const extract = (page.extract || '').toLowerCase();
    const head = `${description} ${extract.slice(0, 320)}`;
    return /\b(character|protagonist|antagonist|portrayed by|voiced by)\b/.test(head);
}

function isShowArticle(page, media) {
    if (!page || isCharacterArticle(page)) return false;
    const description = (page.description || '').toLowerCase();
    if (/\b(series|sitcom|anime|film|movie|franchise|miniseries)\b/.test(description)) return true;
    const title = String(page.title || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
    const show = mediaLookupTitle(media).toLowerCase().replace(/[^a-z0-9]+/g, '');
    return Boolean(title && show && title === show);
}

function contextIsShowBlurb(text, show) {
    const clean = String(text || '').toLowerCase();
    const head = clean.slice(0, 320);
    if (/\b(character|protagonist|antagonist|portrayed by|voiced by)\b/.test(head)) return false;
    const aboutSeries = /\b(television series|tv series|anime series|animated series|web series|sitcom|miniseries)\b/.test(head);
    if (!aboutSeries) return false;
    const title = mediaLookupTitle(show).toLowerCase();
    return !title || clean.startsWith(title) || head.includes(title);
}

function lookupNames(name) {
    const original = String(name || '').trim();
    const pieces = original.split(/\s*[/|]\s*/).map(part => part.trim()).filter(Boolean);
    const names = [];
    const add = (value) => {
        const text = String(value || '').replace(/\s+/g, ' ').trim();
        if (!text || names.some(existing => existing.toLowerCase() === text.toLowerCase())) return;
        names.push(text);
    };
    for (const piece of (pieces.length > 1 ? pieces : [original])) {
        let spaced = piece.replace(/([a-z\d])([A-Z])/g, '$1 $2');
        spaced = spaced.replace(/\bMac ([A-Z])/g, 'Mac$1').replace(/\bMc ([A-Z])/g, 'Mc$1');
        add(spaced);
        if (spaced !== piece) add(piece);
    }
    return names;
}

async function findCharacterPage(name, show) {
    const media = mediaLookupTitle(show);
    for (const candidate of lookupNames(name)) {
        const titles = [`${candidate} (${media})`, `${candidate} (character)`, candidate];
        for (const title of titles) {
            const page = await wikipediaSummary(title);
            if (!page || isShowArticle(page, media) || !pageMatchesCharacter(page, candidate)) continue;
            if (title === candidate && !pageMentionsShow(page, media)) continue;
            if (title.endsWith('(character)') && !pageMentionsShow(page, media)) continue;
            return page;
        }
    }
    return null;
}

async function characterImage(name, show) {
    const page = await findCharacterPage(name, show);
    const characterContext = page && isCharacterArticle(page)
        ? clipContext(page.extract || page.description)
        : '';
    if (page && page.src) {
        return {
            src: page.src,
            title: page.title,
            page: page.page || '',
            context: characterContext,
            contextKind: 'character'
        };
    }
    const poster = await showImage(show);
    if (!poster && !characterContext) return null;
    return {
        src: (poster && poster.src) || '',
        title: (poster && poster.title) || name,
        page: (poster && poster.page) || '',
        context: characterContext,
        contextKind: 'character'
    };
}

async function showProfile(show) {
    const profile = await showImage(show);
    if (!profile) return null;
    return {
        ...profile,
        context: clipContext(profile.extract || profile.description),
        contextKind: 'show'
    };
}

function attachMediaImage(root, spec) {
    if (!root) return;
    const token = `${spec.kind}|${spec.name || ''}|${spec.show || ''}`;
    root.dataset.imageToken = token;
    const lookup = spec.kind === 'show'
        ? showProfile(spec.show || spec.name)
        : characterImage(spec.name, spec.show);
    lookup.then(image => {
        if (!image || !root.isConnected || root.dataset.imageToken !== token) return;
        const link = root.querySelector('.media-portrait-link');
        const img = root.querySelector('.media-portrait');
        if (link && img && image.src) {
            img.alt = image.title || spec.name || spec.show || '';
            img.onerror = () => {
                link.hidden = true;
                root.classList.remove('has-image');
            };
            img.src = image.src;
            if (image.page) {
                link.href = image.page;
                link.setAttribute('aria-label', img.alt);
            }
            link.hidden = false;
            root.classList.add('has-image');
        }
        const blurb = root.querySelector('.media-context');
        const showContextOnCharacter = spec.kind === 'character' && (
            image.contextKind === 'show' || contextIsShowBlurb(image.context, spec.show)
        );
        if (blurb && image.context && !showContextOnCharacter) {
            blurb.textContent = image.context;
            blurb.hidden = false;
            root.classList.add('has-context');
        }
    }).catch(() => {});
}

function mediaPortraitHtml() {
    return `<a class="media-portrait-link" target="_blank" rel="noopener noreferrer" hidden><img class="media-portrait" alt=""></a>`;
}

// Display character details
function displayCharacterDetails(character) {
    const resultsDiv = document.getElementById('results');
    
    console.log('Displaying character:', character);
    console.log('Tropes:', character.tropes);
    console.log('Tropes by category:', character.tropes_by_category);
    
    let html = `
        <div class="character-card main-character">
            ${mediaPortraitHtml()}
            <div class="media-copy">
                <h2>${escapeHtml(character.name)}</h2>
                <p class="show-name">From: ${showLinkHtml(character.show)}</p>
                <p class="trope-count">${character.trope_count} tropes</p>
                <p class="media-context" hidden></p>
            </div>
        </div>
        ${renderTraitSection(character)}
        <div id="similar-characters"><div class="loading">Finding similar characters...</div></div>

        <div class="tropes-section is-collapsed">
            <div class="tropes-heading">
                <h3>Character Tropes</h3>
                <button type="button" class="tropes-toggle" aria-expanded="false">Show all</button>
            </div>
            <div class="tropes-body">
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

    html += `</div></div>`;
    
    resultsDiv.innerHTML = html;
    revealResults(resultsDiv);
    attachMediaImage(resultsDiv.querySelector('.main-character'), {
        kind: 'character',
        name: character.name,
        show: character.show
    });
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
    
    similarChars = (similarChars || []).filter(character => !isLetterBucket(character.name));
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
                <p class="show-name">${showLinkHtml(char.show)}</p>
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
            ${mediaPortraitHtml()}
            <div class="media-copy">
                <h2>${escapeHtml(showName)}</h2>
                <p>${characters.length} characters</p>
                <p class="media-context" hidden></p>
            </div>
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
    attachMediaImage(resultsDiv.querySelector('.show-header'), {
        kind: 'show',
        show: showName
    });
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

function initParticles() {
    const canvas = document.getElementById('particles');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let dots = [];
    let width = 0;
    let height = 0;
    let running = true;

    function resize() {
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        canvas.style.width = width + 'px';
        canvas.style.height = height + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        const count = Math.max(28, Math.round((width * height) / 18000));
        dots = Array.from({ length: count }, () => ({
            x: Math.random() * width,
            y: Math.random() * height,
            r: Math.random() * 1.15 + 0.35,
            o: Math.random() * 0.45 + 0.15,
            vy: Math.random() * 0.18 + 0.04
        }));
    }

    function frame() {
        if (!running) return;
        ctx.clearRect(0, 0, width, height);
        const light = document.documentElement.getAttribute('data-theme') === 'light';
        ctx.fillStyle = light ? '#111111' : '#ffffff';
        for (const dot of dots) {
            if (!reduceMotion) {
                dot.y -= dot.vy;
                if (dot.y < -2) dot.y = height + 2;
            }
            ctx.globalAlpha = dot.o;
            ctx.beginPath();
            ctx.arc(dot.x, dot.y, dot.r, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.globalAlpha = 1;
        requestAnimationFrame(frame);
    }

    resize();
    frame();
    window.addEventListener('resize', resize);
    document.addEventListener('visibilitychange', () => {
        running = !document.hidden;
        if (running) frame();
    });
}

initParticles();
