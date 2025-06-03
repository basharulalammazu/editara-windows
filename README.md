# Editara - Image Format Converter for Windows

![Editara Logo](logo.png)

**Version:** 1.0.0 (Prerelease)

Editara is a modern, user-friendly image format converter for Windows. Easily convert images in bulk between popular formats (JPG, PNG, BMP, TIFF, WEBP, HEIC) with drag-and-drop, folder selection, and quality control.

---

## Features

- **Drag & Drop** folders or image files for instant selection
- **Bulk Conversion** to JPG, PNG, BMP, TIFF, WEBP, HEIC
- **Quality Slider** for lossy formats (JPG, WEBP, PNG)
- **Dark/Light Theme** toggle
- **Progress Bar** and status updates
- **Update Checker** (GitHub releases)
- **About Developer** dialog

---

## Installation

1. Download the latest release from [GitHub Releases](https://github.com/basharulalammazu/editara-windows/releases).
2. Extract the ZIP file.
3. Run `main.py` with Python 3.8+ installed.

### Requirements

- Python 3.8+
- [Pillow](https://pypi.org/project/Pillow/)
- [tkinterdnd2](https://pypi.org/project/tkinterdnd2/)
- requests

Install dependencies with:

```sh
pip install pillow tkinterdnd2 requests
```

---

## Usage

1. **Run the app:**  
   ```sh
   python main.py
   ```

2. **Select images:**  
   - Drag and drop a folder or image files, or  
   - Click "Browse" to select files or a folder.

3. **Choose output format** and adjust quality as needed.

4. **Click "Convert Images"** to start conversion.

5. Converted images will be saved in a new folder named `Converted_to_<format>`.

---

---

## Developer

- **Name:** Basharul - Alam - Mazu  
- **GitHub:** [basharulalammazu](https://github.com/basharulalammazu)  
- **Website:** [basharulalammazu.github.io](https://basharulalammazu.github.io)  
- **Email:** mazu.aiub@gmail.com

---

## License

[MIT License](LICENSE)

---

## Contributing

Pull requests and suggestions are welcome! Please open an issue first to discuss changes.
