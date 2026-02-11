"""
CircuitPython Main Code
"""


import board
import displayio
import digitalio
import fourwire
import busio
import busdisplay
import terminalio
import time
import sys
import select
try:
    import brailleparse
except:
    pass
from ulab import numpy as np
from adafruit_display_text import label
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.polygon import Polygon


#TFT Init Sequence
ST7735S_INIT = (
    b"\x01\x00"
    b"\x11\x80\x78"
    b"\x3A\x01\x05"
    b"\x20\x00"
    b"\x36\x01\xA0"
    b"\x29\x80\x64"
)


class Display:
    """Handles TFT Display Splashing"""

    def __init__(self):
        """Init SPI, GPIO"""
        displayio.release_displays()

        self.spi = busio.SPI(clock=board.GPIO12, MOSI=board.GPIO11)
        self.tft_cs = board.GPIO14
        self.tft_dc = board.GPIO10
        self.tft_rst = board.GPIO9

        reset_pin = digitalio.DigitalInOut(self.tft_rst)
        reset_pin.direction = digitalio.Direction.OUTPUT
        reset_pin.value = True
        time.sleep(0.1)
        reset_pin.value = False
        time.sleep(0.1)
        reset_pin.value = True
        time.sleep(0.1)
        reset_pin.deinit()

        self.splash = displayio.Group()
        self.color_bitmap = displayio.Bitmap(160, 128, 1)
        self.color_palette = displayio.Palette(1)
        self.color_palette[0] = 0xFFD1DC

        self.display_bus = fourwire.FourWire(
            self.spi,
            command=self.tft_dc,
            chip_select=self.tft_cs,
            reset=self.tft_rst
        )
        
        self.display = busdisplay.BusDisplay(
            self.display_bus, 
            ST7735S_INIT,
            width=160, 
            height=128
        )    

        self.display.root_group = self.splash
    
    def main_menu(self):
        """Simple Background Splash, Init Looped Splsah"""
        bg_sprite = displayio.TileGrid(
            self.color_bitmap,
            pixel_shader=self.color_palette,
            x=0, y=0
        )

        self.text_title = label.Label(terminalio.FONT, text="GRADE 1", color=0x800080, scale=1)
        self.text_title.x = 3
        self.text_title.y = 5

        self.splash.append(bg_sprite)
        self.splash.append(self.text_title)
        self.display_time_init()
        self.braille_text_init()

    def display_time_init(self):
        """Init Clock"""
        time_now = time.localtime()
        time_str = "{:02d}:{:02d}:{:02d}".format(
            time_now.tm_hour, 
            time_now.tm_min, 
            time_now.tm_sec)
        self.text_time = label.Label(terminalio.FONT, text=time_str, color=0x800080, scale=1)
        self.text_time.x = 110
        self.text_time.y = 5
        self.splash.append(self.text_time)

    def display_time(self):
        """Refresh Clock Time"""
        time_now = time.localtime()
        self.text_time.text = "{:02d}:{:02d}:{:02d}".format(
            time_now.tm_hour, 
            time_now.tm_min, 
            time_now.tm_sec
        )
    
    def mode_display(self, mode):
        """Refresh Mode Display"""
        if mode:
            self.text_title.text = "GRADE 2"
        else:
            self.text_title.text = "GRADE 1"

    def braille_text_init(self):
        """Init Braille Display"""
        self.braille_group = displayio.Group()
        self.splash.append(self.braille_group)

    def braille_text(self, data):
        """Refresh Braille Display"""
        
        if data == None:
            return None

        CHAR_WIDTH = 25
        CHAR_HEIGHT = 40
        DOT_SPACING = 8
        START_X = 15
        START_Y = 30

        while len(self.braille_group) > 0:
            self.braille_group.pop()
        
        for index, char_data in enumerate(data):
            row_idx = index // 6
            col_idx = index % 6
            base_x = START_X + (col_idx * CHAR_WIDTH)
            base_y = START_Y + (row_idx * CHAR_HEIGHT)

            for dot_idx, bit in enumerate(char_data):
                if bit:
                    dot_x = base_x + (dot_idx % 2) * DOT_SPACING
                    dot_y = base_y + (dot_idx // 2) * DOT_SPACING

                    dot = Circle(x0=dot_x, y0=dot_y, r=1, fill=0x800080, outline=None)
                    self.braille_group.append(dot)
                else:
                    dot_x = base_x + (dot_idx % 2) * DOT_SPACING
                    dot_y = base_y + (dot_idx // 2) * DOT_SPACING

                    dot = Circle(x0=dot_x, y0=dot_y, r=1, fill=0xFFFFFF, outline=None)
                    self.braille_group.append(dot)


class UARTRX:
    """Handles UART recieve from stdin"""

    def __init__(self):
        self.buffer = []
        self.buzzer = digitalio.DigitalInOut(board.GPIO15)
        self.buzzer.direction = digitalio.Direction.OUTPUT


    def get_uart(self):
        """Write to FIFO Buffer"""

        poll = select.select([sys.stdin], [], [], 0)

        if poll[0]:
            data = sys.stdin.readline().strip()
            if len(data) == 73:
                rows = 12
                cols = 6
                data_raw = data[1:]
                grid = [
                    [int(bit) for bit in data_raw[i * cols: (i + 1) * cols]]
                    for i in range(rows)
                ]
                if data[0] == "0":
                    self.buffer.append(grid)
                elif data[0] == "1":
                    self.buzzer_activation()
                    self.buffer.insert(0, grid)
    
    def next_fifo(self, read_en):
        """Read from FIFO Buffer with First Word Fall Through"""
        if len(self.buffer) > 0 and read_en:
            self.buffer.pop(0)

        if len(self.buffer) > 0:
            data = self.buffer[0]
        else:
            data = None
        return data
    
    def buzzer_activation(self):
        self.buzzer.value = True
        time.sleep(1)
        self.buzzer.value = False

class ButtonInput:
    """Handles Button Input and Debouncing"""

    def __init__(self):
        """Init GPIO"""
        self.mode = digitalio.DigitalInOut(board.GPIO4)
        self.next = digitalio.DigitalInOut(board.GPIO5)
        self.send = digitalio.DigitalInOut(board.GPIO7)
        self.mode.pull = digitalio.Pull.UP
        self.next.pull = digitalio.Pull.UP
        self.send.pull = digitalio.Pull.UP

        self.mode_sel = False
        self.mode_press = False

        self.next_pulse = False
        self.next_press = False

        self.send_pulse = False
        self.send_press = False

    def toggle_mode(self):
        """Handle Mode Selection for GRADE 1 / GRADE 2 Brille"""
        if not self.mode.value and not self.mode_press:
            self.mode_sel = not self.mode_sel
            print(self.mode_sel)
            time.sleep(0.1)
            self.mode_press = True
        
        if self.mode.value and self.mode_press:
            self.mode_press = False
    
    def check_next(self):
        """Handle Swipe Function"""

        self.next_pulse = False
        if not self.next.value and not self.next_press:
            self.next_pulse = True
            time.sleep(0.1)
            self.next_press = True
        
        if self.next.value and self.next_press:
            self.next_press = False
    
    def check_send(self):
        """Handle Push to Talk"""

        self.send_pulse = False
        if not self.send.value and not self.send_press:
            self.send_pulse = True
            time.sleep(0.1)
            self.send_press = True
            print("SEND")
        if self.send.value and self.send_press:
            self.send_press = False
    
    def check_mode(self):
        """Relay Mode"""
        return self.mode


last_time_update = time.monotonic()
def baudgen():
    """Generates Single Tick Every 500ms for Display Update"""
    global last_time_update
    current_time = time.monotonic()
    if current_time - last_time_update >= 0.5:
        last_time_update = time.monotonic()
        return True
    return False


if __name__ == "__main__":

    #Begin (Similar to void main())
    display = Display()
    receiver = UARTRX()
    buttons = ButtonInput()

    display.main_menu()

    old_data = None
    display.braille_text(
        [
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0]
        ]
    )
    
    #Loop (Similar to void loop())
    while True:
        data = receiver.get_uart()
        buttons.check_next()
        buttons.toggle_mode()
        buttons.check_send()

        mode = buttons.mode_sel
        next = buttons.next_pulse
        data = receiver.next_fifo(next)

        #Ticks every 500ms
        if baudgen():
            display.display_time()
            display.mode_display(mode)
            if data is not None and data != old_data:
                display.braille_text(data)
                old_data = data
