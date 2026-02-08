const { spawn } = require('child_process');
const path = require('path');

const executable = path.join(__dirname, 'yt-dlp.exe');
const videoId = "jpKaptxKfnI"; // Blok3 - KUSURA BAKMA (Known working ID)

function testCommand(label, extraArgs) {
    return new Promise((resolve) => {
        console.log(`\n--- Testing: ${label} ---`);
        const args = [
            '-g',
            '-f', 'bestaudio',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            ...extraArgs,
            `https://www.youtube.com/watch?v=${videoId}`
        ];

        console.log("Command:", executable, args.join(" "));

        const process = spawn(executable, args);
        let stdout = '';
        let stderr = '';

        process.stdout.on('data', d => stdout += d.toString());
        process.stderr.on('data', d => stderr += d.toString());

        process.on('close', (code) => {
            if (code === 0 && stdout.trim()) {
                console.log("✅ SUCCESS. URL received (length: " + stdout.trim().length + ")");
                resolve(true);
            } else {
                console.log("❌ FAILED.");
                console.log("STDERR:", stderr);
                resolve(false);
            }
        });
    });
}

(async () => {
    // Test 1: Web client only
    await testCommand("Web Client Only", ['--extractor-args', 'youtube:player_client=web']);

    // Test 2: No extractor args (Default)
    await testCommand("Default Behavior", []);

    // Test 3: Android only (Expect Fail)
    // await testCommand("Android Only", ['--extractor-args', 'youtube:player_client=android']);
})();
