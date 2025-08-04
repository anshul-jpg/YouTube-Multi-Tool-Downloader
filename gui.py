import customtkinter as ctk
from downloader import Downloader, search_youtube
from tkinter import filedialog, messagebox
from PIL import Image
import requests
from io import BytesIO
import json
import os
import pyperclip
import logging
import subprocess
import sys
import threading
from queue import Queue
from functools import partial

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Multi-Tool Downloader")
        self.geometry("900x700")
        self.minsize(800, 650) # Increased min height for ETA
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.downloader = Downloader()
        self.download_path = ""
        self.video_info = None
        self.history_file = "download_history.json"
        self.download_history = self.load_history()
        self.thumbnail_cache = {}

        # --- RE-ENGINEERED: Master thread-safe queue for all GUI updates ---
        self.gui_queue = Queue()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_widgets()
        self.bind_all("<MouseWheel>", self.on_mouse_wheel)
        
        self.process_gui_queue()

    def on_closing(self):
        """Cleanly closes the application."""
        self.destroy()

    def process_gui_queue(self):
        """Safely process all updates for the GUI from the main thread."""
        try:
            while not self.gui_queue.empty():
                widget, method_name, args, kwargs = self.gui_queue.get_nowait()
                if widget and widget.winfo_exists():
                    method = getattr(widget, method_name)
                    method(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error processing GUI queue: {e}")
        
        self.after(100, self.process_gui_queue)

    def queue_gui_update(self, widget, method_name, *args, **kwargs):
        """Puts a widget update task into the thread-safe queue."""
        self.gui_queue.put((widget, method_name, args, kwargs))

    def create_widgets(self):
        self.tabs = ctk.CTkTabview(self, anchor="nw")
        self.tabs.pack(expand=True, fill="both", padx=10, pady=10)

        self.downloader_tab = self.tabs.add("Downloader")
        self.search_tab = self.tabs.add("Search")
        self.history_tab = self.tabs.add("History")

        self.create_downloader_tab()
        self.create_search_tab()
        self.create_history_tab()

        self.downloader_tab.bind("<Configure>", self.on_resize)

    def on_mouse_wheel(self, event):
        active_tab = self.tabs.get()
        if active_tab == "Search":
            self.search_results_frame._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif active_tab == "History":
            self.history_frame._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_downloader_tab(self):
        self.downloader_tab.grid_columnconfigure(0, weight=1)
        self.downloader_tab.grid_rowconfigure(2, weight=1)

        url_frame = ctk.CTkFrame(self.downloader_tab)
        url_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        url_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(url_frame, text="YouTube URL(s):").grid(row=0, column=0, padx=10, pady=10)
        self.url_entry = ctk.CTkTextbox(url_frame, height=4)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=(0,5), pady=10)

        paste_button = ctk.CTkButton(url_frame, text="Paste", width=60, command=self.paste_from_clipboard)
        paste_button.grid(row=0, column=2, padx=(0,5), pady=10)

        self.fetch_button = ctk.CTkButton(url_frame, text="Fetch", width=60, command=self.start_fetch_thread)
        self.fetch_button.grid(row=0, column=3, padx=(0,10), pady=10)

        details_frame = ctk.CTkFrame(self.downloader_tab)
        details_frame.grid(row=1, column=0, sticky="new", padx=10, pady=5)
        details_frame.grid_columnconfigure(1, weight=1)

        self.thumbnail_label = ctk.CTkLabel(details_frame, text="")
        self.thumbnail_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)

        self.title_label = ctk.CTkLabel(details_frame, text="Title: ", anchor="w", justify="left")
        self.title_label.grid(row=0, column=1, sticky="ew", padx=10, pady=(10, 0))

        self.author_label = ctk.CTkLabel(details_frame, text="Author: ", anchor="w", justify="left")
        self.author_label.grid(row=1, column=1, sticky="ew", padx=10, pady=(0, 10))

        main_frame = ctk.CTkFrame(self.downloader_tab)
        main_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)

        self.download_type = ctk.CTkSegmentedButton(main_frame, values=["Video", "Audio"], command=self.update_format_options)
        self.download_type.pack(pady=10)

        self.format_menu = ctk.CTkOptionMenu(main_frame, values=["mp4", "mkv", "webm"])
        self.format_menu.pack(pady=5)

        self.quality_menu = ctk.CTkOptionMenu(main_frame, values=["Best"])
        self.quality_menu.pack(pady=5)

        self.subtitle_checkbox = ctk.CTkCheckBox(main_frame, text="Download Subtitles")
        self.subtitle_checkbox.pack(pady=10)

        self.folder_button = ctk.CTkButton(main_frame, text="Select Folder", command=self.select_folder)
        self.folder_button.pack(pady=5)

        self.folder_label = ctk.CTkLabel(main_frame, text="No folder selected")
        self.folder_label.pack(pady=5)

        self.download_button = ctk.CTkButton(main_frame, text="Download", command=self.start_download_thread, state="disabled")
        self.download_button.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(main_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=10, fill="x", padx=20)

        self.status_label = ctk.CTkLabel(main_frame, text="", wraplength=700)
        self.status_label.pack(pady=5, padx=10, expand=True, fill="x")

    def create_search_tab(self):
        search_frame = ctk.CTkFrame(self.search_tab)
        search_frame.pack(pady=10, padx=10, fill="x")

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search YouTube...")
        self.search_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.start_search_thread())
        
        search_button = ctk.CTkButton(search_frame, text="Search", command=self.start_search_thread)
        search_button.pack(side="left", padx=5)
        
        self.search_results_frame = ctk.CTkScrollableFrame(self.search_tab, label_text="Search Results")
        self.search_results_frame.pack(expand=True, fill="both", padx=10, pady=10)

    def create_history_tab(self):
        self.history_frame = ctk.CTkScrollableFrame(self.history_tab, label_text="Download History")
        self.history_frame.pack(expand=True, fill="both", padx=10, pady=10)
        self.update_history_display()

    def on_resize(self, event):
        width = event.width - self.thumbnail_label.winfo_width() - 40 
        if width > 0:
            self.title_label.configure(wraplength=width)
            self.author_label.configure(wraplength=width)

    def start_fetch_thread(self):
        self.queue_gui_update(self.fetch_button, 'configure', state="disabled")
        self.queue_gui_update(self.title_label, 'configure', text="Title: Fetching...")
        threading.Thread(target=self.fetch_video_details, daemon=True).start()

    def start_search_thread(self):
        threading.Thread(target=self.perform_search, daemon=True).start()

    def start_download_thread(self):
        self.queue_gui_update(self.download_button, 'configure', state="disabled", text="Downloading...")
        self.queue_gui_update(self.progress_bar, 'set', 0)
        threading.Thread(target=self.download_video, daemon=True).start()

    def fetch_thumbnail_threaded(self, url, size, thumb_label):
        ctk_img = self.get_thumbnail_from_url(url, size)
        if ctk_img:
            self.queue_gui_update(thumb_label, 'configure', image=ctk_img, text="")

    def perform_search(self):
        query = self.search_entry.get()
        if not query: return

        self.queue_gui_update(self, '_clear_search_results')
        results = search_youtube(query)
        self.queue_gui_update(self, '_populate_search_results', results)

    def fetch_video_details(self):
        urls = self.url_entry.get("1.0", "end-1c").splitlines()
        if not urls or not urls[0]:
            self.queue_gui_update(messagebox, 'showerror', "Error", "Please enter a URL")
            self.queue_gui_update(self.fetch_button, 'configure', state="normal")
            return

        try:
            self.video_info = self.downloader.get_video_info(urls[0])
            thumb = self.get_thumbnail_from_url(self.video_info.get('thumbnail'), (320, 180))
            
            self.queue_gui_update(self.title_label, 'configure', text=f"Title: {self.video_info['title']}")
            self.queue_gui_update(self.author_label, 'configure', text=f"Author: {self.video_info['uploader']}")
            self.queue_gui_update(self.thumbnail_label, 'configure', image=thumb, text="")
            self.queue_gui_update(self, 'update_format_options', self.download_type.get())
            self.queue_gui_update(self, 'update_quality_options')
            self.queue_gui_update(self.download_button, 'configure', state="normal")
        except Exception as e:
            self.queue_gui_update(messagebox, 'showerror', "Error", f"Failed to fetch video details: {e}")
            logging.error(f"Fetch failed: {e}", exc_info=True)
        finally:
            self.queue_gui_update(self.fetch_button, 'configure', state="normal")

    def download_video(self):
        if not self.download_path:
            self.queue_gui_update(messagebox, 'showerror', "Error", "Please select a download folder.")
            self.queue_gui_update(self.download_button, 'configure', state="normal", text="Download")
            return

        urls = self.url_entry.get("1.0", "end-1c").splitlines()
        urls = [url.strip() for url in urls if url.strip()]

        for url in urls:
            try:
                info = self.downloader.get_video_info(url)
                final_path = self.downloader.download(url, self.download_path, self.quality_menu.get(),
                                                    self.format_menu.get(), self.subtitle_checkbox.get(),
                                                    self.progress_callback)
                if final_path:
                    self.queue_gui_update(self, 'add_to_history', info['title'], final_path)
                self.queue_gui_update(messagebox, 'showinfo', "Success", f"Download completed for: {info['title']}")
            except Exception as e:
                self.queue_gui_update(messagebox, 'showerror', "Error", f"Download failed for {url}: {e}")
                logging.error(f"Download failed for {url}: {e}", exc_info=True)
        
        self.queue_gui_update(self.download_button, 'configure', state="normal", text="Download")

    def _clear_search_results(self):
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.search_results_frame, text="Searching...").pack(pady=20)

    def _populate_search_results(self, results):
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        
        if not results:
            ctk.CTkLabel(self.search_results_frame, text="No results found.").pack()
            return

        for video in results:
            video_url = f"https://www.youtube.com/watch?v={video.get('id')}"
            
            result_card = ctk.CTkFrame(self.search_results_frame)
            result_card.pack(fill="x", pady=5, padx=5)
            result_card.grid_columnconfigure(1, weight=1)

            thumb_label = ctk.CTkLabel(result_card, text="Loading...")
            thumb_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="ns")

            threading.Thread(target=self.fetch_thumbnail_threaded, args=(video.get('thumbnail'), (120, 90), thumb_label), daemon=True).start()
            
            ctk.CTkLabel(result_card, text=video.get('title', 'No Title'), anchor="w", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="ew", padx=5)
            ctk.CTkLabel(result_card, text=video.get('channel', 'No Channel'), anchor="w", text_color="gray").grid(row=1, column=1, sticky="ew", padx=5)
            
            # --- FIX: Use functools.partial to correctly capture the URL ---
            select_command = partial(self.select_video_from_search, video_url)
            ctk.CTkButton(result_card, text="Select", width=60, command=select_command).grid(row=0, column=2, rowspan=2, padx=10)


    def select_video_from_search(self, url):
        self.tabs.set("Downloader")
        self.url_entry.delete("1.0", "end")
        self.url_entry.insert("1.0", url)
        self.start_fetch_thread()

    def update_history_display(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        for item in self.download_history:
            history_card = ctk.CTkFrame(self.history_frame)
            history_card.pack(fill="x", pady=5, padx=5)
            history_card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(history_card, text=item['title'], anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            btn_frame = ctk.CTkFrame(history_card)
            btn_frame.grid(row=0, column=1, padx=5, pady=5)
            ctk.CTkButton(btn_frame, text="Open", width=60, command=partial(self.open_path, item['path'])).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Folder", width=60, command=partial(self.open_path, os.path.dirname(item['path']))).pack(side="left", padx=5)

    def open_path(self, path):
        try:
            if sys.platform == "win32": os.startfile(path)
            elif sys.platform == "darwin": subprocess.Popen(["open", path])
            else: subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open path: {e}")

    def get_thumbnail_from_url(self, url, size):
        if not url: return None
        if url in self.thumbnail_cache: return self.thumbnail_cache[url]
        try:
            response = requests.get(url, timeout=5)
            img = Image.open(BytesIO(response.content))
            img.thumbnail(size)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            self.thumbnail_cache[url] = ctk_img
            return ctk_img
        except Exception: return None
            
    def update_format_options(self, value="Video"):
        if value == "Video":
            self.format_menu.configure(values=["mp4", "mkv", "webm"])
            self.format_menu.set("mp4")
            self.quality_menu.configure(state="normal")
        else:
            self.format_menu.configure(values=["mp3", "m4a", "wav"])
            self.format_menu.set("mp3")
            self.quality_menu.configure(state="disabled")

    def update_quality_options(self):
        if not self.video_info: return
        qualities = [f for f in self.video_info['formats'] if f.get('height') and f.get('vcodec') != 'none']
        quality_options = sorted(list(set([f"{f['height']}p" for f in qualities])), key=lambda x: int(x[:-1]))
        self.quality_menu.configure(values=quality_options or ["Best"])
        self.quality_menu.set(quality_options[-1] if quality_options else "Best")

    def paste_from_clipboard(self):
        self.url_entry.delete("1.0", "end")
        self.url_entry.insert("1.0", pyperclip.paste())

    def select_folder(self):
        self.download_path = filedialog.askdirectory()
        if self.download_path:
            self.folder_label.configure(text=self.download_path)

    def progress_callback(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if total_bytes > 0:
                percentage = d['downloaded_bytes'] / total_bytes
                text = f"{int(percentage*100)}% | {self.format_size(d.get('speed'))}/s | ETA: {self.format_eta(d.get('eta'))} | {self.format_size(d.get('downloaded_bytes'))}/{self.format_size(total_bytes)}"
                self.queue_gui_update(self.progress_bar, 'set', percentage)
                self.queue_gui_update(self.status_label, 'configure', text=text)
        elif d['status'] == 'finished':
            self.queue_gui_update(self.progress_bar, 'set', 1)
            self.queue_gui_update(self.status_label, 'configure', text="Download finished")
    
    def format_size(self, size):
        if not size: return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024: return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def format_eta(self, seconds):
        if seconds is None: return "N/A"
        h, r = divmod(seconds, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02}:{int(m):02}:{int(s):02}"
        
    def load_history(self):
        if not os.path.exists(self.history_file): return []
        if os.path.getsize(self.history_file) == 0: return []
        with open(self.history_file, 'r') as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []

    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.download_history, f, indent=4)

    def add_to_history(self, title, path):
        self.download_history.insert(0, {"title": title, "path": path})
        self.save_history()
        self.update_history_display()

def create_gui():
    app = YouTubeDownloaderApp()
    app.mainloop()