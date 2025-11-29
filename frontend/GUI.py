#!/usr/bin/env python3
# gui_art_linkage.py  ——  无人时轮播艺术照片，有人靠近时切换到数据面板

import customtkinter as ctk
import requests
import threading
import os
import glob
import random
import time
from datetime import datetime
from PIL import Image, ImageTk
import RPi.GPIO as GPIO

# ========================= 配置 =========================
BASE_URL   = "http://127.0.0.1:8000"
PLANT_ID    = 1
PHOTO_DIR   = "/home/pi/smart-plant-advisor/backend/data/images"      # 原始照片
ART_DIR     = "/home/pi/smart-plant-advisor/art"                       # 艺术照片文件夹（自己建）
PIR_PIN     = 27                                                       # HC-SR312 OUT 接的 GPIO

# 创建艺术照片目录（不存在就建一个放几张默认图也行）
os.makedirs(ART_DIR, exist_ok=True)

class SmartFrame(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Plant Frame")
        self.attributes("-fullscreen", True)        # 全屏
        self.bind("<Double-Button-1>", lambda e: self.destroy())  # 双击退出

        self.person_near = False                    # 当前是否有人
        self.art_list = []
        self.art_index = 0

        self.init_pir()
        self.load_art_photos()
        self.create_widgets()

        # 默认先显示艺术照片
        self.show_art_mode()
        self.start_tasks()

    def init_pir(self):
        """轮询版红外感应，专治虚拟环境 Failed to add edge detection"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIR_PIN, GPIO.IN)
        
        # 启动独立线程轮询（永不阻塞主线程）
        threading.Thread(target=self._pir_poll_loop, daemon=True).start()
        print("红外感应已启动（轮询模式，虚拟环境完美兼容）")

    def _pir_poll_loop(self):
        """后台轮询线程，检测电平变化"""
        last_state = 0
        last_trigger_time = 0  # 防抖

        while True:
            try:
                current_state = GPIO.input(PIR_PIN)
                
                # 上升沿：没人 → 有人
                if current_state == 1 and last_state == 0:
                    now = time.time()
                    if now - last_trigger_time > 2:  # 至少隔 2 秒才触发
                        self.after(0, self.on_person_detected, None)
                        last_trigger_time = now
                
                # 下降沿：有人 → 没人
                elif current_state == 0 and last_state == 1:
                    # 延迟 5 秒确认人真的走了
                    time.sleep(5)
                    if GPIO.input(PIR_PIN) == 0:  # 再次确认还在低电平
                        self.after(0, self.on_person_left, None)
                
                last_state = current_state
                time.sleep(0.05)  # 50ms 轮询一次，超快响应
                
            except:
                time.sleep(0.1)  # 出异常也别崩
    def load_art_photos(self):
        exts = ["*.jpg", "*.jpeg", "*.png", "*.bmp"]
        self.art_list = []
        for ext in exts:
            self.art_list.extend(glob.glob(os.path.join(ART_DIR, ext)))
            self.art_list.extend(glob.glob(os.path.join(ART_DIR, ext.upper())))
        random.shuffle(self.art_list)
        if not self.art_list:
            # 没图就放个占位
            self.art_list = ["/home/pi/smart-plant-advisor/art/ac06e8aa938d25fcc1cf3d57f91b43a5.jpg"]

    def create_widgets(self):
        # 艺术模式：全屏照片
        self.art_label = ctk.CTkLabel(self, text="")
        self.art_label.place(relx=0.5, rely=0.5, anchor="center")

        # 数据模式：上下布局
        self.data_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # 顶部时间 + 昵称
        top = ctk.CTkFrame(self.data_frame)
        top.pack(fill="x", padx=30, pady=20)
        ctk.CTkLabel(top, text="我的小绿", font=("微软雅黑", 40, "bold")).pack(side="left")
        self.time_lbl = ctk.CTkLabel(top, text="", font=("微软雅黑", 28))
        self.time_lbl.pack(side="right")

        # 四宫格传感器
        sensor_grid = ctk.CTkFrame(self.data_frame)
        sensor_grid.pack(pady=20)
        self.sensor_vals = {}
        for i, (name, unit) in enumerate([("温度", "°C"), ("光照", "lux"), ("土壤湿度", ""), ("盆重", "g")]):
            f = ctk.CTkFrame(sensor_grid, corner_radius=20)
            f.grid(row=i//2, column=i%2, padx=25, pady=25)
            ctk.CTkLabel(f, text=name, font=("微软雅黑", 22)).pack()
            val = ctk.CTkLabel(f, text="--", font=("微软雅黑", 48, "bold"))
            val.pack(pady=10)
            bar = ctk.CTkProgressBar(f, height=20)
            bar.pack(fill="x", padx=30, pady=10)
            bar.set(0)
            self.sensor_vals[name] = (val, bar)

        # 建议
        self.advice_lbl = ctk.CTkLabel(self.data_frame, text="加载中...", font=("微软雅黑", 28), wraplength=900, justify="center")
        self.advice_lbl.pack(pady=30)

        # 最新实拍照片（小图）
        self.real_photo = ctk.CTkLabel(self.data_frame, text="暂无实拍")
        self.real_photo.pack(pady=20)

    # ========================= 模式切换 =========================
    def show_art_mode(self):
        if self.person_near: return
        self.data_frame.place_forget()
        self.show_next_art()

    def show_data_mode(self):
        self.person_near = True
        self.art_label.place_forget()
        self.data_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.update_data()

    def show_next_art(self):
        if not self.person_near and self.art_list:
            img = Image.open(self.art_list[self.art_index])
            img = img.resize((self.winfo_screenwidth(), self.winfo_screenheight()), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.art_label.configure(image=photo, text="")
            self.art_label.image = photo
            self.art_index = (self.art_index + 1) % len(self.art_list)
        self.after(8000, self.show_next_art)   # 无人时每8秒换一张

    # ========================= 红外回调 =========================
    def on_person_detected(self, channel):
        print("检测到有人靠近 → 切换到数据模式")
        self.show_data_mode()

    def on_person_left(self, channel):
        print("人离开 → 切换回艺术写真模式")
        self.person_near = False
        self.show_art_mode()

    # ========================= 数据更新 =========================
    def update_data(self):
        if not self.person_near: return
        try:
            r = requests.get(f"{BASE_URL}/analysis/{PLANT_ID}", timeout=8)
            if r.status_code == 200:
                j = r.json()
                d = j.get("sensor_summary_7d", {})

                self.sensor_vals["温度"][0].configure(text=f"{d.get('avg_temperature',0):.1f}")
                self.sensor_vals["光照"][0].configure(text=f"{int(d.get('avg_light',0))}")
                self.sensor_vals["土壤湿度"][0].configure(text=f"{int(d.get('avg_soil_moisture',0))}")
                self.sensor_vals["盆重"][0].configure(text=f"{int(d.get('avg_weight',0))}")

                # 进度条（示例阈值，可自行调）
                self.sensor_vals["温度"][1].set(max(0, min(1, (d.get('avg_temperature',20)-10)/25)))
                self.sensor_vals["光照"][1].set(max(0, min(1, d.get('avg_light',0)/1000)))
                self.sensor_vals["土壤湿度"][1].set(max(0, min(1, (255-d.get('avg_soil_moisture',128))/200)))

                self.advice_lbl.configure(text=j.get("advice", "状态良好，继续保持！"))

                # 最新实拍小图
                if j.get("latest_image"):
                    path = j["latest_image"].replace("/images/", PHOTO_DIR + os.path.basename(j["latest_image"]))
                    if os.path.exists(path):
                        img = Image.open(path).resize((400, 300), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        self.real_photo.configure(image=photo, text="")
                        self.real_photo.image = photo
        except Exception as e:
            print("数据刷新出错:", e)

        self.after(10000, self.update_data)

    # ========================= 时钟 =========================
    def clock(self):
        while True:
            t = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
            self.time_lbl.configure(text=t)
            threading.Event().wait(1)

    def start_tasks(self):
        threading.Thread(target=self.clock, daemon=True).start()
        self.after(8000, self.show_next_art)   # 启动艺术轮播
        self.after(5000, self.update_data)     # 启动数据刷新（有人时才生效）

if __name__ == "__main__":
    try:
        app = SmartFrame()
        app.mainloop()
    finally:
        GPIO.cleanup()
