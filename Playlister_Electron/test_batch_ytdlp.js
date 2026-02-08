const { spawn } = require('child_process');
const path = require('path');
const ytDlpPath = path.join(__dirname, 'yt-dlp.exe');

// IDs from youtube-music-api search (UZI - Ou, etc.)
const ids = ['FzoxTZ8shWY', 'YiJAxtSdeTw', '_2-bzgB_LSw'];

async function testBatchMetadata() {
    console.log(`Testing batch metadata fetch for ${ids.length} items...`);
    const startTime = Date.now();

    const urls = ids.map(id => `https://www.youtube.com/watch?v=${id}`);

    const args = [
        '--dump-json',
        '--no-playlist',
        '--no-warnings',
        '--ignore-errors',
        ...urls
    ];

    const child = spawn(ytDlpPath, args);
    let stdout = '';

    child.stdout.on('data', d => stdout += d.toString());
    child.stderr.on('data', d => console.error(d.toString())); // Progress info

    await new Promise(resolve => child.on('close', resolve));

    const duration = (Date.now() - startTime) / 1000;
    console.log(`\nBatch fetch completed in ${duration} seconds.`);

    const lines = stdout.trim().split('\n');
    let foundAlbum = false;

    lines.forEach(line => {
        try {
            if (!line.trim()) return;
            const data = JSON.parse(line);
            console.log(`ID: ${data.id} | Title: ${data.fulltitle} | Album: ${data.album}`);
            if (data.album === "Mortal Kombat") foundAlbum = true;
        } catch (e) { }
    });

    if (foundAlbum) {
        console.log("✅ verified: Found 'Mortal Kombat' in batch results.");
    } else {
        console.log("❌ Failed to find 'Mortal Kombat'.");
    }
}

testBatchMetadata();
