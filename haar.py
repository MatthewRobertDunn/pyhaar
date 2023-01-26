from tokenize import String
import wavefile
import pywt
import numpy as np
import sounddevice as sd


#Number of PCM samples we fit into a block
BLOCK_SIZE = 65536

#The wavelet we are using
WAVELET = 'haar'

class Encoder:
    def __init__(self, fileName) -> None:
        self.reader = wavefile.WaveReader(fileName) 

    '''Yields a stream of compressed blocks'''
    def encode_block(self):
        for frame in self.reader.read_iter(size=BLOCK_SIZE):
            
            #pad any non BLOCK_SIZE data out to block_size
            frame = self.pad_frame(frame)
            
            #Run DWT on each audio channel
            dwt = list(map(self.dwt_dec,frame))
            
            #Quantize each channel
            for channel in dwt:
                self.quantize(channel)

            #yield result

            #todo: include a block header
            yield dwt
    
    def pad_frame(self, frame):
        result = []
        for channel in range(0,len(frame)):
            result.append(self.resize(frame[channel]))
        return result

    def resize(self, input):
        if len(input) < BLOCK_SIZE:
            return np.pad(input, (0, BLOCK_SIZE - len(input)), 'constant', constant_values=(0, 0))
        else:
            return input

    def dwt_dec(self,input):
        return pywt.wavedec(input, 'haar', level=4)

    def quantize(self, input):
        #quantize the detail coefficients
        #coefficients are ordered into least to most detail
        #Interestingly as each detail coefficient is smaller than the last
        #this applies progressively more quantization
        input[1] = np.around(input[1], decimals=2)
        input[2] = np.around(input[2], decimals=2)
        input[3] = np.around(input[3], decimals=2)


    def Compress(self, input):
        #todo: entropy encode
        pass


class Decoder:
    def decode_bock(self, block):
        rec = list(map(self.dwt_rec,block))
        return rec


    def dwt_rec(self,input):
        return pywt.waverec(input, 'haar')



h = Encoder("d:\\tempstuff\\bee.flac");
d = Decoder()

sd.default.samplerate = 96000       #Make sure this matches your input file or weird stuff
sd.default.channels = 2
sd.default.dtype = 'float32'

os = sd.OutputStream()
os.start()

for block in h.encode_block():
    print(block)
    r = d.decode_bock(block)
    os.write(np.ascontiguousarray((np.transpose(r)))) #annoying I have to do this transpose
