# art_mode.py —— 只显示最新一张 AI 梦境图（极简终极版）
import customtkinter as ctk
from PIL import Image, ImageTk
import requests
import os
from config import BASE_URL, PLANT_ID

class ArtMode:
    def __init__(self, master, on_switch_to_data=None):
        self.master = master
        self.on_switch_to_data = on_switch_to_data

        # 全屏显示区域
        self.label = ctk.CTkLabel(master, text="正在唤醒梦境…", font=("微软雅黑", 32))
        self.label.place(relx=0.5, rely=0.5, anchor="center")

        self.current_image_path = None

    def _fetch_latest_dream(self):
        """获取最新的一张梦境图 URL"""
        try:
            url = f"{BASE_URL}/dreams/{PLANT_ID}"
            r = requests.get(url, timeout=8)
            if r.status_code != 200 or not r.json():
                return None
            # 按时间倒序取第一张
            latest = sorted(r.json(), key=lambda x: x["created_at"], reverse=True)[0]
            return latest["file_path"]
        except Exception as e:
            print(f"[梦境] 获取失败: {e}")
            return None

    def _download_and_show(self, image_url):
        """下载并显示图片（带本地缓存）"""
        if not image_url:
            self.label.configure(text="暂无梦境生成", image=None)
            return

        # 本地缓存路径（只缓存最新一张）
        cache_path = os.path.expanduser(f"~/.cache/smart_plant_latest_dream.jpg")

        # 如果和上次一样，不重复下载
        if self.current_image_path == image_url:
            if os.path.exists(cache_path):
                self._show_image(cache_path)
                return

        # 下载新图
        try:
            r = requests.get(image_url, timeout=15)
            if r.status_code == 200:
                with open(cache_path, "wb") as f:
                    f.write(r.content)
                self.current_image_path = image_url
                self._show_image(cache_path)
                print(f"[梦境] 已更新最新梦境图")
        except Exception as e:
            print(f"[梦境] 下载失败: {e}")

    def _show_image(self, path):
        """全屏显示图片"""
        try:
            img = Image.open(path)
            img = img.resize(
                (self.master.winfo_screenwidth(), self.master.winfo_screenheight()),
                Image.Resampling.LANCZOS
            )
            photo = ImageTk.PhotoImage(img)
            self.label.configure(image=photo, text="")
            self.label.image = photo  # 保持引用
        except Exception as e:
            print(f"显示图片失败: {e}")

    def show(self):
        """每次进入艺术模式都刷新最新一张"""
        latest_url = self._fetch_latest_dream()
        self._download_and_show(latest_url)

    def start_slideshow(self):
        """我们不需要轮播，但保留接口兼容"""
        self.show()  # 直接显示最新一张
        
        # 每30分钟（1800000毫秒）检查一次是否有新梦境
        self.master.after(1800000, self._auto_refresh)

    def _auto_refresh(self):
        """后台自动刷新逻辑（不打扰用户）"""
        print("[梦境] 30分钟到，检查新梦境…")
        latest_url = self._fetch_latest_dream()
        if latest_url and latest_url != self.current_image_path:
            print("[梦境] 发现新梦境！正在更新…")
            self._download_and_show(latest_url)
        else:
            print("[梦境] 暂无新梦境，继续显示当前图")
        
        # 再次预约下一次检查（形成无限循环）
        self.master.after(1800000, self._auto_refresh)
    def stop(self):
        pass
