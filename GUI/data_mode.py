# data_mode.py

import customtkinter as ctk
import os
import cairosvg
from api_client import fetch_latest_summary
from PIL import Image
from io import BytesIO

class DataMode:
    def __init__(self, master):
        self.master = master
        self.frame = ctk.CTkFrame(master, fg_color="#f0f0f0")   
        self.build_ui()

    def build_ui(self):
        
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        
        top = ctk.CTkFrame(self.frame, fg_color="transparent")
        top.pack(fill="x", pady=(4, 0), padx=6)

        
        ctk.CTkLabel(
            top, text="My Plant",
            font=("微软雅黑", 46, "bold"),
            text_color="#2e8b57"
        ).pack(side="left", padx=10)

        
        self.time_lbl = ctk.CTkLabel(
            top,
            text="",
            font=("微软雅黑", 46),
            text_color="#444444"
        )
        self.time_lbl.pack(side="right", padx=10)   

        
        cards = ctk.CTkFrame(self.frame, fg_color="transparent")
        cards.pack(fill="x", pady=(8, 12), padx=8)

        icon_dir = os.path.join(os.path.dirname(__file__), "icons")

        def load_svg_to_ctkimage(svg_name, size=(32, 32)):
            svg_path = os.path.join(icon_dir, svg_name)
            if not os.path.exists(svg_path):
                return None
            
            png_data = cairosvg.svg2png(bytestring=open(svg_path, "rb").read(), output_width=size[0], output_height=size[1])
            img = Image.open(BytesIO(png_data))
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)

        
        icons = {
            "temperature": load_svg_to_ctkimage("temperature.svg",size=(48,48)),
            "light":       load_svg_to_ctkimage("light.svg",size=(48,48)),
            "soil_moisture": load_svg_to_ctkimage("soil.svg",size=(48,48)),
            "weight":      load_svg_to_ctkimage("weight.svg",size=(48,48)),
        }

        self.val_labels = {}
        items = [
            ("temperature", "温度"),
            ("light", "光照"),
            ("soil_moisture", "土壤"),
            ("weight", "重量")
        ]

        for key, name in items:
            box = ctk.CTkFrame(cards, corner_radius=16, fg_color="white", height=104)
            box.pack(side="left", expand=True, fill="x", padx=6)
            box.pack_propagate(False)

            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(pady=(20, 0))

            if icons[key]:
                ctk.CTkLabel(row, text="", image=icons[key]).pack(side="left", padx=(12, 8))

            val = ctk.CTkLabel(row, text="--", font=("微软雅黑", 46, "bold"), text_color="#222")
            val.pack(side="left")

            unit = {"temperature": "°C", "light": " lux", "soil_moisture": " %", "weight": " g"}[key]
            ctk.CTkLabel(row, text=unit, font=("微软雅黑", 32), text_color="#666").pack(side="left", padx=(0, 12))

            self.val_labels[name] = val

        
        self.advice = ctk.CTkLabel(
            self.frame,
            text="加载中…",
            font=("微软雅黑", 34, "bold"),      
            wraplength=self.master.winfo_screenwidth() - 50,
            justify="left",
            anchor="nw",
            text_color="#2e8b57",
            pady=15,
            padx=20
        )
        self.advice.pack(expand=True, fill="both")

    def update(self):
        data = fetch_latest_summary()

        
        self.val_labels["温度"].configure(text=f"{data['temperature']:.1f}")
        self.val_labels["光照"].configure(text=f"{int(data['light'])}")
        self.val_labels["土壤"].configure(text=f"{int(data['soil_moisture'])}")
        self.val_labels["重量"].configure(text=f"{int(data['weight'])}")

        
        raw = data["suggestions"].strip()
        lines = [line.strip() for line in raw.split("\n") if line.strip()]
        suggestion = "\n".join(lines) if lines else "In good condition, keep it up!"

        
        warning = any(kw in suggestion for kw in ["warting", "lighting", "Excessive moisture", "Too dry", "Too wet","Descend", "Rise up"])
        self.advice.configure(
            text=suggestion,
            text_color="#d4380d" if warning else "#2e8b57"
        )

    def show(self):
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.start_refresh()

    def hide(self):
        self.frame.place_forget()

    def start_refresh(self):
        self.update()
        self.master.after(10000, self.start_refresh)
