#matty's fun haar compressor toy
import librosa
import pywt
import sounddevice as sd
import soundfile as sf
from functools import reduce
import numpy as np
import zlib
#import haar

#normalize audio in case it's too loud 
def normalize(sample):
    x1 = abs(sample.max())
    x2 = abs(sample.min())
    k = max(x1, x2)
    if k <= 1.0:
        return sample
    v = 1.0 / k
    sample = sample * v
    return sample

#read and normalize input source amplitude and sample rate
def get_input_data(filename):
    source, inrate = librosa.load(filename, mono=True, sr=44100)
    source = normalize(source)
    return source



#load our input file
input = get_input_data("d:\\tempstuff\\bee.flac")

#Remember how long it is so we can compare after compression
originalLength = len(input.tobytes())

#write the original so we can compare it with volume normalization
sf.write('d:\\tempstuff\\original.flac', input,
         44100, format='flac', subtype='PCM_24')


#perform 8 levels of haar
stuff = pywt.wavedec(input, 'haar', level=8)

for x in range(1,len(stuff)):
    stuff[x] = np.multiply(stuff[x], 2**x)
    
#quantize the detail coefficients
stuff[-5] = np.around(stuff[-5], decimals=2)
stuff[-4] = np.around(stuff[-4], decimals=2)
stuff[-3] = np.around(stuff[-3], decimals=2)
stuff[-2] = np.around(stuff[-2], decimals=2)



#entirely throw away the highest detail coefficients
stuff[-1] = np.zeros_like(stuff[-1])

#throw away all the 0s before we compress
stuff2 = stuff[:-1]

#compress all floats
compLength = zlib.compress(np.hstack(stuff2).tobytes(), level=9)

print("Size after compression is")
print(len(compLength) / originalLength)

print(len(compLength))
print(originalLength)

for x in range(1,len(stuff)):
    stuff[x] = np.divide(stuff[x], 2**x)

reverse = pywt.waverec(stuff, 'haar')

# Write out decompressed result as 24bit Flac
sf.write('d:\\tempstuff\\out.flac', reverse,
         44100, format='flac', subtype='PCM_24')


#play the audio

sd.default.samplerate = 44100
sd.default.channels = 1
sd.default.dtype = 'float32'

os = sd.OutputStream()
os.start()
os.write(reverse)
