const YoutubeMusicApi = require('youtube-music-api');

class MusicApi {
    constructor() {
        this.api = new YoutubeMusicApi();
        this.isInitialized = false;
    }

    async init() {
        if (!this.isInitialized) {
            try {
                await this.api.initalize(); // Note: 'initalize' is a typo in the library itself, sadly common
                this.isInitialized = true;
                console.log("YouTube Music API Initialized");
            } catch (error) {
                console.error("Failed to initialize YouTube Music API:", error);
                throw error;
            }
        }
    }

    async search(query) {
        await this.init();
        try {
            const result = await this.api.search(query, "song");
            if (result.content && result.content.length > 0) {
                require('fs').writeFileSync('debug_raw_item.json', JSON.stringify(result.content[0], null, 2));
            }
            return result.content;
        } catch (error) {
            console.error("Search failed:", error);
            return [];
        }
    }

    async getCharts(country = 'US') {
        await this.init();
        // The library might not support direct charts for all countries easily, 
        // but we can simulate it or use specific playlists.
        // For now, let's implemented a basic search as a placeholder or explore library capabilities.
        // 'getCharts' isn't standard in all wrappers, falling back to a popular playlist search
        try {
            const result = await this.api.search("Top 100 " + country, "playlist");
            return result.content;
        } catch (error) {
            console.error("Get Charts failed:", error);
            return [];
        }
    }
}

module.exports = new MusicApi();
