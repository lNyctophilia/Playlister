const MusicApi = require('./modules/music-api');

async function testAlbum() {
    try {
        console.log("Searching details...");

        // Use a known single's album ID (if valid) or just search results
        // Actually, if search gives UC ID, we can't use getAlbum on it?
        // Let's try to getAlbum with the UC ID and see if it fails or returns something.

        // Blok3 - KUSURA BAKMA album browseId: UCZpmeLoLLb3vmxgscRyLPgw
        const invalidAlbumId = "UCZpmeLoLLb3vmxgscRyLPgw";

        console.log(`Testing getAlbum with ArtistChannel ID: ${invalidAlbumId}`);
        try {
            const album = await MusicApi.api.getAlbum(invalidAlbumId);
            console.log("Result (Unexpected):", album);
        } catch (e) {
            console.log("Error as expected (or not?):", e.message);
        }

    } catch (error) {
        console.error("Error:", error);
    }
}

testAlbum();
