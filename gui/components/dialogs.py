import tkinter as tk
from tkinter import ttk

def prompt_download_choice(root, url):
    """
    Display a dialog for the user to choose the download format (Video or Audio).

    Args:
        root (tk.Tk): The main application window.
        url (str): The URL for which the download choice is being made.

    Returns:
        str: The chosen format ('video' or 'audio').
    """
    choice = tk.StringVar(value="video")  # Default choice is 'video'

    def confirm_choice():
        dialog.destroy()

    # Create a modal dialog window
    dialog = tk.Toplevel(root)
    dialog.title("Download Choice")
    dialog.geometry("450x250")
    dialog.resizable(False, False)

    # Center the dialog relative to the parent window
    dialog.transient(root)
    dialog.grab_set()

    dialog_frame = ttk.Frame(dialog, padding=10)
    dialog_frame.pack(fill=tk.BOTH, expand=True)

    label = ttk.Label(dialog_frame, text=f"Choose format for: {url}", font=('Helvetica', 12, 'bold'))
    label.pack(pady=(10, 20))

    radio_video = ttk.Radiobutton(dialog_frame, text="Video", variable=choice, value="video")
    radio_video.pack(anchor=tk.W, pady=5)

    radio_audio = ttk.Radiobutton(dialog_frame, text="Audio", variable=choice, value="audio")
    radio_audio.pack(anchor=tk.W, pady=5)

    confirm_button = ttk.Button(dialog_frame, text="Confirm", command=confirm_choice)
    confirm_button.pack(pady=(20, 10))

    # Wait for the user to close the dialog
    root.wait_window(dialog)

    return choice.get()
