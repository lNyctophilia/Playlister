const musicApi = require('./modules/music-api');
const fs = require('fs');

async function verifyRefinedSearch() {
    console.log("Verifying Refined Search (Limit 20 + Smart Metadata)...");

    try {
        const results = await musicApi.search("UZI - Ou");

        let output = "";
        output += `Found ${results.length} results (Expected ~20).\n\n`;

        results.forEach((item, index) => {
            output += `[Result ${index + 1}]\n`;
            output += `Title: ${item.name}\n`;
            output += `Artist: ${item.artist.name}\n`;
            output += `Album: ${item.album.name}\n`;
            output += `Duration: ${item.duration}\n`;
            output += '---\n';
        });

        const first = results[0];
        // Check if first result is "UZI - Ou" with correct Artist "UZI" (from API) and Album "Mortal Kombat" (from yt-dlp)

        let hasMortalKombat = results.some(r => r.album.name === "Mortal Kombat");
        let hasCorrectArtist = results.some(r => r.artist.name.includes("UZI"));

        if (hasMortalKombat && hasCorrectArtist) {
            output += "\n✅ SUCCESS: Found 'Mortal Kombat' album and 'UZI' artist.\n";
        } else {
            output += `\n❌ FAILURE: MortalKombat=${hasMortalKombat}, CorrectArtist=${hasCorrectArtist}\n`;
        }

        fs.writeFileSync('verify_refined_search.txt', output);
        console.log("Output written to verify_refined_search.txt");

    } catch (error) {
        console.error("Test failed:", error);
    }
}

verifyRefinedSearch();
