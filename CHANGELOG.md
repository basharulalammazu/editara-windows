# Changelog

All notable changes to **Editara** will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)  
and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] – 2025-06-04

### Added
- **Video Conversion Support**:
  - Introduced support for video file formats (`.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`) using `moviepy`.
  - Added UI with radio buttons to switch between *Image* and *Video* conversion modes.
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
  - Integrated `moviepy` for video processing.
  - Added `packaging` for semantic version comparisons.

### Changed
- **Versioning**:
  - Promoted from `1.0.0 (Pre-release)` to stable `1.0.0`.
- **User Interface**:
  - Updated window title to **🖼️ Image Format Converter**.
  - Increased default window size to `600x600` and set minimum size to `550x550`.
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
  - Added fallback error handling for missing `moviepy` when attempting video conversions.

### Removed
- No features were removed in this release.

---

## [1.0.0-pre-release] – 2025-05-03

### Initial Preview Release
- Implemented image format conversion between: JPG, PNG, BMP, TIFF, WEBP, HEIC.
- Added batch processing for image files.
- Included light/dark theme toggle with real-time switching.
- Introduced progress indicators and file status tracking.
- Provided *About* dialog with developer contact information and update checking functionality.
