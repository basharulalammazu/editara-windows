__version__ = "1.0.0"

# Image Format Converter Application
import os
import tkinter as tk

from tkinter import filedialog, ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image, ImageTk
import threading
from tkinter.font import Font
import json
import requests
import webbrowser
from packaging import version
import sys

# Add moviepy for video conversion
try:
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'heic']
SUPPORTED_VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'mkv', 'webm']

# Enhanced Theme Colors with accent colors
LIGHT_THEME = {
    "bg": "#f5f5f5",
    "fg": "#333333",
    "accent": "#4CAF50",
    "accent_hover": "#3e8e41",
    "card_bg": "#ffffff",
    "entry_bg": "#ffffff",
    "border": "#dddddd",
    "hover": "#e6e6e6"
}

DARK_THEME = {
    "bg": "#2e2e2e",
    "fg": "#f0f0f0",
    "accent": "#4CAF50",
    "accent_hover": "#5dbd61",
    "card_bg": "#3e3e3e",
    "entry_bg": "#454545",
    "border": "#555555",
    "hover": "#505050"
}

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class ImageConverterApp:
    @staticmethod
    def save_theme(theme_name):
        with open("theme.json", "w") as f:
            json.dump({"theme": theme_name}, f)
    
    @staticmethod
    def load_theme():
        try:
            with open("theme.json", "r") as f:
                data = json.load(f)
                return data.get("theme", "dark")
        except Exception:
            return "dark"
        
    def __init__(self, root):
        self.root = root
        self.root.resizable(False, False)  # Disable maximize option
        self.root.title("Editara")
        try:
            icon_path = resource_path("appicon.ico")
            self.root.iconbitmap(icon_path)            
            if not os.path.exists(icon_path):
                raise FileNotFoundError(f"Icon file not found: {icon_path}")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set window icon: {e}")

        # Load theme
        theme_name = ImageConverterApp.load_theme()
        self.theme = DARK_THEME if theme_name == "dark" else LIGHT_THEME


        self.folder_var = tk.StringVar()
        self.format_var = tk.StringVar(value="webp")
        self.quality_var = tk.IntVar(value=90)
        self.is_converting = False
        self.file_count = 0
        self.file_types = []  # Store the type of files (image or video) uploaded

        # For mode selection
        self.mode_var = tk.StringVar(value="Image")

        # For resizing
        self.resize_var = tk.BooleanVar(value=False)
        self.resize_mode_var = tk.StringVar(value="both")
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()

        # Create custom fonts
        self.heading_font = Font(family="Segoe UI", size=12, weight="bold")
        self.normal_font = Font(family="Segoe UI", size=10)
        self.small_font = Font(family="Segoe UI", size=9)

        # Initialize the main window
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width - 300) // 2
        y = (screen_height - window_height - 250) // 2
        self.root.geometry(f"+{x}+{y}")

        self.setup_ui()
        self.apply_theme()

    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def center_window(self):
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"+{x}+{y}")

    def setup_ui(self):
        self.root.title("🖼️ Image Format Converter")
        self.root.geometry("600x600")  # Increased height to accommodate resize options
        self.root.minsize(550, 550)

        # Main content frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        # --- Mode selection radio buttons ---
        self.mode_radio_frame = tk.Frame(self.main_frame)
        self.mode_radio_frame.pack(fill=tk.X, pady=(0, 10))
        self.image_radio = tk.Radiobutton(
            self.mode_radio_frame, text="Image", variable=self.mode_var, value="Image",
            command=self.update_mode, font=self.normal_font
        )
        self.image_radio.pack(side=tk.LEFT, padx=(0, 10))
        self.video_radio = tk.Radiobutton(
            self.mode_radio_frame, text="Video", variable=self.mode_var, value="Video",
            command=self.update_mode, font=self.normal_font
        )
        self.video_radio.pack(side=tk.LEFT)

        # Header with app name and theme toggle
        self.header_frame = tk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 15))

        self.app_title = tk.Label(self.header_frame, text="Image Format Converter", font=self.heading_font)
        self.app_title.pack(side=tk.LEFT)

        # Info button for developer information
        self.info_button = tk.Button(
            self.header_frame, 
            text="ℹ️", 
            width=3, 
            command=self.show_about, 
            relief=tk.FLAT,
            font=self.normal_font
        )
        self.info_button.pack(side=tk.RIGHT, padx=(0, 5))

        # Check for updates button
        self.update_button = tk.Button(
            self.header_frame,
            text="⬆️",
            width=3,
            command=self.check_for_update,
            relief=tk.FLAT,
            font=self.normal_font
        )
        self.update_button.pack(side=tk.RIGHT, padx=(0, 5))

        # Theme toggle button
        self.theme_button = tk.Button(
            self.header_frame, 
            text="🌙", 
            width=3, 
            command=self.toggle_theme, 
            relief=tk.FLAT,
            font=self.normal_font
        )
        self.theme_button.pack(side=tk.RIGHT)

        # Source folder selection card
        self.source_card = tk.Frame(self.main_frame, relief=tk.RIDGE, bd=1)
        self.source_card.pack(fill=tk.X, pady=10)

        self.source_inner = tk.Frame(self.source_card)
        self.source_inner.pack(fill=tk.X, padx=15, pady=15)

        self.source_header = tk.Label(
            self.source_inner, 
            text="Source Folder", 
            anchor='w', 
            font=self.normal_font
        )
        self.source_header.pack(fill=tk.X)

        self.folder_frame = tk.Frame(self.source_inner)
        self.folder_frame.pack(fill=tk.X, pady=(10, 0))

        # Styled entry with drop indication
        self.entry = tk.Entry(
            self.folder_frame, 
            textvariable=self.folder_var, 
            font=self.normal_font,
            relief=tk.FLAT, 
            bd=1
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))
        self.entry.drop_target_register(DND_FILES)
        self.entry.dnd_bind('<<Drop>>', self.drop_folder)

        # Browse button
        self.browse_button = tk.Button(
            self.folder_frame, 
            text="Browse", 
            command=self.browse_folder, 
            relief=tk.FLAT,
            padx=12,
            font=self.normal_font
        )
        self.browse_button.pack(side=tk.RIGHT)

        # Drop instructions
        self.drop_label = tk.Label(
            self.source_inner, 
            text="✨ Drag and drop a folder or image/video files here", 
            font=self.small_font
        )
        self.drop_label.pack(anchor='w', pady=(5, 0))

        # Files info label
        self.files_label = tk.Label(
            self.source_inner, 
            text="No folder selected", 
            font=self.small_font,
            anchor='w'
        )
        self.files_label.pack(fill=tk.X, pady=(5, 0))

        # Settings card
        self.settings_card = tk.Frame(self.main_frame, relief=tk.RIDGE, bd=1)
        self.settings_card.pack(fill=tk.X, pady=10)

        self.settings_inner = tk.Frame(self.settings_card)
        self.settings_inner.pack(fill=tk.X, padx=15, pady=15)

        self.settings_header = tk.Label(
            self.settings_inner, 
            text="Conversion Settings", 
            anchor='w', 
            font=self.normal_font
        )
        self.settings_header.pack(fill=tk.X, pady=(0, 10))

        # Format settings row
        self.format_frame = tk.Frame(self.settings_inner)
        self.format_frame.pack(fill=tk.X, pady=5)

        self.format_label = tk.Label(self.format_frame, text="Output Format:", width=15, anchor='w')
        self.format_label.pack(side=tk.LEFT)

        self.format_dropdown = ttk.Combobox(
            self.format_frame, 
            textvariable=self.format_var,
            values=SUPPORTED_FORMATS, 
            width=15, 
            state='readonly'
        )
        self.format_dropdown.pack(side=tk.LEFT, padx=(0, 15))

        # Quality settings row (only for images)
        self.quality_frame = tk.Frame(self.settings_inner)
        self.quality_frame.pack(fill=tk.X, pady=5)

        self.quality_label = tk.Label(self.quality_frame, text="Image Quality:", width=15, anchor='w')
        self.quality_label.pack(side=tk.LEFT)

        self.quality_slider = ttk.Scale(
            self.quality_frame, 
            from_=10, 
            to=100, 
            orient=tk.HORIZONTAL, 
            variable=self.quality_var,
            command=self.update_quality_label
        )
        self.quality_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.quality_value_label = tk.Label(self.quality_frame, text="90%", width=5)
        self.quality_value_label.pack(side=tk.RIGHT)

        # Resize settings
        self.resize_frame = tk.Frame(self.settings_inner)
        self.resize_frame.pack(fill=tk.X, pady=5)

        self.resize_check = tk.Checkbutton(
            self.resize_frame, 
            text="Resize", 
            variable=self.resize_var,
            command=self.update_resize_options,
            font=self.normal_font
        )
        self.resize_check.pack(anchor='w')

        self.resize_options_frame = tk.Frame(self.resize_frame)
        self.resize_options_frame.pack(fill=tk.X, padx=(20, 0))

        # Resize mode radio buttons
        self.width_radio = tk.Radiobutton(
            self.resize_options_frame, 
            text="Specify Width", 
            variable=self.resize_mode_var, 
            value="width",
            font=self.normal_font
        )
        self.width_radio.pack(anchor='w')

        self.height_radio = tk.Radiobutton(
            self.resize_options_frame, 
            text="Specify Height", 
            variable=self.resize_mode_var, 
            value="height",
            font=self.normal_font
        )
        self.height_radio.pack(anchor='w')

        self.both_radio = tk.Radiobutton(
            self.resize_options_frame, 
            text="Specify Both", 
            variable=self.resize_mode_var, 
            value="both",
            font=self.normal_font
        )
        self.both_radio.pack(anchor='w')

        # Width and height entries
        self.width_label = tk.Label(self.resize_options_frame, text="Width:", font=self.normal_font)
        self.width_label.pack(side=tk.LEFT, padx=(0, 5))
        self.width_entry = tk.Entry(self.resize_options_frame, textvariable=self.width_var, width=10, font=self.normal_font)
        self.width_entry.pack(side=tk.LEFT, padx=(0, 10))

        self.height_label = tk.Label(self.resize_options_frame, text="Height:", font=self.normal_font)
        self.height_label.pack(side=tk.LEFT, padx=(0, 5))
        self.height_entry = tk.Entry(self.resize_options_frame, textvariable=self.height_var, width=10, font=self.normal_font)
        self.height_entry.pack(side=tk.LEFT)

        # Initially hide resize options
        self.resize_options_frame.pack_forget()

        # Action area
        self.action_frame = tk.Frame(self.main_frame)
        self.action_frame.pack(fill=tk.X, pady=10)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            self.action_frame, 
            orient=tk.HORIZONTAL, 
            length=100, 
            mode='determinate',
            variable=self.progress_var
        )
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # Convert button
        self.convert_button = tk.Button(
            self.action_frame, 
            text="🚀 Convert", 
            command=self.start_conversion, 
            relief=tk.FLAT,
            font=("Segoe UI", 13, "bold"),
            padx=10,
            pady=10,
            height=2,
            width=5,
            bg=self.theme["accent"],
            fg="#ffffff",
            activebackground=self.theme["accent_hover"],
            cursor="hand2"
        )
        self.convert_button.pack(fill=tk.X)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Label(
            self.main_frame, 
            textvariable=self.status_var, 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            font=self.small_font
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Trace resize mode to update entries
        self.resize_mode_var.trace('w', self.update_resize_entries)
        self.update_resize_entries()

    def update_resize_options(self):
        if self.resize_var.get():
            self.resize_options_frame.pack(fill=tk.X, padx=(20, 0))
        else:
            self.resize_options_frame.pack_forget()

    def update_resize_entries(self, *args):
        mode = self.resize_mode_var.get()
        if mode == "width":
            self.width_entry.config(state='normal')
            self.height_entry.config(state='readonly')
        elif mode == "height":
            self.width_entry.config(state='readonly')
            self.height_entry.config(state='normal')
        elif mode == "both":
            self.width_entry.config(state='normal')
            self.height_entry.config(state='normal')

    def update_mode(self, event=None):
        mode = self.mode_var.get()
        if mode == "Image":
            self.format_dropdown['values'] = SUPPORTED_FORMATS
            self.format_var.set(SUPPORTED_FORMATS[0])
            self.quality_frame.pack(fill=tk.X, pady=5)
            self.resize_check.config(text="Resize Image")
        else:
            self.format_dropdown['values'] = SUPPORTED_VIDEO_FORMATS
            self.format_var.set(SUPPORTED_VIDEO_FORMATS[0])
            self.quality_frame.forget()
            self.resize_check.config(text="Resize Video")
        # Revalidate selected files when mode changes
        if hasattr(self, 'selected_files') and self.selected_files:
            self.update_file_info(self.folder_var.get().split(';') if ';' in self.folder_var.get() else self.folder_var.get())

    def browse_folder(self):
        mode = self.mode_var.get()
        if mode == "Image":
            filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp *.heic"), ("All files", "*.*")]
            allowed_exts = SUPPORTED_FORMATS
        else:
            filetypes = [("Video files", "*.mp4 *.avi *.mov *.mkv *.webm"), ("All files", "*.*")]
            allowed_exts = SUPPORTED_VIDEO_FORMATS
        files = filedialog.askopenfilenames(title=f"Select {mode}s", filetypes=filetypes)
        if files:
            # Check file extensions
            for f in files:
                ext = os.path.splitext(f)[1].lower().lstrip('.')
                if ext not in allowed_exts:
                    messagebox.showwarning("Invalid File", f"{os.path.basename(f)} is not a supported {mode.lower()} file.")
                    return
            self.folder_var.set(";".join(files))
            self.file_types = [mode.lower()] * len(files)  # Store file types
            self.update_file_info(files)
        else:
            folder = filedialog.askdirectory()
            if folder:
                self.folder_var.set(folder)
                self.update_file_info(folder)

    def drop_folder(self, event):
        mode = self.mode_var.get()
        allowed_exts = SUPPORTED_FORMATS if mode == "Image" else SUPPORTED_VIDEO_FORMATS
        paths = self.root.tk.splitlist(event.data)
        valid_paths = []
        for path in paths:
            path = path.strip("{").strip("}")
            if os.path.isdir(path):
                valid_paths.append(path)
            elif os.path.isfile(path):
                ext = os.path.splitext(path)[1].lower().lstrip('.')
                if ext in allowed_exts:
                    valid_paths.append(path)
                else:
                    messagebox.showwarning("Invalid File", f"{os.path.basename(path)} is not a supported {mode.lower()} file.")
                    return
        if valid_paths:
            self.folder_var.set(";".join(valid_paths))
            self.file_types = [mode.lower()] * len(valid_paths)  # Store file types
            self.update_file_info(valid_paths)
        else:
            messagebox.showwarning("Invalid Drop", f"Please drop valid {mode.lower()} files or folders.")

    def update_file_info(self, paths):
        mode = self.mode_var.get()
        formats = SUPPORTED_FORMATS if mode == "Image" else SUPPORTED_VIDEO_FORMATS
        files = []
        file_types = []
        if isinstance(paths, str):
            if os.path.isdir(paths):
                for filename in os.listdir(paths):
                    file_path = os.path.join(paths, filename)
                    if os.path.isfile(file_path):
                        ext = os.path.splitext(filename)[1].lower()[1:]
                        if ext in formats:
                            files.append(file_path)
                            file_types.append(mode.lower())
            elif os.path.isfile(paths):
                ext = os.path.splitext(paths)[1].lower()[1:]
                if ext in formats:
                    files.append(paths)
                    file_types.append(mode.lower())
        else:
            for path in paths:
                if os.path.isdir(path):
                    for filename in os.listdir(path):
                        file_path = os.path.join(path, filename)
                        if os.path.isfile(file_path):
                            ext = os.path.splitext(filename)[1].lower()[1:]
                            if ext in formats:
                                files.append(file_path)
                                file_types.append(mode.lower())
                elif os.path.isfile(path):
                    ext = os.path.splitext(path)[1].lower()[1:]
                    if ext in formats:
                        files.append(path)
                        file_types.append(mode.lower())
        self.file_count = len(files)
        self.file_types = file_types  # Update stored file types
        if self.file_count > 0:
            self.files_label.config(text=f"Found {self.file_count} convertible {mode.lower()}{'s' if self.file_count != 1 else ''}")
            self.status_var.set(f"Ready to convert {self.file_count} {mode.lower()}{'s' if self.file_count != 1 else ''}")
        else:
            self.files_label.config(text=f"No convertible {mode.lower()}s found")
            self.status_var.set(f"No {mode.lower()}s to convert")
        self.selected_files = files

    def update_quality_label(self, *args):
        self.quality_value_label.config(text=f"{self.quality_var.get():.0f}%")

    def toggle_theme(self):
        if self.theme == DARK_THEME:
            self.theme = LIGHT_THEME
            ImageConverterApp.save_theme("light")
        else:
            self.theme = DARK_THEME
            ImageConverterApp.save_theme("dark")
        self.apply_theme()

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About Developer")
        about_window.geometry("320x220")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        th = self.theme
        about_window.configure(bg=th["bg"])
        about_window.withdraw()
        about_window.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - about_window.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - about_window.winfo_height()) // 2
        about_window.geometry(f"+{x}+{y}")
        about_window.deiconify()
        content_frame = tk.Frame(about_window, bg=th["bg"], padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        title_frame = tk.Frame(content_frame, bg=th["bg"])
        title_frame.pack(fill=tk.X, pady=(0, 15))
        title_label = tk.Label(
            title_frame, 
            text="🧑‍💻 Developer Information", 
            font=self.heading_font,
            bg=th["bg"],
            fg=th["fg"]
        )
        title_label.pack()
        info_frame = tk.Frame(content_frame, bg=th["bg"])
        info_frame.pack(fill=tk.BOTH, expand=True)
        name_label = tk.Label(info_frame, text="Name:", width=10, anchor='e', bg=th["bg"], fg=th["fg"])
        name_label.grid(row=0, column=0, sticky='e', pady=3)
        name_value = tk.Label(info_frame, text="Basharul - Alam - Mazu", anchor='w', bg=th["bg"], fg=th["fg"])
        name_value.grid(row=0, column=1, sticky='w', pady=3)
        github_label = tk.Label(info_frame, text="GitHub:", width=10, anchor='e', bg=th["bg"], fg=th["fg"])
        github_label.grid(row=1, column=0, sticky='e', pady=3)
        github_value = tk.Label(
            info_frame,
            text="basharulalammazu",
            anchor='w',
            bg=th["bg"],
            fg=th["accent"],
            cursor="hand2"
        )
        github_value.grid(row=1, column=1, sticky='w', pady=3)
        github_value.bind("<Button-1>", lambda e: os.startfile("https://github.com/basharulalammazu"))
        github_value.grid(row=1, column=1, sticky='w', pady=3)
        web_label = tk.Label(info_frame, text="Website:", width=10, anchor='e', bg=th["bg"], fg=th["fg"])
        web_label.grid(row=2, column=0, sticky='e', pady=3)
        web_value = tk.Label(info_frame, text="basharulalammazu.github.io", anchor='w', 
                            bg=th["bg"], fg=th["accent"], cursor="hand2")
        web_value.grid(row=2, column=1, sticky='w', pady=3)
        web_value.bind("<Button-1>", lambda e: os.startfile("https://basharulalammazu.github.io"))
        email_label = tk.Label(info_frame, text="Email:", width=10, anchor='e', bg=th["bg"], fg=th["fg"])
        email_label.grid(row=3, column=0, sticky='e', pady=3)
        email_value = tk.Label(info_frame, text="basharulalammazu6@gmail.com", anchor='w', 
                            bg=th["bg"], fg=th["accent"], cursor="hand2")
        email_value.grid(row=3, column=1, sticky='w', pady=3)
        email_value.bind("<Button-1>", lambda e: os.startfile("mailto:basharulalammazu6@gmail.com"))
        close_button = tk.Button(
            content_frame, 
            text="Close", 
            command=about_window.destroy,
            bg=th["accent"],
            fg="#ffffff",
            activebackground=th["accent_hover"],
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=20,
            font=self.normal_font
        )
        close_button.pack(pady=(15, 0))
        self.root.wait_window(about_window)

    def apply_theme(self):
        th = self.theme
        self.root.configure(bg=th["bg"])
        self.main_frame.configure(bg=th["bg"])
        if self.theme == DARK_THEME:
            self.theme_button.configure(text="🌙")
        else:
            self.theme_button.configure(text="☀️")
        for frame in [
            self.main_frame, self.source_card, self.source_inner, self.folder_frame, 
            self.settings_card, self.settings_inner, self.format_frame, self.quality_frame, 
            self.resize_frame, self.resize_options_frame, self.action_frame
        ]:
            frame.configure(bg=th["bg"])
        for label in [
            self.app_title, self.source_header, self.drop_label, self.files_label, 
            self.settings_header, self.format_label, self.quality_label, self.quality_value_label,
            self.status_bar, self.width_label, self.height_label
        ]:
            label.configure(bg=th["bg"], fg=th["fg"])
        for card in [self.source_card, self.settings_card]:
            card.configure(bg=th["card_bg"], highlightbackground=th["border"])
        self.entry.configure(
            bg=th["entry_bg"], 
            fg=th["fg"], 
            insertbackground=th["fg"],
            highlightbackground=th["border"]
        )
        button_config = {
            'bg': th["accent"], 
            'fg': '#ffffff', 
            'activebackground': th["accent_hover"],
            'activeforeground': '#ffffff'
        }
        self.browse_button.configure(**button_config)
        self.convert_button.configure(**button_config)
        self.theme_button.configure(**button_config)
        self.info_button.configure(**button_config)
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TCombobox", 
                        fieldbackground=th["entry_bg"],
                        background=th["bg"],
                        foreground=th["fg"])
        style.configure("TProgressbar", 
                        background=th["accent"],
                        troughcolor=th["entry_bg"])
        style.configure("Horizontal.TScale",
                        background=th["bg"],
                        troughcolor=th["entry_bg"])

    def show_splash(root, logo_path="logo.png", duration=2000):
        splash = tk.Toplevel(root)
        splash.overrideredirect(True)
        splash.configure(bg="#ffffff")
        try:
            pil_img = Image.open(logo_path).resize((50, 50), Image.LANCZOS)
            img = ImageTk.PhotoImage(pil_img)
            label = tk.Label(splash, image=img, bg="#ffffff")
            label.image = img  # Keep a reference!
            label.pack(padx=20, pady=20)
        except Exception as e:
            label = tk.Label(splash, text="Loading...", bg="#ffffff", font=("Segoe UI", 16))
            label.pack(padx=20, pady=20)

        # Center splash
        splash.update_idletasks()
        w, h = splash.winfo_width(), splash.winfo_height()
        sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
        x, y = (sw - w) // 2, (sh - h) // 2
        splash.geometry(f"+{x}+{y}")

        # Hide main window during splash
        root.withdraw()
        # After duration, destroy splash and show main window
        root.after(duration, lambda: (splash.destroy(), root.deiconify()))

    def start_conversion(self):
        if self.is_converting:
            return
        mode = self.mode_var.get()
        fmt = self.format_var.get().lower()
        quality = self.quality_var.get()
        files = getattr(self, "selected_files", None)
        if not files or len(files) == 0:
            messagebox.showinfo("Info", f"No {mode.lower()}s to convert in the selected files/folder.")
            return
        # Validate file types match the current mode
        for file_path, file_type in zip(self.selected_files, self.file_types):
            ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            if mode == "Image" and file_type == "video":
                messagebox.showerror("Error", "Images cannot be converted to video formats.")
                return
            if mode == "Video" and file_type == "image":
                messagebox.showerror("Error", "Videos cannot be converted to image formats.")
                return
        if mode == "Image" and fmt not in SUPPORTED_FORMATS:
            messagebox.showerror("Error", "Invalid image format selected.")
            return
        if mode == "Video":
            if not MOVIEPY_AVAILABLE:
                messagebox.showerror("Error", "moviepy is not installed. Please run:\npip install moviepy")
                return
            if fmt not in SUPPORTED_VIDEO_FORMATS:
                messagebox.showerror("Error", "Invalid video format selected.")
                return
        # Validate resize inputs if resize is enabled
        if self.resize_var.get():
            resize_mode = self.resize_mode_var.get()
            if resize_mode in ["width", "both"] and not self.width_var.get().isdigit():
                messagebox.showerror("Invalid Input", "Please enter a valid width.")
                return
            if resize_mode in ["height", "both"] and not self.height_var.get().isdigit():
                messagebox.showerror("Invalid Input", "Please enter a valid height.")
                return
        self.is_converting = True
        self.convert_button.config(state=tk.DISABLED)
        self.status_var.set(f"Converting {mode.lower()}s...")
        self.progress_var.set(0)
        if mode == "Image":
            thread = threading.Thread(target=self.run_conversion, args=(files, fmt, quality))
        else:
            thread = threading.Thread(target=self.run_video_conversion, args=(files, fmt))
        thread.daemon = True
        thread.start()

    def run_conversion(self, files, fmt, quality):
        try:
            converted, skipped = self.convert_images(files, fmt, quality)
            self.root.after(0, lambda: self.conversion_complete(converted, skipped))
        except Exception as e:
            self.root.after(0, lambda: self.conversion_error(str(e)))

    def run_video_conversion(self, files, fmt):
        try:
            converted, skipped = self.convert_videos(files, fmt)
            self.root.after(0, lambda: self.conversion_complete(converted, skipped))
        except Exception as e:
            self.root.after(0, lambda: self.conversion_error(str(e)))

    def conversion_complete(self, converted, skipped):
        self.is_converting = False
        self.convert_button.config(state=tk.NORMAL)
        self.status_var.set(f"Completed: {converted} converted, {skipped} skipped")
        messagebox.showinfo("Done", f"✅ Converted: {converted}\n⏭️ Skipped: {skipped}\n\nSaved to:\n{self.output_folder}")
        self.progress_var.set(100)

    def conversion_error(self, error):
        self.is_converting = False
        self.convert_button.config(state=tk.NORMAL)
        self.status_var.set("Error during conversion")
        messagebox.showerror("Conversion Error", f"An error occurred:\n{error}")

    def get_new_dimensions(self, original_width, original_height):
        if not self.resize_var.get():
            return None, None
        mode = self.resize_mode_var.get()
        try:
            if mode == "width":
                width = int(self.width_var.get())
                height = int(original_height * (width / original_width))
            elif mode == "height":
                height = int(self.height_var.get())
                width = int(original_width * (height / original_height))
            elif mode == "both":
                width = int(self.width_var.get())
                height = int(self.height_var.get())
            else:
                return None, None
            return width, height
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for dimensions.")
            return None, None

    def convert_images(self, files, target_format, quality):
        target_ext = '.' + target_format
        if os.path.isdir(files[0]):
            output_folder = os.path.join(files[0], f"Converted_to_{target_format}")
        else:
            output_folder = os.path.join(os.path.dirname(files[0]), f"Converted_to_{target_format}")
        os.makedirs(output_folder, exist_ok=True)
        self.output_folder = output_folder
        converted = skipped = 0
        total_files = len(files)
        for idx, file_path in enumerate(files):
            filename = os.path.basename(file_path)
            base_name, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext == target_ext:
                skipped += 1
                progress = ((idx + 1) / total_files) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                continue
            try:
                with Image.open(file_path) as img:
                    if self.resize_var.get():
                        original_width, original_height = img.size
                        new_width, new_height = self.get_new_dimensions(original_width, original_height)
                        if new_width and new_height:
                            img = img.resize((new_width, new_height), Image.LANCZOS)
                    if img.mode in ("RGBA", "P") and target_format.lower() in ['jpg', 'jpeg']:
                        img = img.convert("RGB")
                    target_path = os.path.join(output_folder, base_name + target_ext)
                    save_args = {}
                    if target_format.lower() in ['jpg', 'jpeg', 'webp']:
                        save_args['quality'] = int(quality)
                    elif target_format.lower() == 'png':
                        compression = min(9, max(0, int(9 - (quality / 10))))
                        save_args['compress_level'] = compression
                    img.save(target_path, target_format.upper(), **save_args)
                    converted += 1
            except Exception as e:
                print(f"Failed: {filename} – {e}")
            progress = ((idx + 1) / total_files) * 100
            self.root.after(0, lambda p=progress: self.progress_var.set(p))
        return converted, skipped

    def convert_videos(self, files, target_format):
        target_ext = '.' + target_format
        if os.path.isdir(files[0]):
            output_folder = os.path.join(files[0], f"Converted_to_{target_format}")
        else:
            output_folder = os.path.join(os.path.dirname(files[0]), f"Converted_to_{target_format}")
        os.makedirs(output_folder, exist_ok=True)
        self.output_folder = output_folder
        converted = skipped = 0
        total_files = len(files)
        for idx, file_path in enumerate(files):
            filename = os.path.basename(file_path)
            base_name, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext == target_ext:
                skipped += 1
                progress = ((idx + 1) / total_files) * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                continue
            try:
                clip = VideoFileClip(file_path)
                if self.resize_var.get():
                    original_width, original_height = clip.w, clip.h
                    new_width, new_height = self.get_new_dimensions(original_width, original_height)
                    if new_width and new_height:
                        clip = clip.resize((new_width, new_height))
                target_path = os.path.join(output_folder, base_name + target_ext)
                if target_format in ['mp4', 'mkv']:
                    codec = 'libx264'
                    audio_codec = 'aac'
                elif target_format == 'webm':
                    codec = 'libvpx'
                    audio_codec = 'libvorbis'
                else:
                    codec = None
                    audio_codec = None
                clip.write_videofile(target_path, codec=codec, audio_codec=audio_codec)
                clip.close()
                converted += 1
            except Exception as e:
                print(f"Failed: {filename} – {e}")
            progress = ((idx + 1) / total_files) * 100
            self.root.after(0, lambda p=progress: self.progress_var.set(p))
        return converted, skipped

    def check_for_update(self):
         # Check internet connection first
        try:
            requests.get("https://www.google.com", timeout=5)
        except requests.RequestException:
            messagebox.showerror("No Internet", "Please check your internet connection and try again.")
            return
        

        # Check the github server
        try:
            requests.get("https://www.github.com", timeout=5)
        except requests.RequestException:
            messagebox.showerror("Server Down", "Oops! It looks like the update server is currently down.\nPlease try again later.")
            return
        
        
        """Check GitHub for the newest (even pre-release) version and prompt to update."""
        repo = "basharulalammazu/editara-windows"
        api_url = f"https://api.github.com/repos/{repo}/releases"

        try:
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                releases = response.json()

                if not releases:
                    messagebox.showinfo("No Update", "No releases found.")
                    return

                 # Sort releases by version, pick latest (includes pre-releases)
                latest = sorted(
                    releases,
                    key=lambda r: version.parse(r["tag_name"].lstrip("v")),
                    reverse=True
                )[0]

                latest_version = latest["tag_name"].lstrip("v")
                latest_url = latest["html_url"]

                if version.parse(latest_version) > version.parse(__version__):
                    if messagebox.askyesno(
                        "Update Available",
                        f"A newer version ({latest_version}) is available.\n"
                        f"You are using version {__version__}.\n\n"
                        "Do you want to download the latest version?"
                    ):
                        webbrowser.open(latest_url)
                else:
                    messagebox.showinfo("Version Check", f"You are using the latest version ({__version__}).")
            else:
                messagebox.showerror("Update Error", "Could not connect to GitHub to check for updates.")
        except Exception as e:
            messagebox.showerror("Update Error", f"An error occurred while checking for updates:\n{e}")

# Run App
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    ImageConverterApp.show_splash(root, logo_path = resource_path("logo.png"), duration=2000)
    app = ImageConverterApp(root)
    root.mainloop()