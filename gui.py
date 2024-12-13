import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from core.download_task import DownloadTask
from managers.download_manager import DownloadManager
import validators

class DownloaderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SAOAS Downloader")
        self.root.geometry("1100x750")
        self.root.configure(bg='#E6E6FA')

        self.downloader = None
        self.download_tasks = {}

        self.style = ttk.Style()
        self.configure_styles()

        self.setup_ui()

    def configure_styles(self):
        """Configure custom styles with pastel colors"""
        # Use clam theme for better customization
        self.style.theme_use('clam')

        # Pastel color palette
        LIGHT_PINK = '#FFB6C1'
        LIGHT_BLUE = '#87CEFA'
        LIGHT_GREEN = '#90EE90'
        LAVENDER = '#E6E6FA'

        self.style.configure('Primary.TButton',
                             background=LIGHT_GREEN,  # Light Green
                             foreground='black',
                             font=('Helvetica', 10, 'bold'),
                             padding=8)
        self.style.map('Primary.TButton',
                       background=[('active', '#98FB98'),  # A bit brighter green when active
                                   ('pressed', '#7CFC00')])

        self.style.configure('Secondary.TButton',
                             background=LIGHT_BLUE,  # Light Blue
                             foreground='black',
                             font=('Helvetica', 10, 'bold'),
                             padding=8)
        self.style.map('Secondary.TButton',
                       background=[('active', '#B0E0E6'),  # Lighter blue when active
                                   ('pressed', '#ADD8E6')])

        self.style.configure('Danger.TButton',
                             background=LIGHT_PINK,  # Light Pink
                             foreground='black',
                             font=('Helvetica', 10, 'bold'),
                             padding=8)
        self.style.map('Danger.TButton',
                       background=[('active', '#FFC0CB'),  # Slightly brighter pink when active
                                   ('pressed', '#FFB6C1')])

        # Progress bar style with pastel green
        self.style.configure('Custom.Horizontal.TProgressbar',
                             background=LIGHT_GREEN,
                             troughcolor=LAVENDER)

        self.style.configure('Secondary.TRadiobutton',
                             background='#E6E6FA',  # Lavender background
                             foreground='black',
                             font=('Helvetica', 10))
        self.style.map('Secondary.TRadiobutton',
                       background=[('active', '#B0E0E6'),  # Slightly lighter blue when active
                                   ('pressed', '#ADD8E6')])

        self.style.configure('Main.TFrame', background=LAVENDER)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=15, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame,
                                text="SAOAS Downloader",
                                font=('Helvetica', 18, 'bold'),
                                foreground='#333333',
                                background='#E6E6FA')  # Lavender background
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

        # Right Side Buttons
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


        # Downloads Display

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

        content_type = self.prompt_download_choice(url)
        if not content_type:
            return

        self.downloader.queue_download(url, content_type)  # Queue the download
        self.create_download_entry(url, content_type)

        self.url_var.set('')

    def prompt_download_choice(self, url):
        """Prompt the user to choose a download format (Video or Audio)."""
        choice = tk.StringVar(value="video")  # Default choice is "video"

        def confirm_choice():
            dialog.destroy()

        dialog = tk.Toplevel(self.root)
        dialog.title("Download Choice")
        dialog.geometry("450x250")


        dialog_frame = ttk.Frame(dialog, style='Main.TFrame', padding=10)
        dialog_frame.pack(fill=tk.BOTH, expand=True)

        label = ttk.Label(dialog_frame, text=f"Choose format for: {url}", font=('Helvetica', 12, 'bold'))
        label.pack(pady=(10, 20))

        radio_video = ttk.Radiobutton(dialog_frame, text="Video", variable=choice, value="video",
                                      style='Secondary.TRadiobutton')
        radio_video.pack(anchor=tk.W, pady=5)

        radio_audio = ttk.Radiobutton(dialog_frame, text="Audio", variable=choice, value="audio",
                                      style='Secondary.TRadiobutton')
        radio_audio.pack(anchor=tk.W, pady=5)

        confirm_button = ttk.Button(dialog_frame, text="Confirm", command=confirm_choice, style='Primary.TButton')
        confirm_button.pack(pady=20)

        self.root.wait_window(dialog)
        return choice.get()

    def create_download_entry(self, url, content_type):
        frame = ttk.Frame(self.scrollable_frame, padding=5, relief="ridge")
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

    def stop_download(self, url, frame):
        """Stop a download, remove it from active downloads and destroy the frame"""
        task = self.downloader.active_downloads.get(url)
        if task:
            self.downloader.stop_download(url)
            task.status = "stopped"
            self.download_tasks.pop(url, None)
            frame.destroy()
            print(f"Download stopped for {url}")
        else:
            print(f"No active download found for {url}")

    def pause_download(self, url: str) -> None:
        """Pause a download by removing it from active downloads"""
        if url in self.downloader.active_downloads:
            task = self.downloader.active_downloads[url]
            task.status = "paused"
            self.downloader.queue.remove(url)  # Remove from the queue to pause it
            print(f"Download paused for {url}")
        else:
            print(f"No active download found for {url}")
    def start_downloads(self): # مش راضي يكول الفانكشن الي ف المانجر
        if not self.downloader:
            messagebox.showerror("Error", "Please select a download folder first")
            return

        threading.Thread(
            target=self.downloader.start_downloads,
            args=(self.update_progress,),
            daemon=True
        ).start()

    def update_progress(self, task: DownloadTask):
        """Update the progress bar and progress label in real-time"""
        if task.url in self.download_tasks:
            task_info = self.download_tasks[task.url]

            # Update progress bar
            if task.total_size > 0:
                progress = (task.downloaded / task.total_size) * 100
                task_info['progress']['value'] = progress
                # Update progress label  %
                task_info['progress_label']['text'] = progress
            if task.status == "completed":
                task_info['pause_btn'].pack_forget()
                task_info['stop_btn'].pack_forget()
                ttk.Label(task_info['frame'], text="✓", foreground="green").pack(side=tk.LEFT, padx=5)
            elif task.status == "failed":
                task_info['status']['text'] = f"Failed: {task.error}"

    def pause_all(self):
        """Pause all active downloads"""
        if not self.downloader:
            messagebox.showerror("Error", "No downloads to pause")
            return

        for url in list(self.download_tasks.keys()):
            task = self.downloader.active_downloads.get(url)
            if task and task.status == "downloading":
                self.downloader.pause_download(url)  # Pause download in DownloadManager

        messagebox.showinfo("Info", "All downloads paused.")

    def resume_all(self):
        if not self.downloader:
            messagebox.showerror("Error", "No downloads to resume")
            return

        for url in self.download_tasks.keys():
            task = self.downloader.active_downloads.get(url)
            if task and task.status == "paused":
                self.downloader.resume_download(url)  # Resume download in DownloadManager

        messagebox.showinfo("Info", "All downloads resumed.")

    def clear_completed(self):
        for url, task in list(self.download_tasks.items()):
            if task['progress']['value'] == 100:
                task['frame'].destroy()
                del self.download_tasks[url]

    def run(self):
        self.root.mainloop()


app = DownloaderGUI()
app.run()
