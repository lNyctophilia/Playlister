const YoutubeMusicApi = require('youtube-music-api');

const api = new YoutubeMusicApi();

(async () => {
    try {
        await api.initalize();
        console.log("Searching for 'Pink Floyd Comfortably Numb'...");
        const results = await api.search("Pink Floyd Comfortably Numb", "song");

        if (results.content && results.content.length > 0) {
            const item = results.content[0];
            console.log("Title:", item.name);
            console.log("Artist:", item.artist ? (Array.isArray(item.artist) ? item.artist.map(a => a.name).join(', ') : item.artist.name) : "N/A");
            console.log("Album:", item.album ? item.album.name : "N/A");
        } else {
            console.log("No results");
        }
    } catch (e) {
        console.error("Error:", e);
    }
})();
