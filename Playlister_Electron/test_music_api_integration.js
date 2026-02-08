const musicApi = require('./modules/music-api');

(async () => {
    try {
        console.log("Initializing Music API...");
        await musicApi.init();

        console.log("Searching for 'Blok3'...");
        const results = await musicApi.search("Blok3");

        console.log(`Found ${results.length} results.`);

        if (results.length > 0) {
            const first = results[0];
            console.log("First Result Structure:");
            console.log(JSON.stringify(first, null, 2));

            // Validation Logic
            const isValid =
                first.videoId &&
                first.name &&
                first.artist && first.artist.name &&
                first.album && // album object exists
                (first.album.name !== undefined) && // album name exists (can be empty string)
                typeof first.duration === 'number' &&
                Array.isArray(first.thumbnails);

            if (isValid) {
                console.log("\n✅ Structure Validation PASSED");
                if (first.album.name) {
                    console.log(`✅ Album Name Found: "${first.album.name}"`);
                } else {
                    console.log("⚠️ Album Name is empty (might be a single or API issue?)");
                }
            } else {
                console.error("\n❌ Structure Validation FAILED");
            }
        }
    } catch (error) {
        console.error("Test Failed:", error);
    }
})();
