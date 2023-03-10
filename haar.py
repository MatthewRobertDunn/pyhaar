from tokenize import String
import wavefile
import pywt
import numpy as np
import sounddevice as sd
import soundfile as sf
import zlib


#Number of PCM samples we fit into a block
BLOCK_SIZE = 65536

#The wavelet we are using
WAVELET = 'db7'

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

            #Compress
            self.Compress(dwt)    

            #yield result

            #todo: include a block header
            yield dwt
    
    def pad_frame(self, frame):
        result = []
        for channel in range(0,len(frame)):
            result.append(self.resize(frame[channel]))
        return np.array(result, dtype='float32')

    def resize(self, input):
        if len(input) < BLOCK_SIZE:
            return np.pad(input, (0, BLOCK_SIZE - len(input)), 'constant', constant_values=(0, 0))
        else:
            return input

    def dwt_dec(self,input):
        return pywt.wavedec(input, WAVELET, level=4)

    def quantize(self, input):
        #quantize the detail coefficients
        #coefficients are ordered into least to most detail
        #Interestingly as each detail coefficient is smaller than the last
        #this applies progressively more quantization
        input[1] = np.around(input[1], decimals=3).astype(np.float16)
        input[2] = np.around(input[2], decimals=2).astype(np.float16)
        input[3] = np.around(input[3], decimals=1).astype(np.float16)
        #input[4] = np.around(input[4], decimals=0).astype(np.float16)
        input[4] = np.zeros(len(input[4]),dtype=np.float16)
        for i in range(len(input)):
            input[i] += 0

    def Compress(self, input):
        byte_data = np.hstack(np.hstack(input)).astype(np.float16).tobytes()
        result = zlib.compress(byte_data, level=8)
        print(f"{len(result)} / {len(byte_data)} -- {len(result) / len(byte_data)}")



class Decoder:
    def decode_bock(self, block):
        rec = list(map(self.dwt_rec,block))
        return rec


    def dwt_rec(self,input):
        return pywt.waverec(input, WAVELET)



h = Encoder("d:\\tempstuff\\coke.flac");
d = Decoder()

sd.default.samplerate = 44100       #Make sure this matches your input file or weird stuff
sd.default.channels = 2
sd.default.dtype = 'float32'

os = sd.OutputStream()
os.start()

with sf.SoundFile('d:\\tempstuff\\db7.flac','w',44100, format='flac', channels=2, subtype='PCM_24') as out:
    for block in h.encode_block():
        r = d.decode_bock(block)
        data = np.ascontiguousarray((np.transpose(r)))
        os.write(data) #annoying I have to do this transpose
        out.write(data)
