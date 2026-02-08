const YtDlp = require('./yt-dlp-wrapper');

class StreamExtractor {
    async getAudioStream(videoId) {
        try {
            const result = await YtDlp.getStream(videoId);
            return result; // Contains { url, metadata }
        } catch (error) {
            console.error("Error fetching stream:", error);
            throw error;
        }
    }
}

module.exports = new StreamExtractor();
