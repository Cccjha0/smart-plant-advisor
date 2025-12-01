# main.py
import customtkinter as ctk
from datetime import datetime
import threading
from pir_sensor import PIRSensor
from art_mode import ArtMode
from data_mode import DataMode

class SmartPlantFrame(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Plant Frame")
        self.attributes("-fullscreen", True)
        self.bind("<Double-Button-1>", lambda e: self.destroy())

        self.art_mode = ArtMode(self,on_switch_to_data=self.show_data)
        self.data_mode = DataMode(self)

        self.sensor = PIRSensor(on_detect=self.show_data, on_leave=self.show_art)
        self.sensor.start()

        self.show_art()  # 默认艺术模式
        self.start_clock()

    def show_art(self):
        self.data_mode.hide()
        self.art_mode.start_slideshow()

    def show_data(self):
        self.data_mode.show()
        self.art_mode.stop()

    def start_clock(self):
        def update():
            t = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
            try:
                self.data_mode.time_lbl.configure(text=t)
            except:
                pass
            self.after(1000, update)
        update()

if __name__ == "__main__":
    try:
        app = SmartPlantFrame()
        app.mainloop()
    finally:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
