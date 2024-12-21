from gui.main_window import DownloaderGUI
import threading

if __name__ == "__main__":
    main_thread = threading.Thread(target=DownloaderGUI().run())
    main_thread.start()
