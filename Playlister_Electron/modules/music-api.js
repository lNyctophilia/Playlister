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

            // Search for songs specifically to get better metadata
            const results = await this.api.search(query, "song");

            if (!results || !results.content) {
                return [];
            }

            // Map to the format renderer expecting:
            // renderer expects: { name, artist: {name}, album: {name, id?}, duration, thumbnails: [{url}] }
            return results.content.map(item => {
                // Handle artist structure (can be array or single object)
                let artistName = "Unknown";
                if (item.artist) {
                    if (Array.isArray(item.artist)) {
                        artistName = item.artist.map(a => a.name).join(', ');
                    } else {
                        artistName = item.artist.name;
                    }
                }

                // Handle album (critical fix)
                let albumName = "";
                if (item.album) {
                    albumName = item.album.name;
                }

                // Handle thumbnails (get specific resolution if possible, or use default)
                // The library usually returns an array of thumbnails
                let thumbnails = [];
                if (item.thumbnails && Array.isArray(item.thumbnails)) {
                    thumbnails = item.thumbnails;
                } else if (item.thumbnails) {
                    // Fallback if not array (unlikely but safe)
                    thumbnails = [{ url: item.thumbnails.url || item.thumbnails }];
                }

                return {
                    videoId: item.videoId,
                    name: item.name,
                    artist: { name: artistName },
                    album: { name: albumName },
                    duration: item.duration / 1000, // API returns ms, renderer might expect seconds? 
                    // Wait, let's check what yt-dlp was returning. 
                    // yt-dlp returns duration in seconds (float). 
                    // youtube-music-api returns ms (int). 
                    // Let's divide by 1000.
                    thumbnails: thumbnails,
                    type: 'song'
                };
            });

        } catch (error) {
            console.error("Search failed with youtube-music-api:", error);
            return [];
        }
    }
}

module.exports = new MusicApi();
