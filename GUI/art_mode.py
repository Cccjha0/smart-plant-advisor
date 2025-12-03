# art_mode.py
import customtkinter as ctk
from PIL import Image, ImageTk
import requests
import os
from config import BASE_URL, PLANT_ID

class ArtMode:
    def __init__(self, master, on_switch_to_data=None):
        self.master = master
        self.on_switch_to_data = on_switch_to_data

        
        self.label = ctk.CTkLabel(master, text="Loading…", font=("微软雅黑", 32))
        self.label.place(relx=0.5, rely=0.5, anchor="center")

        self.current_image_path = None

    def _fetch_latest_dream(self):
        try:
            url = f"{BASE_URL}/dreams/{PLANT_ID}"
            r = requests.get(url, timeout=8)
            if r.status_code != 200 or not r.json():
                return None

            latest = sorted(r.json(), key=lambda x: x["created_at"], reverse=True)[0]
            return latest["file_path"]
        except Exception as e:
            print(f"Failed to obtain: {e}")
            return None

    def _download_and_show(self, image_url):
        
        if not image_url:
            self.label.configure(text="No image", image=None)
            return

        
        cache_path = os.path.expanduser(f"~/.cache/smart_plant_latest_dream.jpg")

        
        if self.current_image_path == image_url:
            if os.path.exists(cache_path):
                self._show_image(cache_path)
                return

        
        try:
            r = requests.get(image_url, timeout=15)
            if r.status_code == 200:
                with open(cache_path, "wb") as f:
                    f.write(r.content)
                self.current_image_path = image_url
                self._show_image(cache_path)
                print(f"The latest pictures have been updated.")
        except Exception as e:
            print(f"Download failed: {e}")

    def _show_image(self, path):

        try:
            img = Image.open(path)
            img = img.resize(
                (self.master.winfo_screenwidth(), self.master.winfo_screenheight()),
                Image.Resampling.LANCZOS
            )
            photo = ImageTk.PhotoImage(img)
            self.label.configure(image=photo, text="")
            self.label.image = photo  
        except Exception as e:
            print(f"Failed to display the image: {e}")

    def show(self):
        
        latest_url = self._fetch_latest_dream()
        self._download_and_show(latest_url)

    def start_slideshow(self):
        
        self.show()  
        
        
        self.master.after(1800000, self._auto_refresh)

    def _auto_refresh(self):
        
        print("30min，checkout new image…")
        latest_url = self._fetch_latest_dream()
        if latest_url and latest_url != self.current_image_path:
            print("Find new image, updating…")
            self._download_and_show(latest_url)
        else:
            print("No new pictures yet.")
        
        
        self.master.after(1800000, self._auto_refresh)
    def stop(self):
        pass
