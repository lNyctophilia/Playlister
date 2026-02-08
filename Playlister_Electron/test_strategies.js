const { spawn } = require('child_process');
const path = require('path');

const executable = path.join(__dirname, 'yt-dlp.exe');
const videoId = "jpKaptxKfnI";

function testCommand(label, extraArgs) {
    return new Promise((resolve) => {
        console.log(`\n--- Testing: ${label} ---`);
        const args = [
            '-g',
            '-f', 'bestaudio',
            '--no-warnings',
            // '--verbose', // Uncomment for debug
            ...extraArgs,
            `https://www.youtube.com/watch?v=${videoId}`
        ];

        console.log("Args:", args.join(" "));

        const process = spawn(executable, args);
        let stdout = '';
        let stderr = '';

        process.stdout.on('data', d => stdout += d.toString());
        process.stderr.on('data', d => stderr += d.toString());

        process.on('close', (code) => {
            if (code === 0 && stdout.trim().startsWith("http")) {
                console.log(`✅ SUCCESS (${label})`);
                resolve(true);
            } else {
                console.log(`❌ FAILED (${label})`);
                console.log("STDERR:", stderr.split('\n')[0]); // First line only
                resolve(false);
            }
        });
    });
}

(async () => {
    // 1. Android (often reliable for audio)
    await testCommand("Android", ['--extractor-args', 'youtube:player_client=android']);

    // 2. iOS (often requires PO Token now)
    await testCommand("iOS", ['--extractor-args', 'youtube:player_client=ios']);

    // 3. Web (failed previously with signature)
    await testCommand("Web", ['--extractor-args', 'youtube:player_client=web']);

    // 4. MWeb (Mobile Web)
    await testCommand("MWeb", ['--extractor-args', 'youtube:player_client=mweb']);

    // 5. TV (Embedded)
    await testCommand("TV", ['--extractor-args', 'youtube:player_client=tv']);

    // 6. Default (No args)
    await testCommand("Default", []);
})();
