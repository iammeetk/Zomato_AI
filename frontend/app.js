/**
 * Phase 5 UI — calls Phase 4 API on the same origin when served via `python -m restaurant_rec serve`.
 */
(function () {
    const API_BASE = window.location.origin;

    const form = document.getElementById('preferences-form');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.querySelector('.btn-text');
    const btnLoader = document.getElementById('btn-loader');
    const resultsSection = document.getElementById('results-section');
    const resultsContainer = document.getElementById('results-container');
    const resultsMeta = document.getElementById('results-meta');
    const resultsSummary = document.getElementById('results-summary');
    const errorMessage = document.getElementById('error-message');
    const apiStatus = document.getElementById('api-status');
    const localityList = document.getElementById('locality-list');

    document.addEventListener('DOMContentLoaded', () => {
        initApiStatus();
        form.addEventListener('submit', onSubmit);
    });

    async function initApiStatus() {
        try {
            const health = await fetchJson('/health');
            const count = health.row_count ?? '?';
            let msg = health.dataset === 'loaded'
                ? `API ready · ${count} restaurants`
                : 'API up but dataset not loaded — run ingest';
            if (health.warning) msg += ` — ${health.warning}`;
            setStatus(health.dataset === 'loaded' ? 'ok' : 'warn', msg);
            if (health.dataset === 'loaded') {
                await loadLocalities();
            }
        } catch (err) {
            setStatus(
                'error',
                'Cannot reach API — start server: python -m restaurant_rec serve',
            );
            console.error(err);
        }
    }

    async function loadLocalities() {
        try {
            const data = await fetchJson('/v1/localities');
            localityList.innerHTML = '';
            const options = [
                ...(data.metros || []),
                ...(data.localities || []),
            ];
            [...new Set(options)].slice(0, 500).forEach((city) => {
                const opt = document.createElement('option');
                opt.value = city;
                localityList.appendChild(opt);
            });
        } catch (err) {
            console.warn('Could not load localities', err);
        }
    }

    function setStatus(kind, text) {
        apiStatus.className = `api-status api-status--${kind}`;
        apiStatus.textContent = text;
    }

    async function onSubmit(e) {
        e.preventDefault();

        const location = document.getElementById('location').value.trim();
        const budget = document.getElementById('budget').value;
        const cuisineStr = document.getElementById('cuisine').value.trim();
        const minRating = parseFloat(document.getElementById('min_rating').value);
        const additionalPrefs = document.getElementById('additional_preferences').value.trim();

        const cuisineArray = cuisineStr
            .split(',')
            .map((c) => c.trim())
            .filter((c) => c.length > 0);

        if (cuisineArray.length === 0) {
            showError('Please enter at least one cuisine.');
            return;
        }

        const payload = {
            location,
            budget,
            cuisine: cuisineArray,
            min_rating: minRating,
            additional_preferences: additionalPrefs || null,
        };

        setLoading(true);

        try {
            const data = await fetchJson('/v1/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            renderResults(data);
        } catch (err) {
            console.error(err);
            showError(err.message || 'Request failed');
        } finally {
            setLoading(false);
        }
    }

    async function fetchJson(path, options = {}) {
        const response = await fetch(`${API_BASE}${path}`, options);
        let data = null;
        const text = await response.text();
        if (text) {
            try {
                data = JSON.parse(text);
            } catch {
                data = { detail: text };
            }
        }
        if (!response.ok) {
            const detail = data?.detail ?? data?.message ?? response.statusText;
            throw new Error(formatApiError(detail) || `HTTP ${response.status}`);
        }
        return data;
    }

    function formatApiError(detail) {
        if (!detail) return 'Request failed';
        if (typeof detail === 'string') return detail;
        if (Array.isArray(detail)) {
            return detail
                .map((item) => {
                    const loc = item.loc ? item.loc.filter((p) => p !== 'body').join('.') : '';
                    const msg = item.msg || JSON.stringify(item);
                    return loc ? `${loc}: ${msg}` : msg;
                })
                .join('; ');
        }
        return JSON.stringify(detail);
    }

    function setLoading(isLoading) {
        submitBtn.disabled = isLoading;
        btnText.textContent = isLoading ? 'Finding restaurants…' : 'Get recommendations';
        btnLoader.classList.toggle('hidden', !isLoading);
        if (isLoading) {
            resultsSection.classList.add('hidden');
            clearResults();
        }
    }

    function clearResults() {
        resultsContainer.innerHTML = '';
        errorMessage.classList.add('hidden');
        errorMessage.textContent = '';
        resultsMeta.classList.add('hidden');
        resultsMeta.innerHTML = '';
        resultsSummary.classList.add('hidden');
        resultsSummary.textContent = '';
    }

    function showError(msg) {
        resultsSection.classList.remove('hidden');
        errorMessage.textContent = msg;
        errorMessage.classList.remove('hidden');
    }

    function renderResults(data) {
        resultsSection.classList.remove('hidden');
        clearResults();

        renderMeta(data);

        if (data.message && (!data.items || data.items.length === 0)) {
            showError(data.message);
            return;
        }

        if (!data.items || data.items.length === 0) {
            showError(
                data.message ||
                    'No restaurants matched your filters. Try a different city, cuisine, or lower min rating.',
            );
            return;
        }

        if (data.summary) {
            resultsSummary.textContent = data.summary;
            resultsSummary.classList.remove('hidden');
        }

        if (data.warnings && data.warnings.length > 0) {
            const warn = document.createElement('p');
            warn.className = 'results-warnings';
            warn.textContent = data.warnings.join(' ');
            resultsMeta.appendChild(warn);
        }

        data.items.forEach((item) => {
            resultsContainer.appendChild(buildCard(item));
        });
    }

    function renderMeta(data) {
        const chips = [];
        if (data.used_llm) chips.push('Groq LLM');
        else chips.push('Template fallback');
        if (typeof data.filter_count === 'number') {
            chips.push(`${data.filter_count} matched`);
        }
        if (typeof data.returned_count === 'number') {
            chips.push(`${data.returned_count} candidates`);
        }
        if (data.dataset_snapshot_id) {
            chips.push('Snapshot loaded');
        }

        resultsMeta.innerHTML = chips
            .map((c) => `<span class="meta-chip">${escapeHTML(c)}</span>`)
            .join('');
        resultsMeta.classList.remove('hidden');
    }

    function buildCard(item) {
        const card = document.createElement('article');
        card.className = 'restaurant-card';
        const ratingDisplay =
            item.rating != null && !Number.isNaN(item.rating)
                ? Number(item.rating).toFixed(1)
                : 'N/A';

        card.innerHTML = `
            <div class="card-header">
                <div>
                    <h3 class="card-title">${escapeHTML(item.name)}</h3>
                    <p class="card-cuisine">${escapeHTML(item.cuisine)}</p>
                </div>
                <div class="card-rank">#${item.rank}</div>
            </div>
            <div class="card-stats">
                <div class="stat-item">
                    <span class="stat-icon" aria-hidden="true">★</span>
                    <span>${escapeHTML(ratingDisplay)}</span>
                </div>
                <div class="stat-item">
                    <span aria-hidden="true">₹</span>
                    <span>${escapeHTML(item.estimated_cost)}</span>
                </div>
            </div>
            <p class="card-explanation">${escapeHTML(item.explanation)}</p>
        `;
        return card;
    }

    function escapeHTML(str) {
        if (str == null) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    }
})();
