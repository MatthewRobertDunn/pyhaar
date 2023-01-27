from tokenize import String
import wavefile
import pywt
import numpy as np
import sounddevice as sd
import soundfile as sf
import zlib


#Number of PCM samples we fit into a block
BLOCK_SIZE = 2048

#The wavelet we are using
WAVELET = 'haar'
LEVEL = 4
PATHS = ['aaaa', 'aaad', 'aada', 'aadd', 'adaa', 'adad', 'adda', 'addd', 'daaa', 'daad', 'dada', 'dadd', 'ddaa', 'ddad', 'ddda', 'dddd']


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
        wp = pywt.WaveletPacket(data=input, wavelet=WAVELET)
        return [node.data for node in wp.get_level(LEVEL, 'natural')]

    def quantize(self, input):
        #quantize the detail coefficients
        #coefficients are ordered into least to most detail
        #Interestingly as each detail coefficient is smaller than the last
        #this applies progressively more quantization
        bands = len(input)
        #for i in range(0, bands):
            #input[i] = np.around(input[i], decimals=0).astype(np.float16)
        #input[0] = np.around(input[0], decimals=1).astype(np.float16)
        #print(f"{input[2].var()} - {input[3].var()}")

        foo = int((input[2].var() - input[3].var()) * 1000);
        #print(foo)

        input[0] = np.around(input[0], decimals=2).astype(np.float16)
        input[1] = np.around(input[1], decimals=2).astype(np.float16)
        input[2] = np.around(input[2], decimals=2).astype(np.float16)
        input[3] = np.around(input[3], decimals=2).astype(np.float16)
        input[4] = np.around(input[4], decimals=2).astype(np.float16)
        input[5] = np.around(input[5], decimals=2).astype(np.float16)
        input[6] = np.around(input[6], decimals=2).astype(np.float16)
        input[7] = np.around(input[7], decimals=2).astype(np.float16)
        input[8] = np.around(input[8], decimals=-100).astype(np.float16)
        input[9] = np.around(input[9], decimals=-100).astype(np.float16)
        input[10] = np.around(input[10], decimals=-100).astype(np.float16)
        input[11] = np.around(input[11], decimals=-100).astype(np.float16)
        input[12] = np.around(input[12], decimals=-100).astype(np.float16)
        input[13] = np.around(input[13], decimals=-100).astype(np.float16)
        input[14] = np.around(input[14], decimals=-100).astype(np.float16)
        input[15] = np.around(input[15], decimals=-100).astype(np.float16)
        for i in range(len(input)):
            input[i] += 0
        
    def Compress(self, input):
        byte_data = np.hstack(np.hstack(input)).astype(np.float16).tobytes()
        result = zlib.compress(byte_data, level=9)
        print(f"{len(result)} / {len(byte_data)} -- {len(result) / len(byte_data)}")



class Decoder:
    def decode_bock(self, block):
        rec = list(map(self.dwt_rec,block))
        return rec


    def dwt_rec(self,input):
        wp = pywt.WaveletPacket(data=None, wavelet=WAVELET)
        for i in range(0,len(PATHS)):
            wp[PATHS[i]] = input[i]
        return wp.reconstruct(update=False)


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
        #out.write(data)
