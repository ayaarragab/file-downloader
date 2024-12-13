import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import validators

from core.download_task import DownloadTask
from managers.download_manager import DownloadManager
from utils.url_utils import determine_url_type


class DownloaderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced File Downloader")
        self.root.geometry("1000x700")

        self.downloader = None
        self.download_tasks = {}

        self.setup_ui()
        self.setup_styles()
        self.setup_menu()

    def setup_styles(self):
        """Configure custom styles for the application"""
        style = ttk.Style()
        style.configure('Header.TFrame', padding=10, relief='raised')
        style.configure('Download.TFrame', padding=5)
        style.configure('Status.TFrame', padding=3, relief='sunken')
        style.configure('Primary.TButton', padding=5)
        style.configure('Warning.TButton', padding=5, background='#FFA500')
        style.configure('Status.TLabel', padding=2)
        style.configure('URL.TLabel', wraplength=400)

    def setup_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Folder", command=self.select_folder)
        file_menu.add_command(label="Import URLs", command=self.import_urls)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        downloads_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Downloads", menu=downloads_menu)
        downloads_menu.add_command(label="Start All", command=self.start_downloads)
        downloads_menu.add_command(label="Pause All", command=self.pause_all)
        downloads_menu.add_command(label="Resume All", command=self.resume_all)
        downloads_menu.add_separator()
        downloads_menu.add_command(label="Clear Completed", command=self.clear_completed)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences", command=self.show_preferences)

    def setup_ui(self):
        """Initialize all UI components"""
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_container)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.url_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.url_var, width=80).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Add URL", command=self.add_url, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Start Downloads", command=self.start_downloads, style='Primary.TButton').pack(
            side=tk.LEFT)

        downloads_frame = ttk.Frame(main_container, style='Download.TFrame')
        downloads_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(downloads_frame)
        self.scrollable_frame = ttk.Frame(self.canvas)

        scrollbar = ttk.Scrollbar(downloads_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Frame(self.root, style='Status.TFrame')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status_bar, textvariable=self.status_var, style='Status.TLabel').pack(side=tk.LEFT, padx=5)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.downloader = DownloadManager(folder)
            self.status_var.set(f"Selected download folder: {folder}")

    def add_url(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return

        if not validators.url(url):
            messagebox.showerror("Error", "Invalid URL format")
            return

        if self.downloader:
            # Pass prompt_download_choice to determine_url_type
            content_type = determine_url_type(url, prompt_user=self.prompt_download_choice)
            self.downloader.queue_download(url, content_type)
            self.status_var.set(f"Added {url} as {content_type} to download queue")
            self.create_download_entry(url)
            self.url_var.set("")
        else:
            messagebox.showerror("Error", "Please select a download folder first")

    def prompt_download_choice(self, url):
        """Prompt the user to choose between downloading as video or audio."""
        # Create a StringVar to hold the user's choice
        choice = tk.StringVar(value="video")  # Default choice is "video"

        def confirm_choice():
            # Close the dialog when the user confirms their choice
            dialog.destroy()

        # Create the dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Download Choice")
        dialog.geometry("300x150")

        # Add instructions and radio buttons
        ttk.Label(dialog, text=f"Choose format for: {url}").pack(pady=10)
        ttk.Radiobutton(dialog, text="Video", variable=choice, value="video").pack(anchor=tk.W)
        ttk.Radiobutton(dialog, text="Audio", variable=choice, value="audio").pack(anchor=tk.W)

        # Add the confirm button
        ttk.Button(dialog, text="Confirm", command=confirm_choice).pack(pady=10)

        # Wait for the user to close the dialog
        self.root.wait_window(dialog)

        # Return the selected choice
        return choice.get()

    def create_download_entry(self, url):
        task_frame = ttk.Frame(self.scrollable_frame, style='Download.TFrame')
        task_frame.pack(fill=tk.X, pady=5)

        ttk.Label(task_frame, text=url, style='URL.TLabel').pack(side=tk.LEFT, padx=5)
        progress = ttk.Progressbar(task_frame, length=200, mode='determinate')
        progress.pack(side=tk.LEFT, padx=5)

        status_label = ttk.Label(task_frame, text="Pending")
        status_label.pack(side=tk.LEFT)

        self.download_tasks[url] = {'frame': task_frame, 'progress': progress, 'status': status_label}

    def start_downloads(self):
        if not self.downloader:
            messagebox.showerror("Error", "Please select a download folder first")
            return

        threading.Thread(target=self.downloader.start_downloads, args=(self.update_progress,self.prompt_download_choice), daemon=True).start()
        self.status_var.set("Downloads started")

    def update_progress(self, task: DownloadTask):
        if task.url in self.download_tasks:
            task_info = self.download_tasks[task.url]
            if task.total_size > 0:
                progress = (task.downloaded / task.total_size) * 100
                task_info['progress']['value'] = progress
            task_info['status']['text'] = task.status.title()

            if task.status == "failed":
                task_info['status']['text'] = f"Failed: {task.error}"
                self.status_var.set(f"Download failed: {task.url}")
            elif task.status == "completed":
                self.status_var.set(f"Download completed: {task.filename}")



    def import_urls(self):
        """Import URLs from a file"""
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return

        with open(file_path, "r") as file:
            for line in file:
                url = line.strip()
                if validators.url(url):
                    self.downloader.queue_download(url)
                    self.create_download_entry(url)
        self.status_var.set("Imported URLs from file")

    def pause_all(self):
        """Stub for pausing all downloads"""
        self.status_var.set("Pause all downloads feature not implemented")

    def resume_all(self):
        """Stub for resuming all downloads"""
        self.status_var.set("Resume all downloads feature not implemented")

    def clear_completed(self):
        """Clear completed downloads from the list"""
        for url, task_info in list(self.download_tasks.items()):
            if task_info['status']['text'] == "Completed":
                task_info['frame'].destroy()  # Remove from UI
                del self.download_tasks[url]
        self.status_var.set("Cleared completed downloads")

    def show_preferences(self):
        """Stub for showing preferences"""
        self.status_var.set("Preferences feature not implemented")

    def run(self):
        """Run the GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = DownloaderGUI()
    app.run()
