const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

class YtDlpWrapper {
    constructor() {
        // Assume yt-dlp.exe is in the root (where package.json is)
        this.executable = path.join(__dirname, '..', 'yt-dlp.exe');
        if (!fs.existsSync(this.executable)) {
            console.error("Yt-dlp executable NOT found at:", this.executable);
        } else {
            console.log("Yt-dlp executable found at:", this.executable);
        }
    }

    async search(query, limit = 5) {
        return new Promise((resolve, reject) => {
            // "ytsearch<N>:<query>"
            const searchArg = `ytsearch${limit}:${query}`;

            const args = [
                '--dump-json',
                '--default-search', `ytsearch${limit}`,
                '--no-playlist',
                '--no-warnings',
                '--ignore-errors',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                '--extractor-args', 'youtube:player_client=ios,android,web',
                searchArg
            ];

            console.log(`Running: ${this.executable} ${args.join(' ')}`);

            const process = spawn(this.executable, args);
            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            process.on('close', (code) => {
                if (stderr) {
                    // console.warn("yt-dlp stderr:", stderr); 
                }

                if (code !== 0 && stdout.trim().length === 0) {
                    console.error("yt-dlp failed with code", code);
                    return resolve([]); // Graceful failure
                }

                try {
                    const lines = stdout.trim().split('\n');
                    const results = [];

                    for (const line of lines) {
                        if (!line.trim()) continue;
                        try {
                            const item = JSON.parse(line);
                            results.push({
                                id: item.id,
                                title: item.title || item.fulltitle,
                                uploader: item.uploader || item.artist || "Unknown",
                                album: item.album || "",
                                duration: item.duration,
                                thumbnail: item.thumbnail,
                                webpage_url: item.webpage_url
                            });
                        } catch (parseError) {
                            console.error("Failed to parse line:", parseError);
                        }
                    }

                    resolve(results);

                } catch (error) {
                    console.error("Processing output failed:", error);
                    resolve([]);
                }
            });
        });
    }

    async getStream(videoId) {
        return new Promise((resolve, reject) => {
            const url = `https://www.youtube.com/watch?v=${videoId}`;
            const args = [
                '-g',
                '-f', 'bestaudio',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                // '--extractor-args', 'youtube:player_client=web', // REMOVED: Default works best
                url
            ];

            console.log(`Getting stream: ${this.executable} ${args.join(' ')}`);

            const process = spawn(this.executable, args);
            let stdout = '';
            let stderr = '';

            process.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            process.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            process.on('close', (code) => {
                if (code !== 0) {
                    console.error("yt-dlp getStream failed:", stderr);
                    return reject(new Error(stderr || "Failed to get stream"));
                }
                const streamUrl = stdout.trim();
                if (streamUrl) {
                    resolve(streamUrl);
                } else {
                    reject(new Error("Empty URL returned"));
                }
            });
        });
    }
}

module.exports = new YtDlpWrapper();
