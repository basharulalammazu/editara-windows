## [1.2.0] - 2025-06-20
### ✨ New Features & Improvements
- **Image Crop Tool:** Added interactive cropping dialog with zoom, fit-to-view, and clear crop selection.
- **Loading Spinner:** Circular waiting animation overlay during image edit operations (crop, background removal, quality improve, passport).
- **File Preview Remove:** Added "Remove" (❌) button for each file in the preview dialog, allowing users to remove files before conversion.
- **OpenCV-Only Background Removal:** Fallback to OpenCV GrabCut for background removal if rembg/onnxruntime are unavailable.
- **Better Large Image Handling:** Crop dialog now displays original image size and supports zoom controls for large images.
- **Improved Error Handling:** More robust error messages and graceful fallback for missing dependencies.

### 🐛 Bug Fixes
- Fixed `QPoint` import for PyQt6 (now from `QtCore`).
- Fixed tuple unpacking in worker results for conversion completion.
- Fixed missing `show_loading` method in main app class.
- Fixed crop dialog not resetting selection.
- Fixed UI freezes and overlay cleanup after processing.

---

## [1.1.0] - 2025-06-03
### 🚀 Feature Update: Extended Functionality & UI
- **Menu Bar Added**  
  Added a top menu bar with a "Settings" dropdown:
  - Privacy Policy, Documentation, Policy, Help, About dialogs now accessible from the menu.
  - Enhances user accessibility without cluttering the main UI.

- **File Preview Window**  
  - New "Preview" button shows a scrollable popup with thumbnails/previews of selected files.
  - Allows file removal before conversion.
  - Includes individual progress bars for each file.

- **Video Cropping Feature**  
  - Added input fields to trim videos using start and end time (in seconds).
  - Available in video mode only.

- **Image/Video Mode Toggle Buttons**  
  - Replaced old radio buttons with styled toggle buttons for a more modern feel.

### ✨ UI/UX Enhancements
- **Custom Scrollable Popup Dialogs**  
  - Replaced most `messagebox` warnings and errors with themed scrollable popups.
  - Used for long messages (privacy, policy, errors, etc.).

- **Per-File Progress Bars in Preview**  
  - See real-time progress for each selected file inside the preview window.

- **Modern Mode Switching**  
  - Visually styled buttons to switch between "Image" and "Video" modes with color feedback.

### 🛠 Improvements
- Improved consistency of error/info messages using custom popup handler.
- Email in About window updated to `basharulalammazu6@gmail.com`.
- GitHub link behavior improved for About dialog.

### 🐞 Fixes
- Redundant `grid` call in GitHub label (minor internal cleanup).
- `center_window` method defined but not called (no visual issue due to `__init__` layout coverage).

---

## [1.0.0] - 2025-06-02
### 🎉 New Stable Release
- First official full release (after `v1.0.0-pre-release`)

### ✨ Features Added
- Video format conversion (MP4, AVI, MOV, etc.)
- Video resizing by resolution
- Image resizing (custom width & height)

### 🛠 Improvements
- Optimized batch image conversion performance
- Enhanced drag & drop handling
- Clearer status updates with improved progress tracking

### 💄 UI Enhancements
- Minor UI polish for theme toggle and button styling
- Updated file size info and output path display

---

## [1.0.0-pre-release] - 2025-05-01
### 🧪 Initial Preview Release
- Convert images between JPG, PNG, BMP, TIFF, WEBP, HEIC
- Batch processing support
- Dark/light theme toggle
- Progress and status indicators
- About dialog with developer info and update checker