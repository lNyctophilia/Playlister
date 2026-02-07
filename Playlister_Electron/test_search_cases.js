const MusicApi = require('./modules/music-api');
const fs = require('fs');

async function testSearch() {
    try {
        const queries = [
            "Blok3 - KUSURA BAKMA", // Single likely
            "The Weeknd - Starboy", // Album track
            "Beyonce - Beyonce"     // Self-titled album check, or Artist==Album check
        ];

        let allResults = {};

        for (const q of queries) {
            console.log(`Searching for: ${q}`);
            const results = await MusicApi.search(q);
            if (results && results.length > 0) {
                // Taking the first 2 results for each query
                allResults[q] = results.slice(0, 2);
            } else {
                allResults[q] = "No results";
            }
        }

        fs.writeFileSync('search_results.json', JSON.stringify(allResults, null, 2));
        console.log("Results saved to search_results.json");

    } catch (error) {
        console.error("Error:", error);
    }
}

testSearch();
