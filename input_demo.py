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

# Original
colors = [
        "FF0000", # red
        "FF0000", # red
        "FFFF00", # yellow
        "FFFF00", # yellow
        "C3F2FF", # light cyan
        "7F8BFD", # light blue
        "7F8BFD", # light blue
        "F37900", # orange
        "F37900", # orange 
        "33CC33", # green
        "33CC33", # green
        "8EC9FF"  # light blue
]

# Daft Punk
# colors = [
#         "8e2a8b", # red
#         "8e2a8b", # red
#         "fde74e", # yellow
#         "fde74e", # yellow
#         "86d3f1", # light cyan
#         "86d3f1", # light blue
#         "86d3f1", # light blue
#         "ef58a0", # orange
#         "ef58a0", # orange 
#         "97bd4c", # green
#         "97bd4c", # green
#         "86d3f1"  # light blue
# ]


# LED strip configuration:
LED_COUNT      = 144      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 100     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# constants
samplerate = 16000
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
    if color_1 <= 0:
        hex_1 = "0x000000"
    else:
        hex_1 = '0x{:06x}'.format(color_1)
    
    if color_2 <= 0:
        hex_2 = "0x000000"
    else:
        hex_2 = '0x{:06x}'.format(color_2)

    red = int((int("0x"+hex_1[2:4], 16) * (1-ratio)) + (int("0x"+hex_2[2:4], 16) * ratio))
    green = int((int("0x"+hex_1[4:6], 16) * (1-ratio)) + (int("0x"+hex_2[4:6], 16) * ratio))
    blue = int((int("0x"+hex_1[6:8], 16) * (1-ratio)) + (int("0x"+hex_2[6:8], 16) * ratio))

    return Color(red, green, blue)

param_max_level = 0.8 # maximum energy 
param_highlight_power = 2 # filter only high energy beats.
param_energy_multiply = 30 # multiply energy values by.
param_mix_power = 4 # for color mixing
param_fade = 0.05 # 5% black every tick.

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
            energy_ratio = index % 1
            if energy_ratio == 0:
                energy = new_energies[energy_index]
            else: 
                energy = new_energies[energy_index] * (1-energy_ratio) + new_energies[energy_index+1] * (energy_ratio)
            energy = round(energy, 6)
            energy = pow(energy, param_highlight_power)
            energy = energy*param_energy_multiply
            energy = pow(energy, param_mix_power)
            if energy > param_max_level:
                energy = param_max_level
            
            cur_color = strip.getPixelColor(index)
            color_mix = mix_colors(cur_color, note_color, energy)
            black_mix = mix_colors(color_mix, 0, param_fade)
            strip.setPixelColor(index, black_mix)

        strip.show()

class LedOutTask(threading.Thread):
    def __init__(self, samples):
        threading.Thread.__init__(self)
        self.samples = samples

    def run(self):
        send_to_leds(self.samples)

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)

# Main program logic follows:
if __name__ == '__main__':
    print("Starting to listen, press Ctrl+C to stop")
   
    # Intialize the library (must be called once before other functions).
    strip.begin()
    strip_reset()

    while True:
        try:
            # read data from audio input
            _, data = audio_in.read()
            # convert data to aubio float samples
            samples = np.fromstring(data, dtype=float_type)
            
            led_out_bg = LedOutTask(samples)
            led_out_bg.start()

            audio_out.write(data)

        except KeyboardInterrupt:
            print("Ctrl+C pressed, exiting")
            break
