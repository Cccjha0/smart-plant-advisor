import time
import lgpio

class HX711:
    def __init__(self, dout, pd_sck, gain=128):
        self.dout = dout
        self.pd_sck = pd_sck
        self.gain = gain

 
        self.chip = lgpio.gpiochip_open(0)

  
        lgpio.gpio_claim_input(self.chip, self.dout)
        lgpio.gpio_claim_output(self.chip, self.pd_sck)


        if gain == 128:
            self.GAIN = 1
        elif gain == 64:
            self.GAIN = 3
        elif gain == 32:
            self.GAIN = 2

        self.read()  

    def is_ready(self):
        return lgpio.gpio_read(self.chip, self.dout) == 0

    def read(self):
    
        while not self.is_ready():
            time.sleep(0.001)

        raw_data = 0
        for _ in range(24):
            lgpio.gpio_write(self.chip, self.pd_sck, 1)
            raw_data = (raw_data << 1) | lgpio.gpio_read(self.chip, self.dout)
            lgpio.gpio_write(self.chip, self.pd_sck, 0)

    
        for _ in range(self.GAIN):
            lgpio.gpio_write(self.chip, self.pd_sck, 1)
            lgpio.gpio_write(self.chip, self.pd_sck, 0)


        if raw_data & (1 << 23):
            raw_data -= (1 << 24)

        return raw_data

    def get_value(self, times=10):
        values = [self.read() for _ in range(times)]
        return sum(values) / len(values)

    def tare(self, times=15):
        offset = self.get_value(times)
        self.offset = offset
        return offset

    def get_weight(self, scale=1):
        return (self.get_value() - self.offset) / scale

    def cleanup(self):
        lgpio.gpiochip_close(self.chip)
