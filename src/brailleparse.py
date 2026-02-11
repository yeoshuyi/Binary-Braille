"""
Program communicates with the ESP-32 via UART
Handles Text-to-Braille and Alert functions
"""

import sys
import os
import time
import adafruit_esp32_HW484
import sounddevice as sd
from passive import PassiveAlert
from adafruit_esp32_HW484 import esp_sr
from uartcomm import ESP32UART
from grade1 import grade1_translate

#Type 2 Braille Dictionary Converter by Antonis Katzourakis
#Credits: https://github.com/ant0nisk/pybrl
sys.path.append(os.path.join(os.path.dirname(__file__), 'braille'))
from braille.pybrl import translate as grade2_translate

class BrailleHandler:
    """Handles Braille Parsing"""

    def __init__(self):
        """Init Library"""

        self.uart = ESP32UART()
        self.mic = esp_sr.Microphone()
        self.mode = 0

    def encode_braille(self, s):
        """6-to-6 Brille Encoder for UART Communication"""

        return s[0] + s[3] + s[1] + s[4] + s[2] + s[5]

    def string_to_braille(self, text):
        """Translates a string to a braille representation"""

        output = ''
        if self.mode == 0:
            translated = grade1_translate(text)
            for char in translated:
                output += self.encode_braille(char)
        else:
            translated = grade2_translate(text)
            for word in translated:
                for character in word:
                    output += self.encode_braille(character)
                output += '000000'
        return output

    def run_pipeline(self):
        """Main Code for Speech to Brille"""

        with self.mic as source:

            if __debug__: print("Recording...")
            try:
                audio = adafruit_esp32_HW484.ping(source, 5)
                raw_text = adafruit_esp32_HW484.recall(audio)
                if __debug__: print(f"Raw text: {raw_text}")
                
                braille_bits = self.string_to_braille(raw_text)
                trimmed_bits = braille_bits[:72].ljust(72, '0')
                processed_str = (f"0{trimmed_bits}\n").encode('utf-8')
                if __debug__: print(f"UART Out: {processed_str}")
                self.uart.send_braille(processed_str)
            except esp_sr.UnknownValueError:
                if __debug__: print("Pipeline Error")
            except Exception as e:
                if __debug__: print(f"Pipeline Error: {e}")
            self.uart.flush_in()
            if __debug__: print("Done Recording...")
    
    def calibrate_mic(self):
        """Calibration"""

        if __debug__: print("Calibrating... please wait...")
        with self.mic as source:
            adafruit_esp32_HW484.cal(source)
        if __debug__: print("Done Calibrating!")

    def check_send(self):
        """Check UART Signal"""
        
        return self.uart.check_send()
    
    def send_alert(self, alert):
        alert_b = (f"1{self.string_to_braille(alert)[:72].ljust(72, '0')}\n").encode('utf-8')
        if __debug__: print(alert_b)
        self.uart.send_braille(alert_b)


if __name__ == "__main__":
    braille = BrailleHandler()
    passive = PassiveAlert()
    start_time = time.time()
    braille.calibrate_mic()
    calibrate = False
    while True:
        with sd.InputStream(callback=passive.audio_callback, channels=1, samplerate=passive.FS, blocksize=int(passive.FS * 2)):
            while True:
                opcode = braille.check_send()
                match opcode:
                    case "00":
                        if passive.trigger:
                            braille.send_alert(passive.alert)
                            passive.trigger = False
                        if time.time() - start_time > 300:
                            calibrate = True
                            break
                    case "01":
                        break
                    case "10":
                        if __debug__: print("SWAPPED TO GRADE 2")
                        braille.mode = 1
                    case "11":
                        if __debug__: print("SWAPPED TO GRADE 1")
                        braille.mode = 0
                time.sleep(0.01)
        if calibrate:
            braille.calibrate_mic()
            calibrate = False
            start_time = time.time()
            continue
        braille.run_pipeline()
        time.sleep(0.1)
