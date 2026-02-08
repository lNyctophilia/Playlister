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

            console.log(`Running search: ${this.executable} ${args.join(' ')}`);

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
                if (code !== 0 && stdout.trim().length === 0) {
                    console.error("yt-dlp search failed with code", code);
                    return resolve([]);
                }

                try {
                    const lines = stdout.trim().split('\n');
                    const results = [];

                    for (const line of lines) {
                        if (!line.trim()) continue;
                        try {
                            const item = JSON.parse(line);

                            // Map to renderer format:
                            // renderer expects: { videoId, name, artist: {name}, album: {name}, duration, thumbnails: [{url}], type: 'song' }

                            results.push({
                                videoId: item.id,
                                name: item.title || item.fulltitle,
                                artist: { name: item.artist || item.uploader || "Unknown" },
                                album: { name: item.album || "" },
                                duration: item.duration, // in seconds
                                thumbnails: item.thumbnail ? [{ url: item.thumbnail }] : [],
                                type: 'song'
                            });
                        } catch (parseError) {
                            console.error("Failed to parse search result line:", parseError);
                        }
                    }

                    resolve(results);

                } catch (error) {
                    console.error("Processing search output failed:", error);
                    resolve([]);
                }
            });
        });
    }

    async getStream(videoId) {
        return new Promise((resolve, reject) => {
            const url = `https://www.youtube.com/watch?v=${videoId}`;
            const args = [
                '--dump-json',
                '-f', 'bestaudio',
                '--no-playlist',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                // '--extractor-args', 'youtube:player_client=web', 
                url
            ];

            console.log(`Getting stream & metadata: ${this.executable} ${args.join(' ')}`);

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

                try {
                    const data = JSON.parse(stdout);
                    if (data.url) {
                        resolve({
                            url: data.url,
                            metadata: {
                                album: data.album,
                                artist: data.artist,
                                title: data.title || data.fulltitle,
                                duration: data.duration,
                                thumbnail: data.thumbnail
                            }
                        });
                    } else {
                        reject(new Error("No URL returned in JSON"));
                    }
                } catch (e) {
                    console.error("Failed to parse JSON output from yt-dlp", e);
                    reject(e);
                }
            });
        });
    }
}

module.exports = new YtDlpWrapper();
