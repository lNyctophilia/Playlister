const YoutubeMusicApi = require('youtube-music-api');

class MusicApi {
    constructor() {
        this.api = new YoutubeMusicApi();
        this.isInitialized = false;
    }

    async init() {
        if (!this.isInitialized) {
            try {
                // Note: The library has a known typo 'initalize' instead of 'initialize'
                await this.api.initalize();
                this.isInitialized = true;
                console.log("YouTube Music API initialized successfully.");
            } catch (error) {
                console.error("Failed to initialize YouTube Music API:", error);
            }
        }
    }

    async search(query) {
        try {
            if (!this.isInitialized) {
                await this.init();
            }

            console.log(`Searching for '${query}' using YouTube Music API (for initial list)...`);
            // Search for songs specifically to get better metadata (and reliable IDs)
            const results = await this.api.search(query, "song");

            if (!results || !results.content) {
                return [];
            }

            // Get top 20 video IDs to fetch detailed metadata for (User requested more results)
            const topResults = results.content.slice(0, 20);

            // Create a map for quick lookup of original API data (Artist Name is better here)
            const apiDataMap = new Map();
            const videoIds = [];

            topResults.forEach(item => {
                if (item.videoId) {
                    videoIds.push(item.videoId);

                    // Parse artist name from API
                    let artistName = "Unknown";
                    if (item.artist) {
                        if (Array.isArray(item.artist)) {
                            artistName = item.artist.map(a => a.name).join(', ');
                        } else {
                            artistName = item.artist.name;
                        }
                    }

                    apiDataMap.set(item.videoId, {
                        name: item.name,
                        artist: artistName,
                        thumbnails: item.thumbnails // low res but immediate
                    });
                }
            });

            if (videoIds.length === 0) {
                return [];
            }

            console.log(`Fetching detailed metadata for ${videoIds.length} items using yt-dlp...`);

            const { spawn } = require('child_process');
            const path = require('path');
            const ytDlpPath = path.join(__dirname, '..', 'yt-dlp.exe');

            const urls = videoIds.map(id => `https://www.youtube.com/watch?v=${id}`);
            const args = [
                '--dump-json',
                '--no-playlist',
                '--no-warnings',
                '--ignore-errors',
                ...urls
            ];

            const child = spawn(ytDlpPath, args);
            let stdout = '';

            child.stdout.on('data', d => stdout += d.toString());

            // Wait for process
            await new Promise(resolve => child.on('close', resolve));

            const lines = stdout.trim().split('\n');
            const enhancedResults = [];

            // We want to maintain ratio of results even if yt-dlp fails for some? 
            // Better to rely on yt-dlp output for order or map back?
            // yt-dlp outputs in order of input arguments usually.

            lines.forEach(line => {
                if (!line.trim()) return;
                try {
                    const data = JSON.parse(line);
                    const apiData = apiDataMap.get(data.id);

                    // SMART MERGE STRATEGY:
                    // 1. Artist: API is better (yt-dlp gives "Uploader" which might be "S.O.S" instead of "UZI")
                    // 2. Title: API is usually cleaner, but yt-dlp is fine too. Let's stick to API for consistency with Artist.
                    // 3. Album: yt-dlp is BETTER (API gave Artist Name as Album).
                    // 4. Thumbnail: yt-dlp (data.thumbnail) is usually higher res.
                    // 5. Duration: yt-dlp is precise.

                    enhancedResults.push({
                        videoId: data.id,
                        name: apiData ? apiData.name : (data.title || data.fulltitle),
                        artist: { name: apiData ? apiData.artist : (data.artist || data.uploader || "Unknown") },
                        album: { name: data.album || "" }, // The Critical Fix
                        duration: data.duration,
                        thumbnails: data.thumbnail ? [{ url: data.thumbnail }] : (apiData ? apiData.thumbnails : []),
                        type: 'song'
                    });
                } catch (e) {
                    console.error("Failed to parse yt-dlp JSON:", e);
                }
            });

            return enhancedResults;

        } catch (error) {
            console.error("Search failed:", error);
            return [];
        }
    }
}

module.exports = new MusicApi();
