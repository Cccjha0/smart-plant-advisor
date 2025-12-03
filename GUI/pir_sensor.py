# pir_sensor.py
import RPi.GPIO as GPIO
import time
import threading
from config import PIR_PIN

class PIRSensor:
    def __init__(self, on_detect=None, on_leave=None):
        self.on_detect = on_detect
        self.on_leave = on_leave
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIR_PIN, GPIO.IN)

    def start(self):
        threading.Thread(target=self._poll_loop, daemon=True).start()
        print("Infrared sensing has been activated.")

    def _poll_loop(self):
        last_state = 0
        last_trigger = 0

        while True:
            try:
                state = GPIO.input(PIR_PIN)

                if state == 1 and last_state == 0:  
                    now = time.time()
                    if now - last_trigger > 2:
                        if self.on_detect:
                            self.on_detect()
                        last_trigger = now

                elif state == 0 and last_state == 1:  
                    time.sleep(5)  
                    if GPIO.input(PIR_PIN) == 0 and self.on_leave:
                        self.on_leave()

                last_state = state
                time.sleep(0.05)
            except:
                time.sleep(0.1)
