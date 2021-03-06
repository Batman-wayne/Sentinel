# Project Sentinel: TiM781 live parser
# Harris M 
# January 8, 2020 

# LIBRARIES
import sys
import socket
import time
from datetime import datetime 

# EXTERNAL PATHS
sys.path.append('../../SLAM/RANSAC')

# EXTERNAL LIBRARIES
#import RANSAC as ransac

# CONSTANTS 
PORT = 2112
REQUEST_SINGLE_SCAN = b'\x02sRN LMDscandata\x03'  
REQUEST_CONT_SCAN = b'\x02sEN LMDscandata 1\x03'
STOP_CONT_SCAN = b'\x02sEN LMDscandata 0\x03'
IP_ADDRESS = '169.254.100.100'

microsecond = 10**(-6)
angle_step = 10**(3)
scale_factor = {'3F800000': '1x',
                '40000000': '2x' }

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

# Function: telegram_parse 
# Description: Parses a telegram message 
def telegram_parse(scan):
    telegram = {'Version Number': '',
                'Device Number': '',
                'Serial Number': '',
                'Device Status': '',
                'Telegram Counter': '',
                'Scan Counter': '',
                'Time since start-up': '',
                'Time of transmission': '',
                'Scan Frequency': '',
                'Measurement Frequency': '',
                'Amount of Encoder': '',
                '16-bit Channels': '',
                'Scale Factor': '',
                'Scale Factor Offset': '',
                'Start Angle': '',
                'Angular Increment': '', 
                'Quantity': '',
                'Motor encoder': '',
                'Measurement': [] }

    if (scan[0] != 'sRA' or scan[1] != 'LMDscandata'):
        print("There is something wrong with the scan data")
    else:
        telegram['Version Number'] = type_conv(scan[2], 'u16')
        telegram['Device Number'] = type_conv(scan[3], 'u16')
        telegram['Serial Number'] = type_conv(scan[4], 'u32')
        telegram['Device Status'] = type_conv(scan[6], 'u8')
        telegram['Telegram Counter'] = type_conv(scan[7], 'u16')
        telegram['Scan Counter'] = type_conv(scan[8], 'u16')
        telegram['Time since start-up'] = type_conv(scan[9], 'u32') * microsecond
        telegram['Time of transmission'] = type_conv(scan[10], 'u32') * microsecond
        telegram['Scan Frequency'] = type_conv(scan[16], 'u32') 
        telegram['Measurement Frequency'] = type_conv(scan[17], 'u32') 
        telegram['Amount of Encoder'] = type_conv(scan[18], 'u32')
        telegram['16-bit Channels'] = type_conv(scan[19], 'u32')
        telegram['Scale Factor'] = scale_factor[scan[21]]
        telegram['Scale Factor Offset'] = type_conv(scan[22], 'u32')
        telegram['Start Angle'] = type_conv(scan[23], 's32') / angle_step
        telegram['Angular Increment'] = type_conv(scan[24], 'u16') / angle_step
        telegram['Quantity'] = type_conv(scan[25], 'u16')

        for message in range(26, 26 + telegram['Quantity']):
            telegram['Measurement'].append(type_conv(scan[message], 'u16'))

    return telegram    

# Function: live_parse 
# Description: Starts the socket and begins parsing appropriately 
def live_parse():
    curr = datetime.now()
    file_name = str(curr.year) + "-" + str(curr.month) + "-" + str(curr.day) + "_" + str(curr.hour) + "-" + str(curr.minute) + "-" + str(curr.second) + ".txt"

    insideTelegram = False 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP_ADDRESS, PORT))
    sock.send(REQUEST_CONT_SCAN)

    with open(file_name, "w") as file:
        for byte in sock.recv(1):
            curr_time = str(datetime.now())
            file.write(curr_time)

# Function: single_parse 
# Description: Starts the socket and begins parsing appropriately 
def single_parse():
    insideTelegram = False 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP_ADDRESS, PORT))
    sock.send(REQUEST_SINGLE_SCAN)

    scan = []
    curr = ''
    while 1:
        msg_orig = sock.recv(1)
        msg = msg_orig.decode('utf-8')
        if msg_orig == b'\x02':
            insideTelegram = True 
        elif msg_orig == b'\x03':
            insideTelegram = False 
            break
        elif msg == ' ':
            scan.append(curr)
            curr = ''
        else:
            curr += msg
    
    # curr = datetime.now()
    # file_name = str(curr.year) + "-" + str(curr.month) + "-" + str(curr.day) + "_" + str(curr.hour) + "-" + str(curr.minute) + "-" + str(curr.second) + ".txt"

    initial_parse = telegram_parse(scan)
    
    print(initial_parse)

    # with open(file_name, 'w') as file:
    #     curr_time = str(datetime.now())
    #     file.write(curr_time + ' ')

    #     for scans in scan:
    #         file.write(scans)
    #         file.write(' ')

# live_parse()
single_parse()
