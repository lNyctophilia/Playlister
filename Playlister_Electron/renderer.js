// Renderer logic for UI interactions
const player = new Audio(); // Simple HTML5 Player
let currentTrack = null;
let isPlaying = false;
let isLooping = false;
let isDraggingProgress = false;

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

    // Play & Repeat Button Interaction
    const playBtn = document.getElementById('btn-play');
    const repeatBtn = document.getElementById('btn-repeat');
    const iconRepeat = repeatBtn.querySelector('.icon-repeat');
    const iconRepeatOne = repeatBtn.querySelector('.icon-repeat-one');

    repeatBtn.addEventListener('click', () => {
        isLooping = !isLooping;
        if (isLooping) {
            repeatBtn.classList.add('active');
            iconRepeat.style.display = 'none';
            iconRepeatOne.style.display = 'block';
        } else {
            repeatBtn.classList.remove('active');
            iconRepeat.style.display = 'block';
            iconRepeatOne.style.display = 'none';
        }
    });

    playBtn.addEventListener('click', () => {
        // If no track is loaded, do nothing
        if (player.src === "") return;

        if (isPlaying) {
            player.pause();
            playBtn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5V19L19 12L8 5Z" /></svg>`; // Play Icon
        } else {
            player.play();
            playBtn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>`; // Pause Icon
        }
        isPlaying = !isPlaying;
    });

    // Player Events
    const progressSlider = document.querySelector('.progress-slider');

    player.addEventListener('timeupdate', () => {
        if (!player.duration || isDraggingProgress) return;

        const currentTime = player.currentTime;
        const duration = player.duration;
        const progress = (currentTime / duration) * 100;

        progressSlider.value = progress;

        document.querySelector('.time.current').textContent = formatTime(currentTime);
        document.querySelector('.time.total').textContent = formatTime(duration);

        // Update slider background gradient for visual effect
        updateSliderBackground(progressSlider, progress);
    });

    player.addEventListener('ended', () => {
        if (isLooping) {
            player.currentTime = 0;
            player.play();
        } else {
            isPlaying = false;
            playBtn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5V19L19 12L8 5Z" /></svg>`;
        }
    });

    // Progress Bar Interactions
    progressSlider.addEventListener('input', (e) => {
        isDraggingProgress = true;
        const val = e.target.value;
        const duration = player.duration || 1;
        const currentTime = (val / 100) * duration;

        document.querySelector('.time.current').textContent = formatTime(currentTime);
        updateSliderBackground(progressSlider, val);
    });

    progressSlider.addEventListener('change', (e) => {
        const val = e.target.value;
        const duration = player.duration || 1; // Avoid division by zero
        player.currentTime = (val / 100) * duration;
        isDraggingProgress = false;
    });

    function updateSliderBackground(slider, value) {
        const percentage = value; // Value is already 0-100
        slider.style.background = `linear-gradient(to right, var(--text-main) ${percentage}%, #535353 ${percentage}%)`;
    }

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

            // Show album if it exists
            if (item.album && item.album.name) {
                // If album name is same as song title, it's likely a Single or self-titled track.
                // User wants to know if it's an album. 
                // Let's show it unless it's strictly "Single" AND user doesn't want "Single" label everywhere?
                // User said: "single olduğuda yazmıyo" -> implies they WANT to know if it's single.
                // But also: "her albüm verisi çekemediğin şeye single etiketi yapıştırma" -> Don't label Unknown as Single.

                // If the API explicitly returns an album name, we should show it.
                // If album name == title, it's a single usually, but we can verify against type if possible.
                // For now, let's just show what the API gives us, format " • AlbumName"

                if (item.album.name !== item.name) {
                    albumName = ` • ${item.album.name}`;
                } else {
                    // It's a Single or Title Track. Let's label as Single if it's a Single.
                    // Or just show nothing if it's redundant?
                    // "Block3 - KUSURA BAKMA • KUSURA BAKMA" looks weird.
                    // "Block3 - KUSURA BAKMA • Single" is better if we are sure.
                    // Since specific logic is hard without 'type', let's just NOT duplicate the title.
                    // But if it's NOT the title, show it.
                    // If it IS the title, maybe show nothing (cleaner) or show "Single"?
                    // Let's try adding "Single" if title == album.name
                    albumName = ` • Single`;
                }
            }

            // If album name matches artist name (Self-titled album), we SHOULD show it. 
            // e.g. "Metallica - Enter Sandman • Metallica" is valid info (it's from the album Metallica).
            // So we keep it.

            let thumb = "https://via.placeholder.com/150";

            if (item.thumbnails && item.thumbnails.length > 0) {
                thumb = item.thumbnails[item.thumbnails.length - 1].url;
            }

            card.innerHTML = `
                <div class="card-image" style="background-image: url('${thumb}')">
                    <div class="play-overlay">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5V19L19 12L8 5Z" /></svg>
                    </div>
                </div>
                <div class="card-info">
                    <div class="card-title">${title}</div>
                    <div class="card-artist">${artistName}${albumName}</div>
                </div>
                <div class="card-actions">
                    <button class="btn-icon favorite">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                    </button>
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

        let albumDisplay = "";

        if (track.album && track.album.name) {
            if (track.album.name !== track.name) {
                albumDisplay = ` • ${track.album.name}`;
            } else {
                albumDisplay = ` • Single`;
            }
        }

        document.querySelector('.track-artist').textContent = artistName + albumDisplay;

        let thumb = "https://via.placeholder.com/150";
        if (track.thumbnails && track.thumbnails.length > 0) {
            thumb = track.thumbnails[track.thumbnails.length - 1].url;
        }
        document.querySelector('.track-art').style.backgroundImage = `url('${thumb}')`;
        document.querySelector('.track-art').style.backgroundSize = "cover";

        try {
            const streamData = await window.api.getStream(track.videoId);
            console.log("Stream URL received:", streamData.url);

            // Update metadata from yt-dlp if available (more headers/accurate)
            if (streamData.metadata) {
                console.log("Received metadata from yt-dlp:", streamData.metadata);

                // Update Title
                if (streamData.metadata.title) {
                    document.querySelector('.track-title').textContent = streamData.metadata.title;
                }

                // Update Artist & Album
                let newArtist = artistName; // fallback to existing
                if (streamData.metadata.artist) {
                    newArtist = streamData.metadata.artist;
                }

                let newAlbumDisplay = "";
                if (streamData.metadata.album) {
                    if (streamData.metadata.album !== (streamData.metadata.title || track.name)) {
                        newAlbumDisplay = ` • ${streamData.metadata.album}`;
                    } else {
                        newAlbumDisplay = ` • Single`;
                    }
                }

                document.querySelector('.track-artist').textContent = newArtist + newAlbumDisplay;

                // Update Thumbnail if higher quality available
                if (streamData.metadata.thumbnail) {
                    document.querySelector('.track-art').style.backgroundImage = `url('${streamData.metadata.thumbnail}')`;
                }
            }

            player.src = streamData.url;
            player.play();
            isPlaying = true;
            document.getElementById('btn-play').innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>`;
        } catch (error) {
            console.error("Failed to play track:", error);
            // alert("Failed to play track. See console.");
        }
    }
});
