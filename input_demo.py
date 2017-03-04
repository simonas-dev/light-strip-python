#! /usr/bin/env python

import alsaaudio
import numpy as np
from aubio import source, pvoc, specdesc, float_type, pitch, filterbank

from neopixel import *


# LED strip configuration:
LED_COUNT      = 144      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

# constants
samplerate = 44100
win_s = 2048
hop_s = win_s // 2
framesize = hop_s

# set up audio input
audio_in = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE, card='plughw:CARD=Set,DEV=0')
audio_in.setperiodsize(framesize)
audio_in.setrate(samplerate)
audio_in.setformat(alsaaudio.PCM_FORMAT_FLOAT_LE)
audio_in.setchannels(1)
print "Audio Input ready"

# Open the device in playback mode. 
audio_out = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK, card='plughw:CARD=Set,DEV=0')
audio_out.setperiodsize(framesize)
audio_out.setrate(samplerate)
audio_out.setformat(alsaaudio.PCM_FORMAT_FLOAT_LE)
audio_out.setchannels(1)
print "Audio Output ready"

step = 6000 / LED_COUNT

# beat 
def setColor(energy):
    if energy > 1:
        energy = 1
    print energy
    color = Color(int(255*energy), int(255*energy), int(255*energy))
    for i in range(LED_COUNT):
        strip.setPixelColor(i, color)
    strip.show()

def strip_reset():
    for i in range(144):
        strip.setPixelColor(i, Color(0, 0, 0))

pv = pvoc(win_s, hop_s)
# methods = ['default', 'energy', 'hfc', 'complex', 'phase', 'specdiff', 'kl',
#         'mkl', 'specflux', 'centroid', 'slope', 'rolloff', 'spread', 'skewness',
#         'kurtosis', 'decrease',]
methods = ['energy' ]
all_descs = {}
o = {}

# Pitch -- RIP
tolerance = 0.8
pitch_o = pitch("yin", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_tolerance(tolerance)

# Mel-Energy 
f = filterbank(1, win_s)
f.set_mel_coeffs_slaney(samplerate)

for method in methods:
    cands = []
    all_descs[method] = np.array([])
    o[method] = specdesc(method, win_s)

def get_pitch(samples):
    return pitch_o(samples)[0]

# Main program logic follows:
if __name__ == '__main__':
    print("Starting to listen, press Ctrl+C to stop")

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    strip_reset()
    strip.show()
    # main loop
    while True:
        try:
            # read data from audio input
            _, data = audio_in.read()
            # convert data to aubio float samples
            samples = np.fromstring(data, dtype=float_type)
            if len(samples) > 0:
                fftgrain = pv(samples)
                # energy_val = o['energy'](fftgrain)[0]
                new_energies = f(fftgrain)
                print new_energies
                energy_val = 20000
                setColor(float(energy_val/50000))
            audio_out.write(data)
        except KeyboardInterrupt:
            print("Ctrl+C pressed, exiting")
            break