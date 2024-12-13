import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .components.dialogs import prompt_download_choice
from .styles import configure_styles
from managers.download_manager import DownloadManager
import validators
import threading

class DownloaderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SAOAS Downloader")
        self.root.geometry("1100x750")
        self.root.configure(bg='#E6E6FA')

        self.downloader = None
        self.download_tasks = {}

        self.style = ttk.Style()
        configure_styles(self.style)

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=15, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame,
                                text="SAOAS Downloader",
                                font=('Helvetica', 18, 'bold'),
                                foreground='#333333',
                                background='#E6E6FA')
        title_label.pack(side=tk.TOP, pady=(0, 20))

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.url_var = tk.StringVar()
        url_label = ttk.Label(top_frame, text="URL:")
        url_label.pack(side=tk.LEFT, padx=5)

        url_entry = ttk.Entry(top_frame, textvariable=self.url_var, width=50)
        url_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        add_url_btn = ttk.Button(top_frame, text="Add URL",
                                 command=self.add_url,
                                 style='Primary.TButton')
        add_url_btn.pack(side=tk.LEFT, padx=5)

        start_downloads_btn = ttk.Button(top_frame, text="Start Downloads",
                                         command=self.start_downloads,
                                         style='Secondary.TButton')
        start_downloads_btn.pack(side=tk.LEFT, padx=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=5)

        select_folder_btn = ttk.Button(button_frame, text="Select Folder",
                                       command=self.select_folder,
                                       style='Primary.TButton')
        select_folder_btn.pack(fill=tk.X, pady=5)

        pause_all_btn = ttk.Button(button_frame, text="Pause All",
                                   command=self.pause_all,
                                   style='Secondary.TButton')
        pause_all_btn.pack(fill=tk.X, pady=5)

        resume_all_btn = ttk.Button(button_frame, text="Resume All",
                                    command=self.resume_all,
                                    style='Primary.TButton')
        resume_all_btn.pack(fill=tk.X, pady=5)

        clear_completed_btn = ttk.Button(button_frame, text="Clear Completed",
                                         command=self.clear_completed,
                                         style='Secondary.TButton')
        clear_completed_btn.pack(fill=tk.X, pady=5)

        exit_btn = ttk.Button(button_frame, text="Exit",
                              command=self.root.quit,
                              style='Danger.TButton')
        exit_btn.pack(fill=tk.X, pady=5)

        downloads_frame = ttk.Frame(main_frame)
        downloads_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(downloads_frame, bg='#f0f0f0')
        self.scrollable_frame = ttk.Frame(self.canvas)

        scrollbar = ttk.Scrollbar(downloads_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.downloader = DownloadManager(folder)

    def add_url(self):
        url = self.url_var.get().strip()
        if not validators.url(url):
            messagebox.showerror("Error", "Invalid URL")
            return

        if not self.downloader:
            messagebox.showerror("Error", "Please select a download folder first")
            return

        choice = prompt_download_choice(self.root, url)
        if not choice:
            return
        print(choice)
        self.downloader.queue_download(url, choice=choice)
        self.create_download_entry(self.scrollable_frame, url, choice)

        self.url_var.set('')

    def start_downloads(self):
        if not self.downloader:
            messagebox.showerror("Error", "Please select a download folder first")
            return

        threading.Thread(
            target=self.downloader.start_downloads,
            args=(self.update_progress,),
            daemon=True
        ).start()

    def update_progress(self, task):
        if task.url in self.download_tasks:
            task_info = self.download_tasks[task.url]
            if task.total_size > 0:
                progress = (task.downloaded / task.total_size) * 100
                task_info['progress']['value'] = progress
                task_info['progress_label']['text'] = f"{progress:.2f}%"
            if task.status == "completed":
                task_info['pause_btn'].pack_forget()
                task_info['stop_btn'].pack_forget()

    def pause_all(self):
        if not self.downloader:
            messagebox.showerror("Error", "No downloads to pause")
            return
        for url in list(self.download_tasks.keys()):
            self.downloader.pause_download(url)

    def resume_all(self):
        if not self.downloader:
            messagebox.showerror("Error", "No downloads to resume")
            return
        for url in self.download_tasks.keys():
            self.downloader.resume_download(url)

    def clear_completed(self):
        for url, task in list(self.download_tasks.items()):
            if task['progress']['value'] == 100:
                task['frame'].destroy()
                del self.download_tasks[url]

    def create_download_entry(self, frame, url, content_type):
        frame = ttk.Frame(frame, padding=5, relief="ridge")
        frame.pack(fill=tk.X, pady=5)

        ttk.Label(frame, text=url, width=50).pack(side=tk.LEFT, padx=5)
        progress = ttk.Progressbar(frame,
        length=200,
        mode="determinate",
        style='Custom.Horizontal.TProgressbar')
        progress.pack(side=tk.LEFT, padx=5)

        # Add a label to show the progress details
        progress_label = ttk.Label(frame, text="0%")
        progress_label.pack(side=tk.LEFT, padx=5)

        # Stop button now calls stop_download with the url
        stop_btn = ttk.Button(frame, text="Stop",
            command=lambda: self.downloader.stop_download(url),
            style='Danger.TButton')
        stop_btn.pack(side=tk.LEFT, padx=5)

        # Pause button
        pause_btn = ttk.Button(frame, text="Pause",
            command=lambda: self.pause_download(url),
            style='Secondary.TButton')
        pause_btn.pack(side=tk.LEFT, padx=5)

        self.download_tasks[url] = {
            'frame': frame,
            'progress': progress,
            'progress_label': progress_label,
            'stop_btn': stop_btn,
            'pause_btn': pause_btn,
            'content_type': content_type
        }

    def run(self):
        self.root.mainloop()
