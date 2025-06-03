__version__ = "1.0.0 (Prerelease)"  # Update this with each release
import requests
import webbrowser
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from PIL import Image
import threading
from tkinter.font import Font

SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'heic']

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

class ImageConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.resizable(False, False)  # Disable maximize option
        self.root.title("Editara")

         # Add favicon (icon)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
            icon_img = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, icon_img)
        except Exception as e:
            print(f"Could not set window icon: {e}")

        self.theme = DARK_THEME  # Default theme
        self.folder_var = tk.StringVar()
        self.format_var = tk.StringVar(value="webp")
        self.quality_var = tk.IntVar(value=90)
        self.is_converting = False
        self.file_count = 0
        
        # Create custom fonts
        self.heading_font = Font(family="Segoe UI", size=12, weight="bold")
        self.normal_font = Font(family="Segoe UI", size=10)
        self.small_font = Font(family="Segoe UI", size=9)
        
        # Initialize the main window
        self.root.update_idletasks()
    
    # Get window and screen dimensions
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width - window_width-300) // 2
        y = (screen_height - window_height-250) // 2
        
        # Set the position
        self.root.geometry(f"+{x}+{y}")

        self.setup_ui()
        self.apply_theme()


    def center_window(self):
        """Center the main window on the screen"""
        # Update to ensure correct dimensions
        self.root.update_idletasks()
        
        # Get window and screen dimensions
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position coordinates
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set the position
        self.root.geometry(f"+{x}+{y}")

    def setup_ui(self):
        self.root.title("Editara")
        self.root.geometry("600x500")
        self.root.minsize(550, 450)
        
        # Main content frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Header with app name and theme toggle
        self.header_frame = tk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.app_title = tk.Label(self.header_frame, text="Editara", font=self.heading_font)
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
            text="✨ Drag and drop a folder here", 
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

         # Update drop instructions
        self.drop_label = tk.Label(
            self.source_inner, 
            text="✨ Drag and drop a folder or image files here", 
            font=self.small_font
        )
        self.drop_label.pack(anchor='w', pady=(5, 0))
        
        # Quality settings row
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
            text="🚀 Convert Images",  # Added emoji for cuteness
            command=self.start_conversion, 
            relief=tk.FLAT,
            font=("Segoe UI", 13, "bold"),  # Larger, bolder font
            padx=10,  # More horizontal padding
            pady=10,  # More vertical padding
            height=2,  # Button height
            width=5,  # Wider button
            bg=self.theme["accent"],
            fg="#ffffff",  # White text
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
    
    def check_for_update(self):
        """Check GitHub for a new release and prompt user to update."""
        repo = "basharulalammazu/editara-windows"
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                latest = response.json()
                latest_version = latest["tag_name"].lstrip("v")
                if latest_version > __version__:
                    if messagebox.askyesno(
                        "Update Available",
                        f"A new version ({latest_version}) is available!\n\nDo you want to open the download page?"
                    ):
                        webbrowser.open(latest["html_url"])
                else:
                    messagebox.showinfo("No Update", "You are using the latest version.")
            else:
                messagebox.showerror("Update Error", "Could not check for updates.")
        except Exception as e:
            messagebox.showerror("Update Error", f"Error checking for updates:\n{e}")
    def show_about(self):
        # Create a new top-level window
        about_window = tk.Toplevel(self.root)
        about_window.title("About Developer")
        about_window.geometry("320x220")
        about_window.resizable(False, False)
        
        # Make it modal (blocks interaction with the main window)
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Configure with current theme
        th = self.theme
        about_window.configure(bg=th["bg"])
        
        # Center the window on the parent
        about_window.withdraw()
        about_window.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - about_window.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - about_window.winfo_height()) // 2
        about_window.geometry(f"+{x}+{y}")
        about_window.deiconify()
        
        # Main content frame with padding
        content_frame = tk.Frame(about_window, bg=th["bg"], padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with icon
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
        
        # Developer info with key-value pairs
        info_frame = tk.Frame(content_frame, bg=th["bg"])
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        name_label = tk.Label(info_frame, text="Name:", width=10, anchor='e', bg=th["bg"], fg=th["fg"])
        name_label.grid(row=0, column=0, sticky='e', pady=3)
        name_value = tk.Label(info_frame, text="Basharul - Alam - Mazu", anchor='w', bg=th["bg"], fg=th["fg"])
        name_value.grid(row=0, column=1, sticky='w', pady=3)
        
        # GitHub
        github_label = tk.Label(info_frame, text="GitHub:", width=10, anchor='e', bg=th["bg"], fg=th["fg"])
        github_label.grid(row=1, column=0, sticky='e', pady=3)
        github_value = tk.Label(info_frame, text="basharulalammazu", anchor='w', bg=th["bg"], fg=th["fg"])
        github_value.grid(row=1, column=1, sticky='w', pady=3)
        
        # Website
        web_label = tk.Label(info_frame, text="Website:", width=10, anchor='e', bg=th["bg"], fg=th["fg"])
        web_label.grid(row=2, column=0, sticky='e', pady=3)
        web_value = tk.Label(info_frame, text="basharulalammazu.github.io", anchor='w', 
                            bg=th["bg"], fg=th["accent"], cursor="hand2")
        web_value.grid(row=2, column=1, sticky='w', pady=3)
        web_value.bind("<Button-1>", lambda e: os.startfile("https://basharulalammazu.github.io"))
        
        # Email
        email_label = tk.Label(info_frame, text="Email:", width=10, anchor='e', bg=th["bg"], fg=th["fg"])
        email_label.grid(row=3, column=0, sticky='e', pady=3)
        email_value = tk.Label(info_frame, text="mazu.aiub@gmail.com", anchor='w', 
                            bg=th["bg"], fg=th["accent"], cursor="hand2")
        email_value.grid(row=3, column=1, sticky='w', pady=3)
        email_value.bind("<Button-1>", lambda e: os.startfile("mailto:mazu.aiub@gmail.com"))
        
        # Close button at bottom
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
        
        # Wait for the window to close
        self.root.wait_window(about_window)

    def apply_theme(self):
        th = self.theme
        self.root.configure(bg=th["bg"])
        self.main_frame.configure(bg=th["bg"])
        
        # Update theme button icon
        if self.theme == DARK_THEME:
            self.theme_button.configure(text="🌙")
        else:
            self.theme_button.configure(text="☀️")
        
        # Configure all frames with theme
        for frame in [
            self.main_frame, self.source_card, self.source_inner, self.folder_frame, 
            self.settings_card, self.settings_inner, self.format_frame, self.quality_frame, self.action_frame
        ]:
            frame.configure(bg=th["bg"])
        
        # Configure all labels with theme
        for label in [
            self.app_title, self.source_header, self.drop_label, self.files_label, 
            self.settings_header, self.format_label, self.quality_label, self.quality_value_label,
            self.status_bar
        ]:
            label.configure(bg=th["bg"], fg=th["fg"])
        
        # Configure cards
        for card in [self.source_card, self.settings_card]:
            card.configure(bg=th["card_bg"], highlightbackground=th["border"])
        
        # Configure entry
        self.entry.configure(
            bg=th["entry_bg"], 
            fg=th["fg"], 
            insertbackground=th["fg"],
            highlightbackground=th["border"]
        )
        
        # Configure buttons
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

        # Configure ttk widgets
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

    def update_quality_label(self, *args):
        self.quality_value_label.config(text=f"{self.quality_var.get():.0f}%")

    def toggle_theme(self):
        self.theme = LIGHT_THEME if self.theme == DARK_THEME else DARK_THEME
        self.apply_theme()

    def update_quality_label(self, *args):
        self.quality_value_label.config(text=f"{self.quality_var.get():.0f}%")

    def browse_folder(self):
        # Allow user to select files or a folder
        filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp *.heic"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Select Images", filetypes=filetypes)
        if files:
            self.folder_var.set(";".join(files))
            self.update_file_info(files)
        else:
            folder = filedialog.askdirectory()
            if folder:
                self.folder_var.set(folder)
                self.update_file_info(folder)

    def drop_folder(self, event):
        # Accept both files and folders
        paths = self.root.tk.splitlist(event.data)
        valid_paths = []
        for path in paths:
            path = path.strip("{").strip("}")
            if os.path.isdir(path) or os.path.isfile(path):
                valid_paths.append(path)
        if valid_paths:
            self.folder_var.set(";".join(valid_paths))
            self.update_file_info(valid_paths)
        else:
            messagebox.showwarning("Invalid Drop", "Please drop valid files or folders.")

    def update_file_info(self, paths):
        # Accepts a list of files/folders or a single folder path
        files = []
        if isinstance(paths, str):
            # If it's a single folder path
            if os.path.isdir(paths):
                for filename in os.listdir(paths):
                    file_path = os.path.join(paths, filename)
                    if os.path.isfile(file_path):
                        ext = os.path.splitext(filename)[1].lower()[1:]
                        if ext in SUPPORTED_FORMATS:
                            files.append(file_path)
            elif os.path.isfile(paths):
                ext = os.path.splitext(paths)[1].lower()[1:]
                if ext in SUPPORTED_FORMATS:
                    files.append(paths)
        else:
            # It's a list of files/folders
            for path in paths:
                if os.path.isdir(path):
                    for filename in os.listdir(path):
                        file_path = os.path.join(path, filename)
                        if os.path.isfile(file_path):
                            ext = os.path.splitext(filename)[1].lower()[1:]
                            if ext in SUPPORTED_FORMATS:
                                files.append(file_path)
                elif os.path.isfile(path):
                    ext = os.path.splitext(path)[1].lower()[1:]
                    if ext in SUPPORTED_FORMATS:
                        files.append(path)
        self.file_count = len(files)
        if self.file_count > 0:
            self.files_label.config(text=f"Found {self.file_count} convertible image{'s' if self.file_count != 1 else ''}")
            self.status_var.set(f"Ready to convert {self.file_count} image{'s' if self.file_count != 1 else ''}")
        else:
            self.files_label.config(text="No convertible images found")
            self.status_var.set("No images to convert")
        self.selected_files = files

    def start_conversion(self):
        if self.is_converting:
            return

        fmt = self.format_var.get().lower()
        quality = self.quality_var.get()

        # Use self.selected_files if available
        files = getattr(self, "selected_files", None)
        if not files or len(files) == 0:
            messagebox.showinfo("Info", "No images to convert in the selected files/folder.")
            return

        if fmt not in SUPPORTED_FORMATS:
            messagebox.showerror("Error", "Invalid format selected.")
            return

        # Start conversion in a separate thread
        self.is_converting = True
        self.convert_button.config(state=tk.DISABLED)
        self.status_var.set("Converting images...")
        self.progress_var.set(0)

        thread = threading.Thread(target=self.run_conversion, args=(files, fmt, quality))
        thread.daemon = True
        thread.start()

    def run_conversion(self, files, fmt, quality):
        try:
            converted, skipped = self.convert_images(files, fmt, quality)
            self.root.after(0, lambda: self.conversion_complete(converted, skipped))
        except Exception as e:
            self.root.after(0, lambda: self.conversion_error(str(e)))


    def conversion_complete(self, converted, skipped):
        self.is_converting = False
        self.convert_button.config(state=tk.NORMAL)
        self.status_var.set(f"Completed: {converted} converted, {skipped} skipped")
        messagebox.showinfo("Done", f"✅ Converted: {converted}\n⏭️ Skipped: {skipped}\n\nSaved to:\n{self.output_folder}")
        self.progress_var.set(100)

    def convert_images(self, files, target_format, quality):
        target_ext = '.' + target_format
        # Use the directory of the first file or folder
        if os.path.isdir(files[0]):
            output_folder = os.path.join(files[0], f"Converted_to_{target_format}")
        else:
            output_folder = os.path.join(os.path.dirname(files[0]), f"Converted_to_{target_format}")
        os.makedirs(output_folder, exist_ok=True)


        self.output_folder = output_folder  # <-- Add this line

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

# Run App
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ImageConverterApp(root)
    root.mainloop()