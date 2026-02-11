# Binary-Brialle

## Description
> _Submission for the Beyond Binary competition by the Binary Babes_
**Binary-Braille** is a specialized assistive wearable designed for individuals who are **both deaf and blind**, providing a tactile bridge to the auditory world. By leveraging microcontrollers and advanced audio processing, the device translates real-time speech and environmental sounds into haptic and Braille feedback.

Our primary mission is to restore independence and safety to the deaf-blind community. Traditional communication methods for this demographic often require a physical intermediary (like tactile signing); Binary-Braille automates this process, allowing users to "feel" conversations and remain aware of their surroundings through a refreshable Braille interface and targeted vibration alerts.

![alt text](PROTOTYPE.png)<br>
### Seamless Speech-to-Braille Translation
The wearable features a Push-to-Talk (PTT) system that captures spoken language and converts it into Grade 1 or Grade 2 Braille. Using a sophisticated multiplexing routine, the device ensures that transcribed text is stored in a FIFO buffer, allowing the user to read at their own pace by swiping through the content.

### Intelligent Passive Safety Monitoring
Safety is paramount. The device continuously monitors the environment using an optimized Machine Learning model (Random Forest + MFCC). It is trained to identify high-priority danger signals—such as car horns, sirens, dog barks, and explosions. When a threat is detected, the device triggers an immediate haptic interrupt, vibrating the wearable and overriding the current display to show the alert type in Braille.

## Technical Features

### Technical Specifications
Ammeter testing on prototype shows power draw of 80-120mW (Typical for microcontrollers)
> For benchmark, an Apple Watch draws 70mW

### Grade 1/2 Speech-to-Brialle Translation
Audio data is passively polled and multiplexed between the push-to-talk and passive alert system. In push-to-talk mode, the audio data is processed into words and translated to Grade 1/2 brialle depending on the mode selection. The brialle is then sent into the FIFO buffer.

### Alert Passive Monitoring System
In passive mode, audio data is continuously sampled through an optimized version of MFCC, and compared against a pre-trained ML dataset to detect and categorise dangerous sounds like car horns, dog barking and explosions.

Upon detection of an alert signal, the wearable enters an interrupt routine and asserts a vibration motor while also displaying the sound heard in brialle.

### Input FIFO Buffer with Bypass
The FIFO buffer stores push-to-talk brialles, with first-word-fall-through always pushing the first brialle code on the display. New brialle codes are written into the FIFO buffer, with read asserted whenever the user swipes on the screen (emulated by a DIP switch).

When an alert is sent, the FIFO is interrupted and the alert bypasses the FIFO, being pushed directly onto the display.

### Passive Microphone Calibration
The microphone automatically calibrates every 5 minutes through a passive millis timer.

## Setup and Installation
> ESP-32 is developed from a Unix (Ubuntu 24.04) environment. All bash commands shown may only work on Unix.
### Hardware Prerequisites
* ESP-32-S3 Development Board x1
* ST7735 1.44in TFT Screen (SPI) x1
* Hi-Fi MEMs Microphone x1
* Vibration Motor (3.3v) x1
* DIP Switch x3

### Software Prerequisites
>Adafruit CircuitPython 10.x libraries can be obtained from: https://circuitpython.org/libraries<br>

* CircuitPython 10.x
* adafruit_display_shapes
* adafruit_display_text
* adafruit_st7735

### Hardware Setup
1) Configure the connections based on PINOUT.md and PINOUT.png
![alt text](PINOUT.png)

### ESP-32 Flashing
1) Download CircuitPython 10.x binary file from circuitpython.org
2) Flashing the ESP-32 via Esptool
```bash
#Optional venv setup
python3 -m venv .venv
source ./.venv/bin/activate

#Esptool Operation
pip install esptool
ls /dev/ttyUSB* #Find serial port of ESP-32

#Hold Boot and press Reset on ESP-32
esptool.py --chip esp32 --port /dev/[PORT] --baud 460800 write_flash -z [.bin file]
```

### Sourcecode Installation
1) Clone the current repository and download the Grade 2 braille translator from https://github.com/ant0nisk/pybrl
```bash
git clone https://github.com/yeoshuyi/Binary-Brialle.git
git clone https://github.com/ant0nisk/pybrl.git
```
2) Clone files into the repository based on the directory:
```directory
├── code.py             #Main CircuitPython Code
├── brailleparse.py     #Handles Text-to-Braille
├── grade1.py           #Handles Grade 1 Translation
├── passive.py          #Handles Passive Alerts
├── braille             #Handles Grade 2 Translation
│   ├── ...
├── lib
│   ├── adafruit_display_shapes
│   ├── adafruit_display_text
│   └── adafruit_st7735.mpy
├── models              #Models for Passive Detection
│   ├── audio_scaler.joblib
│   └── rf_model_tuned.joblib
├── sd
│   └── placeholder.txt
└── settings.toml
```