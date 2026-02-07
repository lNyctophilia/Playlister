# Playlister - Electron Design Document

## 1. Overview
**Project Name:** Playlister (Electron Version)
**Goal:** Create a modern, standalone desktop music player that aggregates YouTube Music content without ads, using a sleek "Spotify-like" interface.
**Target OS:** Windows (primary), potentially Linux/macOS.

## 2. Technical Stack
- **Framework:** Electron (Node.js + Chromium)
- **Language:** JavaScript (ES6+)
- **Frontend:** HTML5, CSS3 (Modern features: Flexbox, Grid, CSS Variables, Animations)
- **Backend Logic (Internal):** Node.js Main Process
- **Data Source:** YouTube Music (via `youtube-music-api` or `yt-music-api`)
- **Audio Engine:** HTML5 `<audio>` element or `Howler.js` (eliminates VLC dependency)
- **Package Manager:** NPM
- **Builder:** `electron-builder` (for generating .exe)

## 3. Architecture
The application follows the standard Electron multi-process architecture:

### 3.1. Main Process (`main.js`)
- **Responsibility:** Application lifecycle, Window management, Native menus, System tray, File System access (Config/Favorites), API calls (to avoid CORS issues in Renderer).
- **Modules:**
    - `WindowManager`: Handles window creation and state.
    - `ApiHandler`: Wraps the YouTube Music API.
    - `ConfigManager`: Reads/Writes `config.json` and `favorites.json`.

### 3.2. Preload Script (`preload.js`)
- **Responsibility:** Securely bridge the Main and Renderer processes using `contextBridge`.
- **Exposed APIs:**
    - `api.search(query)`
    - `api.getCharts(country)`
    - `player.load(url)`
    - `fs.saveFavorites(data)`

### 3.3. Renderer Process (UI)
- **Responsibility:** DOM manipulation, handling user events, playing audio, updating UI state.
- **Components:**
    - **Sidebar:** Navigation (Search, Charts, Genres, Favorites, Settings).
    - **Main Content Area:** Dynamic view based on selection.
    - **Player Bar:** Persistent bar at the bottom with Play/Pause, Next/Prev, Volume, Progress Bar, Current Track Info.

## 4. UI/UX Design
**Theme:** Dark / Glassmorphism (Modern, Premium feel).
**Color Palette:**
- Background: Very dark grey/black (`#121212`, `#181818`)
- Accent: Vibrant Primary Color (e.g., `#1DB954` Green or a Custom Gradient)
- Text: White / Light Grey

**Key Layout Elements:**
- **Left Sidebar:** Valid for navigation. Fixed width.
- **Bottom Player:** Fixed height. Always visible.
- **Center Stage:** Scrollable content area.

## 5. Data Management
- **Configuration:** Stored in `Config/config.json`.
- **Favorites:** Stored in `Config/favorites.json`.
- **Format:** JSON.
- **Migration:** The new app will read existing JSON files from the Python version if available.

## 6. Libraries & Dependencies
- `electron`: Core framework.
- `youtube-music-api`: For fetching metadata and streams.
- `ytdl-core` (optional): If direct stream URL extraction is complex, might be needed.
- `electron-store`: For simple data persistence (optional).

## 7. Development Roadmap
1.  **Setup:** Initialize Project & Window.
2.  **API Integration:** Connect to YT Music API.
3.  **Player Implementation:** Basic Play/Pause/Stream.
4.  **UI Construction:** Build the Sidebar and Player Bar.
5.  **Feature - Search:** Implement Search UI and logic.
6.  **Feature - Favorites:** Implement Save/Load logic.
7.  **Polish:** CSS styling, animations, error handling.
8.  **Packaging:** Generate `.exe`.
