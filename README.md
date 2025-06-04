# Editara - Image & Video Format Converter

![Editara Logo](logo.png)

**Editara** is a cross-platform desktop tool that simplifies image and video format conversion. With intuitive UI design, drag-and-drop support, dark/light themes, resizing capabilities, and support for major formats, it’s ideal for both everyday users and power users.

---

## 🚀 Features

- ✅ **Image Conversion**: Convert `jpg`, `jpeg`, `png`, `bmp`, `tiff`, `webp`, `heic`
- ✅ **Video Conversion**: Convert `mp4`, `avi`, `mov`, `mkv`, `webm` *(via `moviepy`)*
- ✅ **Resize Options**: Set width and/or height while preserving aspect ratio
- ✅ **Quality Control**: Adjust image quality for JPEG/WebP
- ✅ **Drag & Drop Support**: Quick file/folder input
- ✅ **Dark/Light Theme**: Toggle between light 🌞 and dark 🌙 modes
- ✅ **Theme Persistence**: Remembers your theme preference
- ✅ **Splash Screen**: Displays logo on startup
- ✅ **Update Checker**: Alerts for new GitHub releases
- ✅ **About Developer**: Quick access to GitHub, portfolio, and email

---

## 📸 Screenshots

| Dark Theme                        | Light Theme                        |
|----------------------------------|------------------------------------|
| ![](screenshots/dark_theme.png)  | ![](screenshots/light_theme.png)   |

---

## 🛠️ Installation

### Requirements

- **Python**: `3.8+`
- **Libraries**:
  - `Pillow`
  - `tkinterdnd2`
  - `requests`
  - `packaging`
  - `moviepy` *(optional for video support)*
  - Tkinter *(comes with Python on most systems)*

### Installation (Source)

```bash
git clone https://github.com/basharulalammazu/editara-windows.git
cd editara-windows
pip install pillow tkinterdnd2 requests packaging
pip install moviepy  # Optional
python editara.py
````

### Windows Executable

* Download from [Releases](https://github.com/basharulalammazu/editara-windows/releases)
* Extract the zip
* Run `Editara.exe`

---

## 📒 Usage Guide

### Launch

* Run via `python editara.py` *(source)* or `Editara.exe` *(Windows EXE)*

### Workflow

1. **Select Mode**: Image or Video
2. **Add Files**: Browse or drag-and-drop
3. **Choose Format**: e.g., PNG for images, MP4 for videos
4. **Optional Settings**:

   * Quality (for JPEG/WEBP)
   * Resize by width/height/both
5. **Convert**: Click `🚀 Convert`
6. **Output**: Files saved to `Converted_to_[format]/` in source directory

### Extras

* 🌗 **Theme Toggle**: Dark/Light theme switch
* 🔄 **Update Check**: Notifies if a new version is available
* ℹ️ **About**: Shows developer info

---

## 💻 System Requirements

| Component  | Requirement                       |
| ---------- | --------------------------------- |
| OS         | Windows 10/11, macOS, or Linux    |
| RAM        | 4 GB (8 GB for large video files) |
| Disk Space | 100 MB + space for output files   |
| Python     | 3.8 or newer (source version)     |
| Processor  | CPU only; no GPU required         |

---

## 🏗️ Building Executables (Optional)

To build with **PyInstaller**:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed \
  --icon=appicon.ico \
  --add-data="appicon.ico;." \
  --add-data="logo.png;." \
  editara.py
```

Output will be in the `dist/` folder.

> ✅ Make sure `logo.png` and `appicon.ico` exist in the root directory.

---

## 🐞 Known Issues

* **moviepy**: Ensure `ffmpeg` is installed or accessible
* **Large Files**: Video conversion may be slow
* **Linux Support**: `tkinterdnd2` may need extra setup (`libx11-dev`, etc.)
* **Icons on macOS/Linux**: `.ico` may not render properly; prefer `.png`

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Submit a Pull Request

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 📋 Changelog

See [CHANGELOG.md](CHANGELOG.md) for full release history.

> Highlights in **v1.0.0**:
>
> * Added video conversion support
> * Resize feature (width, height, both)
> * Splash screen
> * Theme memory across sessions

---

## 📄 License

Licensed under the [MIT License](LICENSE).

---

## 👨‍💻 About the Developer

* **Name**: Basharul Alam Mazu
* **GitHub**: [basharulalammazu](https://github.com/basharulalammazu)
* **Website**: [basharulalammazu.github.io](https://basharulalammazu.github.io)
* **Email**: [basharulalammazu6@gmail.com](mailto:basharulalammazu6@gmail.com)

Built with ❤️ using Python, Tkinter, and creativity.


