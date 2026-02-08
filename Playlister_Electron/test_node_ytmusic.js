const YoutubeMusic = require('node-youtube-music');

async function testNodeYoutubeMusic() {
    const queries = [
        "Blok3 - KUSURA BAKMA",
        "The Weeknd - Starboy",
        "Pink Floyd - Time",
        "Beyonce - Beyonce"
    ];

    for (const q of queries) {
        console.log(`\nSearching for: ${q}`);
        // Search for songs
        try {
            const songs = await YoutubeMusic.searchMusics(q);

            if (songs && songs.length > 0) {
                const firstResult = songs[0];
                console.log("Name:", firstResult.title);
                console.log("Artist:", firstResult.artists ? firstResult.artists.map(a => a.name).join(', ') : "Undefined");
                if (firstResult.album) {
                    console.log("Album:", firstResult.album.name);
                    console.log("Album ID:", firstResult.album.id);
                } else {
                    console.log("Album: undefined");
                }
                console.log("Type:", "Song"); // Wrapper typically returns songs
            } else {
                console.log("No results found.");
            }
        } catch (e) {
            console.log("Error:", e.message);
        }
    }
}

testNodeYoutubeMusic();
