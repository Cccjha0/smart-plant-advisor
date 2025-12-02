# art_mode.py
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import glob
import random
from config import ART_DIR


class ArtMode:
    def __init__(self, master, on_switch_to_data=None):
        self.master = master
        self.on_switch_to_data = on_switch_to_data
        self._slideshow_running = False

        # 全屏显示图片
        self.label = ctk.CTkLabel(master, text="")
        self.label.place(relx=0.5, rely=0.5, anchor="center")

        # 右上角手动切换按钮（用于调试）
        self.switch_button = ctk.CTkButton(
            master,
            text="查看植物状态",
            width=180,
            height=50,
            corner_radius=25,
            font=("微软雅黑", 20, "bold"),
            fg_color="#1e1e1e",
            hover_color="#333333",
            command=self._manual_switch
        )
        self.switch_button.place(relx=1.0, rely=0.0, x=-30, y=30, anchor="ne")
        self.switch_button.place_forget()  # 默认隐藏

        self.photos = self._load_photos()
        self.index = 0

    def _load_photos(self):
        exts = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.JPG", "*.JPEG", "*.PNG", "*.BMP"]
        photos = []
        for ext in exts:
            photos.extend(glob.glob(str(ART_DIR / ext)))
        if not photos:
            placeholder = ART_DIR / "placeholder.jpg"
            if placeholder.exists():
                photos = [str(placeholder)]
        random.shuffle(photos)
        return photos

    def show(self):
        if not self.photos:
            self.label.configure(text="艺术照片文件夹为空")
            return
        try:
            img = Image.open(self.photos[self.index])
            img = img.resize(
                (self.master.winfo_screenwidth(), self.master.winfo_screenheight()),
                Image.Resampling.LANCZOS
            )
            photo = ImageTk.PhotoImage(img)
            self.label.configure(image=photo, text="")
            self.label.image = photo  # 保持引用，防止垃圾回收
            self.index = (self.index + 1) % len(self.photos)
        except Exception as e:
            print(f"加载艺术图失败: {e}")

    def start_slideshow(self):
        if not self._slideshow_running:
            self._slideshow_running = True
            self.switch_button.place(relx=1.0, rely=0.0, x=-30, y=30, anchor="ne")
            self._next()

    def stop(self):
        self._slideshow_running = False
        self.switch_button.place_forget()

    def _manual_switch(self):
        print("手动点击：切换到数据面板")
        if self.on_switch_to_data:
            self.on_switch_to_data()

    def _next(self):
        if not self._slideshow_running:
            return

        # 只有真正可见时才渲染，极大省 CPU
        if self.label.winfo_viewable():
            self.show()

        self.master.after(8000, self._next)
