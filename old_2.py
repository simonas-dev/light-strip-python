#! /usr/bin/env python

import alsaaudio

# constants
samplerate = 44100
win_s = 2048
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

# Main program logic follows:
if __name__ == '__main__':
    print("Starting to listen, press Ctrl+C to stop")
    # main loop
    while True:
        try:
            # read data from audio input
            _, data = audio_in.read()
            audio_out.write(data)
            
        except KeyboardInterrupt:
            print("Ctrl+C pressed, exiting")
            break
