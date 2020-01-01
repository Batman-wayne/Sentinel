# Project Sentinel: TiM781 Log File Parser 
# Harris M 
# November 24, 2019 

# LIBRARIES 
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.animation import FuncAnimation
from matplotlib import animation


from scipy import signal
from skimage.io import imread
from numpy.random import randn
from scipy.io import wavfile

# Log file locations 
single_scan = '../sample_logs/Single_11-19-19.log'
dynamic_scan = '../sample_logs/Dynamic-sweep_11-26-19.log'

# Global array/variable instantiation
# Set up formatting for the movie files
# Writer = animation.FFMpegWriter(fps=20, metadata=dict(artist='Me'), bitrate=1800)

# Constants and look-up tables as defined by SICK 
microsecond = 10**(-6)
angle_step = 10000

header_type = {'73524e': 'Read',
                '73574e': 'Write',
                '734d4e': 'Method',
                '73454e': 'Event',
                '735241': 'Answer',
                '735741': 'Answer',
                '73414e': 'Answer',
                '734541': 'Answer',
                '73534e': 'Answer' }

message_class = {'4c4d447363616e64617461': 'Telegram Data' }

scale_factor = {'3F800000': '1x',
                '40000000': '2x' }

# Function: load_file
# Description: Loads a log file generated by the TiM781 sensor
def load_file(file):
    raw_objects = []
    file_length = 0
    try:
        with open(file, "r") as f:
            for line in f:
                raw_objects.append(line)
        return raw_objects
    except IOError:
        print("Error: Couldn't open the specified log file.")

# Function: type converter
# Description: Converts a number to specified base
def type_conv(num, base):
    initial = int(num, 16)
    if base == 's8':
        conv = (initial + 2**7) % 2**8 - 2**7
    elif base == 'u8':
        conv = initial % 2**8 
    elif base == 's16':
        conv = (initial + 2**15) % 2**16 - 2**15
    elif base == 'u16':
        conv = initial % 2**16 
    elif base == 's32':
        conv = (initial + 2**31) % 2**32 - 2**31
    elif base == 'u32':
        conv = initial % 2**32
    elif base == 's64':
        conv = (initial + 2**63) % 2**64 - 2**63
    elif base == 'u64':
        conv = initial % 2**64
    else:
        return initial
    
    return conv

# Function: clean
# Description: prunes a message to be usable
def clean(msg):
    initial_clean = re.findall('[<0-9a-z>]+', msg)

    potential = ''

    for ind in initial_clean:
        if (ind[0] == '<'):
            potential = ind
            break 

    return potential

# Function: concat
# Description: Concatenates a list of hex data into one string 
def concat(msg, a):
    # print(msg)
    if (a == 0):
        # for nibble in msg:
        #     curr += nibble 
        # return curr
        return msg
    else:
        # curr = ''
        # for nibble in msg:
        #     print(nibble)
        #     curr += bytearray.fromhex(nibble).decode()
        return bytearray.fromhex(msg).decode()
        # return bytearray.fromhex(msg).decode()
    
# Function: init_filter
# Description: Regex parsing to return a list of hex data 
def init_filter(msg):
    output = []
    msg = msg[1:-1]
    msg = msg.split('><')
    size = len(msg)
    idx_list = [idx + 1 for idx, val in enumerate(msg) if val == '20'] 
    res = [msg[i: j] for i, j in zip([0] + idx_list, idx_list + ([size] if idx_list[-1] != size else []))] 

    for index in range(len(res)):
        curr = res[index]
        res[index] = curr[:-1]

        current = ''
        
        for nibble in res[index]:
            current += nibble 
        
        output.append(current)

    return output

