const MusicApi = require('./modules/music-api');

(async () => {
    try {
        console.log("Searching...");
        const results = await MusicApi.search("Blok3");
        if (results && results.length > 0) {
            console.log("First result structure:", JSON.stringify(results[0], null, 2));
        } else {
            console.log("No results found.");
        }
    } catch (error) {
        console.error("Error:", error);
    }
})();
