const YtDlp = require('./yt-dlp-wrapper');

class StreamExtractor {
    async getAudioStream(videoId) {
        try {
            const url = await YtDlp.getStream(videoId);
            return {
                url: url
                // Metadata is already handled by search result usually, 
                // but if we needed fresh meta, we'd have to call yt-dlp --dump-json again.
                // For now, renderer relies on search result for metadata display.
            };
        } catch (error) {
            console.error("Error fetching stream:", error);
            throw error;
        }
    }
}

module.exports = new StreamExtractor();
