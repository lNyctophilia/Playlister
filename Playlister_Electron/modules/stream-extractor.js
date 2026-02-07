const ytdl = require('ytdl-core');

class StreamExtractor {
    async getAudioStream(videoId) {
        try {
            const info = await ytdl.getInfo(videoId);
            const format = ytdl.chooseFormat(info.formats, { quality: 'highestaudio' });
            return {
                url: format.url,
                title: info.videoDetails.title,
                author: info.videoDetails.author.name,
                duration: info.videoDetails.lengthSeconds,
                thumbnail: info.videoDetails.thumbnails[0].url
            };
        } catch (error) {
            console.error("Error fetching stream:", error);
            throw error;
        }
    }
}

module.exports = new StreamExtractor();
