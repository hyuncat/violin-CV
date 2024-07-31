import numpy as np
import threading
import os
import essentia.standard as es
from app.modules.midi.MidiData import MidiData
from app.config import AppConfig

class AudioData:
    def __init__(self, MidiData: MidiData=None, audio_filepath: str=None):
        """
        Initialize the RecordingData with an array of zeros of length equal to the MIDI file length.
        @param:
            - midi_length: int, length of the MIDI file in samples
        """
        self._MidiData = MidiData

        # Initialize the audio data array with all zeros, with capacity 
        # based on MIDI file length and app's SAMPLE_RATE
        if self._MidiData is not None:
            self.capacity = int(self._MidiData.get_length() * AppConfig.SAMPLE_RATE)
            self.data = np.zeros(self.capacity, dtype=np.float32)
        
        else: # If no MIDI file is provided, use a default length of 60 seconds
            DEFAULT_LENGTH = 60
            self.capacity = int(DEFAULT_LENGTH * AppConfig.SAMPLE_RATE)
            
        if audio_filepath is not None:
            self.load_data(audio_filepath) # (also sets capacity)

        # To ensure thread-safe access to the buffer
        # as AudioRecorder and AudioPlayer will be accessing it
        self.lock = threading.Lock()

    def load_data(self, audio_filepath: str):
        """
        Load audio data into the recording data array.
        @param:
            - audio_data (np.ndarray): audio data to load into the recording data array
        """
        loader = es.MonoLoader(filename=audio_filepath, sampleRate=AppConfig.SAMPLE_RATE)
        audio_data = loader()

        # Set the loaded audio from file as the new self.audio_data and update capacity
        self.data = audio_data
        self.capacity = len(audio_data)

    def write_data(self, buffer: np.ndarray, start_time: float=0):
        """
        Add a new audio chunk to the recording data, growing the self.data array if necessary.
        @param:
            - buffer (np.ndarray): Temporary buffer of new audio data to be added
            - start_time (float), time in seconds to start adding the new chunk
        """
        start_index = int(start_time * AppConfig.SAMPLE_RATE)
        end_index = start_index + len(buffer)

        if end_index > self.capacity:
            # Double the capacity
            self.capacity *= 2
            self.data = np.resize(self.data, self.capacity)

        # Write the new audio data to the data array
        with self.lock:
            self.data[start_index:end_index] = buffer

    def read_data(self, start_time: float=0, end_time: float=0) -> np.ndarray:
        """
        Read audio data from the recording data array.
        @param:
            - start_time (float): time in seconds to start reading from
            - end_time (float): time in seconds to stop reading
        @return:
            - data (np.ndarray): audio data array from start_time to end_time
        """
        start_index = int(start_time * AppConfig.SAMPLE_RATE)
        end_index = int(end_time * AppConfig.SAMPLE_RATE)

        with self.lock:
            return self.data[start_index:end_index]