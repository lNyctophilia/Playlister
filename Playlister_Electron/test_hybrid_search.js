const musicApi = require('./modules/music-api');
const fs = require('fs');

async function testHybridSearch() {
    console.log("Testing Hybrid Search (API + yt-dlp batch)...");

    try {
        const results = await musicApi.search("UZI - Ou");

        let output = "";
        if (results.length === 0) {
            output += "No results found.\n";
        } else {
            output += `Found ${results.length} results.\n\n`;

            results.forEach((item, index) => {
                output += `[Result ${index + 1}]\n`;
                output += `Video ID: ${item.videoId}\n`;
                output += `Title: ${item.name}\n`;
                output += `Artist: ${item.artist.name}\n`;
                output += `Album: ${item.album.name}\n`;
                output += `Duration: ${item.duration}s\n`;
                output += '---\n';
            });

            const first = results.find(r => r.name.includes("Ou") && r.artist.name.includes("UZI"));

            if (first) {
                if (first.album.name === "Mortal Kombat") {
                    output += "\n✅ SUCCESS: Album correctly identified as 'Mortal Kombat'\n";
                } else {
                    output += `\n❌ FAILURE: Album is '${first.album.name}', expected 'Mortal Kombat'\n`;
                }
            } else {
                output += "\n❌ FAILURE: Could not find target song in results.\n";
            }
        }

        fs.writeFileSync('test_hybrid_search_output.txt', output);
        console.log("Output written to test_hybrid_search_output.txt");

    } catch (error) {
        console.error("Test failed:", error);
    }
}

testHybridSearch();
