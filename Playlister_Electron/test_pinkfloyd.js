const MusicApi = require('./modules/music-api');
const fs = require('fs');

async function testSearch() {
    try {
        const queries = [
            "Pink Floyd - Time"
        ];

        let allResults = {};

        for (const q of queries) {
            console.log(`Searching for: ${q}`);
            const results = await MusicApi.search(q);
            if (results && results.length > 0) {
                allResults[q] = results.slice(0, 1);
            }
        }

        fs.writeFileSync('search_check_pinkfloyd.json', JSON.stringify(allResults, null, 2));
        console.log("Check complete");

    } catch (error) {
        console.error("Error:", error);
    }
}

testSearch();
