// Renderer logic for UI interactions
const player = new Audio(); // Simple HTML5 Player
let currentTrack = null;
let isPlaying = false;

document.addEventListener('DOMContentLoaded', () => {
    console.log('Playlister UI Loaded');

    // Navigation Logic
    const navLinks = document.querySelectorAll('.nav-links li');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Remove active class from all
            navLinks.forEach(l => l.classList.remove('active'));
            // Add active class to clicked
            link.classList.add('active');

            const viewName = link.getAttribute('data-view');
            console.log(`Switched to view: ${viewName}`);

            // Hide all views
            document.querySelectorAll('.view').forEach(view => {
                view.classList.remove('active');
            });

            // Show selected view
            const targetView = document.getElementById(`view-${viewName}`);
            if (targetView) {
                targetView.classList.add('active');
            } else {
                console.error(`View not found: view-${viewName}`);
            }
        });
    });

    // Play Button Interaction
    const playBtn = document.getElementById('btn-play');

    playBtn.addEventListener('click', () => {
        // If no track is loaded, do nothing
        if (player.src === "") return;

        if (isPlaying) {
            player.pause();
            playBtn.textContent = '▶';
        } else {
            player.play();
            playBtn.textContent = '⏸';
        }
        isPlaying = !isPlaying;
    });

    // Player Events
    player.addEventListener('timeupdate', () => {
        if (!player.duration) return;
        const progress = (player.currentTime / player.duration) * 100;
        document.querySelector('.progress-fill').style.width = `${progress}%`;
        document.querySelector('.time.current').textContent = formatTime(player.currentTime);
        document.querySelector('.time.total').textContent = formatTime(player.duration || 0);
    });

    player.addEventListener('ended', () => {
        isPlaying = false;
        playBtn.textContent = '▶';
    });

    function formatTime(seconds) {
        if (isNaN(seconds)) return "0:00";
        const min = Math.floor(seconds / 60);
        const sec = Math.floor(seconds % 60);
        return `${min}:${sec < 10 ? '0' : ''}${sec}`;
    }

    // Volume Control
    const volumeSlider = document.querySelector('.volume-slider');
    volumeSlider.addEventListener('input', (e) => {
        player.volume = e.target.value / 100;
    });

    // Search Input Logic
    const searchInput = document.getElementById('global-search');
    const resultsGrid = document.getElementById('search-results');

    searchInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value;
            if (!query) return;

            console.log(`Searching for: ${query}`);
            resultsGrid.innerHTML = '<div class="placeholder-text">Searching...</div>';

            try {
                const results = await window.api.search(query);
                displayResults(results);
            } catch (error) {
                console.error("Search error:", error);
                resultsGrid.innerHTML = '<div class="placeholder-text">Error occurred while searching.</div>';
            }
        }
    });

    function displayResults(results) {
        resultsGrid.innerHTML = '';
        if (!results || results.length === 0) {
            resultsGrid.innerHTML = '<div class="placeholder-text">No results found.</div>';
            return;
        }

        results.forEach(item => {
            // Basic card template
            const card = document.createElement('div');
            card.className = 'track-card';

            let title = item.name;
            let artistName = "Unknown Artist";

            if (item.artist) {
                if (Array.isArray(item.artist)) {
                    artistName = item.artist.map(a => a.name).join(", ");
                } else {
                    artistName = item.artist.name;
                }
            } else if (item.author) {
                artistName = item.author; // Fallback for some result types
            }

            let albumName = "";
            if (item.album) {
                albumName = ` - ${item.album.name}`;
            }

            let thumb = "https://via.placeholder.com/150";

            if (item.thumbnails && item.thumbnails.length > 0) {
                thumb = item.thumbnails[item.thumbnails.length - 1].url;
            }

            card.innerHTML = `
                <div class="card-image" style="background-image: url('${thumb}')">
                    <div class="play-overlay">▶</div>
                </div>
                <div class="card-info">
                    <div class="card-title">${title}</div>
                    <div class="card-artist">${artistName}${albumName}</div>
                </div>
                <div class="card-actions">
                    <button class="btn-icon favorite">❤</button>
                    <span class="time">${item.duration ? item.duration : ''}</span>
                </div>
            `;

            // Interaction for playing would go here
            card.addEventListener('click', () => {
                playTrack(item);
            });

            resultsGrid.appendChild(card);
        });
    }

    async function playTrack(track) {
        console.log("Requesting stream for:", track.videoId);

        // Update UI immediately (Optimistic UI)
        document.querySelector('.track-title').textContent = track.name;

        let artistName = "Unknown Artist";
        if (track.artist) {
            if (Array.isArray(track.artist)) {
                artistName = track.artist.map(a => a.name).join(", ");
            } else {
                artistName = track.artist.name;
            }
        } else if (track.author) {
            artistName = track.author;
        }
        document.querySelector('.track-artist').textContent = artistName;

        let thumb = "https://via.placeholder.com/150";
        if (track.thumbnails && track.thumbnails.length > 0) {
            thumb = track.thumbnails[track.thumbnails.length - 1].url;
        }
        document.querySelector('.track-art').style.backgroundImage = `url('${thumb}')`;
        document.querySelector('.track-art').style.backgroundSize = "cover";

        try {
            const streamData = await window.api.getStream(track.videoId);
            console.log("Stream URL received:", streamData.url);

            player.src = streamData.url;
            player.play();
            isPlaying = true;
            document.getElementById('btn-play').textContent = '⏸';
        } catch (error) {
            console.error("Failed to play track:", error);
            // alert("Failed to play track. See console.");
        }
    }
});
