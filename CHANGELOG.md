# Changelog

All notable changes to Editara will be documented in this file.  
This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] – 2025-06-10

### Added
- **Settings Menu**:
  - Added a menu bar with options for Privacy, Documentation, Policy, Help, and About.
  - Implemented scrollable pop-up windows for Privacy, Documentation, Policy, and Help with detailed information about app usage, privacy, and support.
  
- **Video Cropping Support**:
  - Added start and end time inputs for cropping videos during conversion.
  - Integrated UI elements to specify crop times in seconds for video mode.

- **File Preview Enhancements**:
  - Added a "Preview" button to display a scrollable preview window for selected files.
  - Implemented thumbnail previews for images and video first frames (if moviepy is available).
  - Added per-file progress bars in the preview window to show conversion progress.
  - Included a "Remove" button for each file in the preview window to allow selective file removal.

- **Update Auto-Download**:
  - Enhanced the update checker to automatically download and run the latest .exe installer from GitHub releases when an update is confirmed by the user.

- **Theme File Change**:
  - Changed theme persistence file from `theme.json` to `app.json` for better app-specific configuration.

- **New Dependency**:
  - Added `urllib.parse` for parsing download URLs in the update checker.

### Changed
- **User Interface**:
  - Replaced radio buttons for Image/Video mode selection with styled buttons for a cleaner look.
  - Moved mode selection buttons to the top-right of the settings card for better layout organization.
  - Updated button styles for Image/Video mode to reflect active/inactive states with theme-aware colors.
  - Adjusted window centering logic to account for updated UI components.
  - Improved popup window positioning to center relative to the main window.

- **Update Mechanism**:
  - Changed update process to download the `.exe` file directly to the user's Downloads folder and auto-run it, instead of opening the GitHub release page in a browser.
  - Added validation to ensure an `.exe` asset exists in the latest GitHub release before attempting download.

- **Conversion Logic**:
  - Integrated video cropping functionality into the video conversion workflow, allowing users to specify start and end times.
  - Improved error handling for invalid crop time inputs by allowing optional inputs and using defaults when invalid.

- **File Handling**:
  - Enhanced file validation to prevent processing of files with unsupported extensions based on the selected mode.
  - Updated drag-and-drop and browse functionality to provide more specific error messages for invalid files.

- **Splash Screen**:
  - Ensured splash screen uses `resource_path` for consistent logo loading across development and PyInstaller environments.

### Fixed
- **Theme Application**:
  - Fixed theme application to consistently update Image/Video mode buttons' appearance when toggling themes.
  - Ensured progress bars and sliders adopt theme colors correctly using `ttk.Style` configurations.

- **Icon Loading**:
  - Removed redundant icon loading code in `__init__` to prevent duplicate attempts and potential errors.

- **Preview Stability**:
  - Fixed memory leaks in preview window by properly storing and referencing image objects.
  - Improved error handling for unsupported file types or corrupted media during preview.

- **Update Checker**:
  - Added checks for GitHub server availability to prevent crashes when the server is down.

### Removed
- **Webbrowser Dependency**:
  - Removed `webbrowser` import as the update mechanism no longer opens the GitHub release page in a browser.

- **Old Mode Selection**:
  - Removed radio button-based mode selection in favor of button-based mode switching.

---

## [1.0.0] – 2025-06-04

### Added
- **Video Conversion Support**:
  - Introduced support for video file formats (`.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`) using moviepy.
  - Added UI with radio buttons to switch between Image and Video conversion modes.
  - Implemented codec options (`libx264`, `libvpx`) and resolution-based resizing.

- **Resizing Capabilities**:
  - Added support for resizing images and videos by width, height, or both.
  - Integrated input validation for numeric resize fields in the UI.

- **Splash Screen**:
  - Implemented a 2-second startup splash screen featuring `logo.png` or fallback text ("Loading...").

- **Theme Persistence**:
  - Theme preferences (light/dark) are now saved in `theme.json` and persist across sessions.

- **File Type Detection**:
  - Added logic to track and validate selected file types based on the active mode.

- **Improved Update Checker**:
  - Enhanced update mechanism to detect all GitHub releases, including pre-releases.
  - Added internet and GitHub connectivity checks before fetching release data.

- **New Dependencies**:
  - Integrated moviepy for video processing.
  - Added packaging for semantic version comparisons.

### Changed
- **Versioning**:
  - Promoted from 1.0.0 (Pre-release) to stable 1.0.0.

- **User Interface**:
  - Updated window title to 🖼️ Image Format Converter.
  - Increased default window size to 600x600 and set minimum size to 550x550.
  - Renamed conversion button from "🚀 Convert Images" to a mode-agnostic "🚀 Convert".
  - Format dropdown now updates dynamically based on selected conversion mode.
  - Updated drag-and-drop instructions to reflect support for both image and video files.
  - Replaced `icon.png` with `appicon.ico` for better compatibility with PyInstaller packaging.

- **File Handling**:
  - Enhanced file browsing and drag-drop logic to validate extensions by selected mode.
  - Updated file preview and info section to reflect mode-specific file filtering.

- **About Dialog**:
  - Updated GitHub profile link to [github.com/basharulalammazu](https://github.com/basharulalammazu).
  - Updated support email to `basharulalammazu6@gmail.com`.

- **Conversion Logic**:
  - Prevented cross-mode conversions (e.g., attempting to convert an image to a video format).
  - Integrated resizing functionality into both image and video conversion workflows.

### Fixed
- **Resource Loading**:
  - Ensured resource files (icons, splash) are correctly loaded when bundled via PyInstaller using `resource_path`.

- **UI Layout**:
  - Refined spacing and alignment for new UI components including mode switch and resize settings.

- **Dependency Handling**:
  - Added fallback error handling for missing moviepy when attempting video conversions.

### Removed
- No features were removed in this release.

---

## [1.0.0-pre-release] – 2025-05-03

**Initial Preview Release**
- Implemented image format conversion between: JPG, PNG, BMP, TIFF, WEBP, HEIC.
- Added batch processing for image files.
- Included light/dark theme toggle with real-time switching.
- Introduced progress indicators and file status tracking.
- Provided About dialog with developer contact information and update checking functionality.
