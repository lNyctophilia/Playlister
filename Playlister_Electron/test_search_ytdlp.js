const fs = require('fs');
const ytDlpWrapper = require('./modules/yt-dlp-wrapper');

async function testSearch() {
    console.log("Testing yt-dlp search for 'UZI - Ou'...");
    try {
        console.log("Attempt 2: Search using music.youtube.com URL");
        // We need to encode the query for the URL
        const query = "UZI - Ou";
        const url = `https://music.youtube.com/search?q=${encodeURIComponent(query)}`;

        // We can't use the wrapper's search() method directly because it forces `ytsearch:`.
        // We'll use the internal spawn logic or just modify the wrapper temporarily/permanently if this works.
        // For this test, let's just use the wrapper but pass the URL as if it was a query, 
        // BUT the wrapper prepends `ytsearch5:`. So we need to modify the wrapper or bypass it.
        // Let's modify the wrapper to accept a direct URL or different mode?
        // Or just let's write a raw spawn in this test script to verify feasibility first.

        const { spawn } = require('child_process');
        const path = require('path');
        const ytDlpPath = path.join(__dirname, 'modules', '..', 'yt-dlp.exe');

        const args = [
            '--dump-json',
            '--flat-playlist', // Get list content only, don't download
            '--no-warnings',
            '--ignore-errors',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            url
        ];

        console.log(`Running raw yt-dlp: ${ytDlpPath} ${args.join(' ')}`);

        const child = spawn(ytDlpPath, args);
        let stdout = '';

        child.stdout.on('data', d => stdout += d.toString());
        child.stderr.on('data', d => console.error(d.toString()));

        await new Promise(resolve => child.on('close', resolve));

        let output = "";
        try {
            const lines = stdout.trim().split('\n');
            const results = [];
            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    results.push(JSON.parse(line));
                } catch (e) { }
            }

            if (results.length === 0) {
                output += "No results found via music.youtube.com URL.\n";
            } else {
                output += `Found ${results.length} results via music.youtube.com URL.\n\n`;
                results.forEach((item, index) => {
                    // Note: result_type might be 'video', 'playlist', 'artist'
                    // music.youtube.com search results are complex mixed types
                    output += `[Result ${index + 1}] (${item.result_type || 'unknown'})\n`;
                    output += `Title: ${item.title}\n`;
                    output += `Artist: ${item.artist}\n`; // might be different field
                    output += `Album: ${item.album}\n`;
                    output += '---\n';
                });
            }
        } catch (e) { output += "Error parsing output: " + e.toString(); }

        fs.writeFileSync('test_search_output_clean.txt', output);
        console.log("Output written to test_search_output_clean.txt");

    } catch (error) {
        console.error("Test failed:", error);
    }
}

// testSearch(); 
// Call the function (I commented it out inside replacement content by mistake? No, looks fine)
testSearch();
