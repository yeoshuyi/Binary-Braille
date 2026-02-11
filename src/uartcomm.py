"""
UART controller for ESP-32 Communication
"""


import serial
import time


PORT = "/dev/cu.usbmodemC1BD4DEAE6881"
#PORT = "/dev/ttyACM0"


class ESP32UART:
    """Controller for UART"""

    def __init__(self, port=PORT):
        """Initialise serial port on ESP-32, /dev/ttyACM0 by default"""

        self.ser = serial.Serial(port, 115200, timeout=1)

    def send_braille(self, package):
        """Send Package to ESP32"""

        try:
            self.ser.write(package)
            return(200)
        except Exception as e:
            print(e)
            return(e)
        
    def check_send(self):
        """Check for Start Record Signal"""

        if self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            
            #OPCODE Decoding
            match line:
                case "SEND":
                    return "01"
                case "True":
                    return "10"
                case "False":
                    return "11"
    
        return "00"
    
    def flush_in(self):
        """Flush STDIN"""
        
        while self.ser.in_waiting > 0:
            flush = self.ser.readline().decode('utf-8', errors='ignore').strip()
        return None