# Function: telegram_parse
# Description: parses a telegram message
def telegram_parse(msg):
    telegram = {'Version Number': '',
                'Device Number': '',
                'Serial Number': '',
                'Device Status': '',
                'Telegram Counter': '',
                'Scan Counter': '',
                'Time since start-up': '',
                'Time of transmission': '',
                'Status of digital inputs': '',
                'Status of digital outputs': '',
                'Layer Angle': '',
                'Scan Frequency': '',
                'Measurement Frequency': '',
                'Amount of Encoder': '',
                '16-bit Channels': '',
                'Message Count': '',
                'Scale Factor': '',
                'Scale Factor Offset': '',
                'Start Angle': '',
                'Angular Increment': '', 
                'Quantity': '',
                'Measurement': [] }

    counter = 1
    loop = 0
    for message in msg:
        if (counter == 1):
            version = concat(message, 1)
            telegram['Version Number'] = type_conv(version, 'u16')
            counter = counter + 1
        elif (counter == 2):
            device = concat(message, 1)
            telegram['Device Number'] = type_conv(device, 'u16')
            counter = counter + 1
        elif (counter == 3):
            serial = concat(message, 1)
            telegram['Serial Number'] = type_conv(serial, 'u32')
            counter = counter + 1
        elif (counter == 4):
            counter = counter + 1
        elif (counter == 5):
            status = concat(message, 1)
            telegram['Device Status'] = type_conv(status, 'u8')
            counter = counter + 1
        elif (counter == 6):
            count = concat(message, 1)
            telegram['Telegram Counter'] = type_conv(count, 'u16')
            counter = counter + 1
        elif (counter == 7):
            scan = concat(message, 1)
            telegram['Scan Counter'] = type_conv(scan, 'u16')
            counter = counter + 1
        elif (counter == 8):
            startup = concat(message, 1)
            telegram['Time since start-up'] = type_conv(startup, 'u32') * microsecond
            counter = counter + 1
        elif (counter == 9):
            transmission = concat(message, 1)
            telegram['Time of transmission'] = type_conv(transmission, 'u32') * microsecond
            counter = counter + 1
        elif (counter == 10):
            inputs = concat(message, 1)
            telegram['Status of digital inputs'] = type_conv(inputs, 'u8')
            counter = counter + 1
        elif (counter == 11):
            counter = counter + 1
        elif (counter == 12):
            counter = counter + 1
        elif (counter == 13):
            outputs = concat(message, 1)
            telegram['Status of digital outputs'] = type_conv(outputs, 'u8')
            counter = counter + 1
        elif (counter == 14):
            angle = concat(message, 1)
            telegram['Layer Angle'] = type_conv(angle, 'u16')
            counter = counter + 1
        elif (counter == 15):
            scan = concat(message, 1)
            telegram['Scan Frequency'] = type_conv(scan, 'u32')
            counter = counter + 1
        elif (counter == 16):
            measure = concat(message, 1)
            telegram['Measurement Frequency'] = type_conv(measure, 'u32')
            counter = counter + 1
        elif (counter == 17):
            encoder = concat(message, 1)
            telegram['Amount of Encoder'] = type_conv(encoder, 'u32')
            counter = counter + 1
        elif (counter == 18):
            channels = concat(message, 1)
            telegram['16-bit Channels'] = type_conv(channels, 'u32')
            counter = counter + 1
        elif (counter == 19):
            # THIS IS THE DIST1 CHECK
            counter = counter + 1
        elif (counter == 20):
            scale = concat(message, 1)
            telegram['Scale Factor'] = scale_factor[scale]
            counter = counter + 1
        elif (counter == 21):
            offset = concat(message, 1)
            telegram['Scale Factor Offset'] = type_conv(offset, 'u32')
            counter = counter + 1
        elif (counter == 22):
            angle = concat(message, 1)
            telegram['Start Angle'] = type_conv(angle, 's32') / angle_step
            counter = counter + 1
        elif (counter == 23):
            increment = concat(message, 1)
            telegram['Angular Increment'] = type_conv(offset, 'u16') / angle_step
            counter = counter + 1
        elif (counter == 24):
            count = concat(message, 1)
            telegram['Message Count'] = type_conv(count, 'u16')
            counter = counter + 1
        else: 
            telegram['Measurement'].append(type_conv(concat(message, 1), 'u16'))
            loop = loop + 1 
            if (loop == telegram['Message Count']):
                break
                
    return telegram


# Function: Parser
# Description: Loads a log file and parses it 
def parser(file):
    output = [] 
    clean_objects = []
    raw_objects = load_file(file)

    for raw_object in raw_objects:
        curr = clean(raw_object)
        if (curr == ''):
            continue 
        else:
            clean_objects.append(clean(raw_object))

    for clean_object in clean_objects: 
        init = init_filter(clean_object)
        
        if (len(init) > 0):
            header = init[0]
            header = header[2:]
            actual = init[2:]
            fetch = header_type.get(header, None)

            if (fetch == 'Read'):
                print("Received a static telegram!")
            elif (fetch == 'Answer'):
                data = telegram_parse(init[2:]).copy()
                output.append(data)
                # print("Parse!")
            elif (fetch == 'Event'):
                print("Received a dynamic telegram!")
                data = telegram_parse(init[2:])
                output.append(data)
            else:
                print("Parsing this type of message is not supported yet.")
   

    return output

def init():
    ax.set_xlim(-5000, 5000)
    ax.set_ylim(-5000, 5000)
    return ln,

def update(frame):
    global looper
    current = res[looper]
    xdata = []
    ydata = []
    current_data = current['Measurement']
    increment = current['Angular Increment']
    for message in range(len(current_data)):
        angle = message * 0.333
        xdata.append((current_data[message]) * np.cos(np.radians(angle)))
        ydata.append((current_data[message]) * np.sin(np.radians(angle)))  
    # ln.set_data(xdata, ydata)
    ln.set_xdata(xdata)
    ln.set_ydata(ydata)
    looper = looper + 1
    return ln,

if __name__=="__main__":
    res = parser(dynamic_scan)

    fig, ax = plt.subplots()
    xdata, ydata = [], []
    ln, = plt.plot([], [], 'ro')

    def init():
        ax.set_xlim(0, 2*np.pi)
        ax.set_ylim(-1, 1)
        return ln,

    def update(frame):
        xdata.append(frame)
        ydata.append(np.sin(frame))
        ln.set_data(xdata, ydata)
        return ln,

    ani = FuncAnimation(fig, update, frames=np.linspace(0, 2*np.pi, 128),
                        init_func=init, blit=True)


    looper = 0

    ani = FuncAnimation(fig, update, frames=np.linspace(-5000, 5000),
                        init_func=init)

    graph_x = []
    graph_y = []

    output = res[5]

    for message in range(output['Message Count']):
        curr = output['Measurement']
        dist = curr[message]
        increment = output['Angular Increment']
        angle = message * 0.333
        graph_x.append((dist/1000) * np.cos(np.radians(angle)))
        graph_y.append((dist/1000) * np.sin(np.radians(angle)))
        

    plt.plot(graph_x, graph_y)