# data_mode.py  ——  专为 3.5 寸屏（480×320 / 800×480）深度优化版

import customtkinter as ctk
from api_client import fetch_latest_summary

class DataMode:
    def __init__(self, master):
        self.master = master
        self.frame = ctk.CTkFrame(master, fg_color="transparent")
        self.build_ui()

    def build_ui(self):
        # ============ 1. 顶部标题 + 时间（占屏幕高度约 1/6） ============
        top = ctk.CTkFrame(self.frame, height=55, fg_color="transparent")
        top.pack(fill="x", pady=(8, 0))
        top.pack_propagate(False)

        ctk.CTkLabel(
            top,
            text="我的小绿",
            font=("微软雅黑", 24, "bold"),      # 3.5寸屏字体别太大
            text_color="#2e8b57"
        ).pack(side="left", padx=15)

        self.time_lbl = ctk.CTkLabel(
            top,
            text="",
            font=("微软雅黑", 18),
            text_color="#555555"
        )
        self.time_lbl.pack(side="right", padx=15)

        # ============ 2. 一行四个超迷你状态块 ============
        cards = ctk.CTkFrame(self.frame, fg_color="transparent")
        cards.pack(fill="x", pady=(8, 10))

        self.val_labels = {}
        items = [("温度", "°C"), ("光照", "lux"), ("土壤", ""), ("重量", "g")]   # 文字改短一点
        for name, unit in items:
            box = ctk.CTkFrame(cards, width=105, height=62, corner_radius=12, fg_color="#f8f8f8")
            box.pack(side="left", padx=6)
            box.pack_propagate(False)

            ctk.CTkLabel(box, text=name, font=("微软雅黑", 13), text_color="#666").pack()
            val = ctk.CTkLabel(box, text="--", font=("微软雅黑", 22, "bold"), text_color="#333")
            val.pack(pady=(0, 2))
            ctk.CTkLabel(box, text=unit, font=("微软雅黑", 11), text_color="#888").pack()

            self.val_labels[name] = val

        # ============ 3. 超美观左对齐建议区（3.5寸屏最优解）============
        advice_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        advice_frame.pack(expand=True, fill="both", padx=20, pady=10)

        self.advice = ctk.CTkLabel(
            advice_frame,
            text="加载中…",
            font=("微软雅黑", 24, "bold"),       # 3.5寸屏最清晰字号
            wraplength=440,                      # 480宽屏安全值，绝不溢出
            justify="left",                      # 关键！左对齐
            anchor="w",                          # 左对齐 + 顶部对齐
            text_color="#2e8b57",                # 默认绿色
            pady=10
        )
        self.advice.pack(fill="both", expand=True)

    def update(self):
        data = fetch_latest_summary()
        
        self.val_labels["温度"].configure(text=f"{data['temperature']:.1f}")
        self.val_labels["光照"].configure(text=f"{int(data['light'])}")
        self.val_labels["土壤"].configure(text=f"{int(data['soil_moisture'])}")
        self.val_labels["重量"].configure(text=f"{int(data['weight'])}")

        # ============ 美观建议处理 ============
        raw = data["suggestions"].strip()
        lines = [line.strip() for line in raw.split("\n") if line.strip()]
        suggestion = "\n".join(lines)

        # 智能变色：有“浇水”“光照不足”“过湿”等关键词就变红
        warning_keywords = ["浇水", "光照", "过湿", "过干", "下降", "升高", "病虫害"]
        is_warning = any(kw in suggestion for kw in warning_keywords)

        self.advice.configure(
            text=suggestion or "状态良好，继续保持～",
            text_color="#d4380d" if is_warning else "#2e8b57"   # 红/绿智能切换
        )

    def show(self):
        self.frame.place(relx=0.5, rely=0.5, anchor="center")
        self.start_refresh()

    def hide(self):
        self.frame.place_forget()

    def start_refresh(self):
        self.update()
        self.master.after(10000, self.start_refresh)
