const YTMusic = require('ytmusic-api');

async function testNewApi() {
    const ytmusic = new YTMusic();
    await ytmusic.initialize();

    const queries = [
        "Blok3 - KUSURA BAKMA",
        "The Weeknd - Starboy",
        "Pink Floyd - Time",
        "Beyonce - Beyonce"
    ];

    for (const q of queries) {
        console.log(`\nSearching for: ${q}`);
        // Search for songs
        const songs = await ytmusic.search(q);

        if (songs && songs.length > 0) {
            // Log the first result
            // The library returns objects. Let's see the structure.
            const firstResult = songs[0];
            console.log("Name:", firstResult.name);
            console.log("Artist:", firstResult.artist.name);
            if (firstResult.album) {
                console.log("Album:", firstResult.album.name);
                console.log("Album ID:", firstResult.album.id);
            } else {
                console.log("Album: undefined");
            }
            console.log("Type:", firstResult.type); // Should be 'SONG' or similar
        } else {
            console.log("No results found.");
        }
    }
}

testNewApi().catch(e => console.error(e));
