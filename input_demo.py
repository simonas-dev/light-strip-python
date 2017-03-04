#! /usr/bin/env python

import alsaaudio
import numpy as np
from aubio import source, pvoc, specdesc, float_type, pitch, filterbank
from neopixel import *
import math
import threading

A4 = 440
C0 = A4*np.power(2, -4.75)
name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

colors = ["FF0000", "FF0000","FFFF00","FFFF00","C3F2FF","7F8BFD","7F8BFD","F37900","F37900","33CC33","33CC33","8EC9FF"]

# LED strip configuration:
LED_COUNT      = 144      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 100     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# constants
samplerate = 44100
win_s = 1024
hop_s = win_s // 2
framesize = hop_s

# set up audio input
audio_in = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE, device='plughw:CARD=Set,DEV=0')
audio_in.setperiodsize(framesize)
audio_in.setrate(samplerate)
audio_in.setformat(alsaaudio.PCM_FORMAT_FLOAT_LE)
audio_in.setchannels(1)
print "Audio Input ready"

# Open the device in playback mode. 
audio_out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, device='plughw:CARD=Set,DEV=0')
audio_out.setperiodsize(framesize)
audio_out.setrate(samplerate)
audio_out.setformat(alsaaudio.PCM_FORMAT_FLOAT_LE)
audio_out.setchannels(1)
print "Audio Output ready"

step = 6000 / LED_COUNT

def strip_reset():
    for i in range(144):
        strip.setPixelColor(i, Color(0, 0, 0))

tolerance = 0.8
pitch_o = pitch("default", win_s, hop_s, samplerate)
pitch_o.set_unit("Hz")
pitch_o.set_tolerance(tolerance)

# Mel-Energy 
f = filterbank(40, win_s)
pv = pvoc(win_s, hop_s)
f.set_mel_coeffs_slaney(samplerate)

def get_pitch(samples):
    return pitch_o(samples)[0]

def get_note_index(freq):
    div = freq/C0
    if div == 0:
        return 0
    h = round(12 * math.log(div, 2))
    octave = h // 12
    n = h % 12
    return int(n)

def get_color(hex):
    red = int("0x"+hex[0:2], 0)
    green = int("0x"+hex[2:4], 0)
    blue = int("0x"+hex[4:6], 0)

    return Color(red, green, blue)

def mix_colors(color_1, color_2, ratio):
    hex_1 = '0x{:06x}'.format(color_1)
    hex_2 = '0x{:06x}'.format(color_2)
    
    inv_ratio = (1-ratio)
    
    red = int((int("0x"+hex_1[2:4], 16) * inv_ratio) + ( int("0x"+hex_2[2:4], 16) * ratio))
    green = int((int("0x"+hex_1[4:6], 16) * inv_ratio) + ( int("0x"+hex_2[4:6], 16) * ratio))
    blue = int((int("0x"+hex_1[6:8], 16) * inv_ratio) + (int("0x"+hex_2[6:8], 16) * ratio))

    return Color(red, green, blue)   

def send_to_leds(_samples):
    if len(_samples) > 0:
        fftgrain = pv(_samples)
        new_energies = f(fftgrain)
        pitch_val = get_pitch(_samples)
    
        note_index = get_note_index(pitch_val)
        note_hex = colors[note_index]
        note_color = get_color(note_hex)

        for index in range(144):
            energy_index = int(index/3.6)
            energy = round(new_energies[energy_index], 4)
            if energy > 1:
                energy = 1
            cur_color = strip.getPixelColor(index)
            color_mix = mix_colors(cur_color, note_color, energy)
            strip.setPixelColor(index, mix_colors(color_mix, 0, 0.05))
            
        print note_color
        strip.show()

class LedOutTask(threading.Thread):
    def __init__(self, samples):
        threading.Thread.__init__(self)
        self.samples = samples
    
    def run(self):
        send_to_leds(self.samples)

class AudioOutTask(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
    def run(self):
        audio_out.write(self.data)    

# Main program logic follows:
if __name__ == '__main__':
    print("Starting to listen, press Ctrl+C to stop")

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    strip_reset()
    strip.setPixelColor(1, Color(255, 0, 0))
    strip.show()
    # main loop
    while True:
        try:
            strip_reset()
            # read data from audio input
            _, data = audio_in.read()
            # convert data to aubio float samples
            samples = np.fromstring(data, dtype=float_type)
            
            led_out_bg = LedOutTask(samples)
            led_out_bg.start()

            audio_out_bg = AudioOutTask(data)
            audio_out_bg.start()
        except KeyboardInterrupt:
            print("Ctrl+C pressed, exiting")
            break