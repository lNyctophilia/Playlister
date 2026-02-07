class AudioPlayer {
    constructor() {
        this.audio = new Audio();
        this.currentTrack = null;
        this.isPlaying = false;

        // Event Listeners for UI updates
        this.audio.addEventListener('timeupdate', () => {
            if (this.onTimeUpdate) this.onTimeUpdate(this.audio.currentTime, this.audio.duration);
        });

        this.audio.addEventListener('ended', () => {
            this.isPlaying = false;
            if (this.onEnded) this.onEnded();
        });
    }

    load(url) {
        this.audio.src = url;
        this.audio.load();
    }

    play() {
        this.audio.play();
        this.isPlaying = true;
    }

    pause() {
        this.audio.pause();
        this.isPlaying = false;
    }

    toggle() {
        if (this.isPlaying) this.pause();
        else this.play();
        return this.isPlaying;
    }

    setVolume(volume) {
        this.audio.volume = volume / 100;
    }

    seek(time) {
        this.audio.currentTime = time;
    }
}

// Export for use in renderer
window.audioPlayer = new AudioPlayer();
