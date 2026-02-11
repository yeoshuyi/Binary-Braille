import numpy as np
import sounddevice as sd
import librosa
import joblib
import time
import models
import os


FS = 22050          
THRESHOLD = 0.05
COOLDOWN_SEC = 2.0
BLOCK_SIZE = 1024
TARGET_CLASSES = ['siren', 'gun_shot', 'car_horn', 'dog_bark','drilling']
CONFIDENCE_THRESHOLD = 20.0 
BASE_PATH = os.path.dirname(os.path.abspath(__file__))


class PassiveAlert:
    """Class handles passive monitoring of dangerous sounds"""

    def __init__(self):
        """Initialise ML Model"""

        self.model = joblib.load(os.path.join(BASE_PATH, 'models', 'rf_model_tuned.joblib'))
        self.scaler = joblib.load(os.path.join(BASE_PATH, 'models', 'audio_scaler.joblib'))
        self.class_names = ['air_conditioner', 'car_horn', 'children_playing', 'dog_bark', 
                    'drilling', 'engine_idling', 'gun_shot', 'jackhammer', 'siren', 'street_music']
        self.last_prediction_time = 0
        self.FS = FS
        self.trigger = False
        self.alert = None
    
    def extract_features(self, audio_data):
        """Extract MFCCS Features"""

        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        mfccs = librosa.feature.mfcc(y=audio_data, sr=FS, n_mfcc=40)
        return np.mean(mfccs.T, axis=0)

    def audio_callback(self, indata, frames, time_info, status):
        """Handles Audio Callback from Microphone"""

        self.trigger = False
        volume_norm = np.linalg.norm(indata) / np.sqrt(len(indata))
        current_time = time.time()
        if volume_norm > THRESHOLD and (current_time - self.last_prediction_time) > COOLDOWN_SEC:
            audio_flat = indata.flatten()
            features = self.extract_features(audio_flat).reshape(1, -1)
            features_scaled = self.scaler.transform(features)
            
            pred_id = self.model.predict(features_scaled)[0]
            probs = self.model.predict_proba(features_scaled)[0]
            label = self.class_names[pred_id]
            conf = probs[pred_id] * 100

            print(label)

            if label in TARGET_CLASSES and conf >= CONFIDENCE_THRESHOLD:
                print(conf)
                self.trigger = True
                match label:
                    case "siren":
                        self.alert = "ALERT SIREN"
                    case "gun_shot":
                        self.alert = "ALERT GUN"
                    case "car_horn":
                        self.alert = "ALERT CAR"
                    case "dog_bark":
                        self.alert = "ALERT DOG"