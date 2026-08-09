import serial
import serial.tools.list_ports
from crc import check_modbus_crc16

MIN_MESSAGE_LEN  = 6
MESSAGE_HEAD_LEN = 4
CRC_LEN          = 2
DEVICE_ID        = 9

def serial_get(serial_name: str, baudrate:int, timeout:int) -> serial.Serial:
    ports = []

    for port in serial.tools.list_ports.comports():
        info = f"{port.device} {port.description}"          #  concatenate all key characters
        if serial_name in info:
            ports.append(port.device)

    if not ports:
        raise RuntimeError(f"do not find any com like {serial_name} !!!")
    if len(ports) > 1:
        raise RuntimeError(f"{serial_name} is not the only one !!!")

    print(f"find the target com {port.description}")
    port = serial.Serial(                                   # configure the port
        port     = ports[0],
        baudrate = baudrate,
        timeout  = timeout, 
        bytesize = serial.EIGHTBITS,  
        parity   = serial.PARITY_NONE,  
        stopbits = serial.STOPBITS_ONE,
    )
    return port


def serial_transmit(port: serial.Serial, data: bytearray):
    transmit_len = port.write(data)
    if transmit_len != len(data):
        raise RuntimeError(f" transmit is not complete, actually transmit number is {transmit_len} ")
    else:
        print(f"success send message: {data.hex(' ')}")

def serial_receive(port: serial.Serial) -> bytes:
    read_frame: bytearray = bytearray(0)
    head: bytes = port.read(MESSAGE_HEAD_LEN)               # max read block time = serial.timeout, read 2 bytes and get length

    if len(head) < MESSAGE_HEAD_LEN:
        return None

    if head[0] != DEVICE_ID:
        print("device id is wrong !")
        return None

    read_frame.extend(bytearray(head))
    data_len: int = (head[2] << 8) + head[3]
    rest_message_len: int = data_len + CRC_LEN
    read_frame.extend(bytearray(port.read(rest_message_len)))                        
    

    msg_len = len(read_frame)
    if msg_len < (MESSAGE_HEAD_LEN + data_len + CRC_LEN) and msg_len != 0:
        print(f"ABNORMAL: message length is too short {msg_len} ")
        return None
    else:
        recv_frame = bytes(read_frame)
        print(f"received message: {recv_frame.hex(' ')}")
    
    if check_modbus_crc16(recv_frame):
        print(f"INFO: check message crc success !!! ")
        return recv_frame
    else:
        print(f"ABNORMAL: check message crc failed !!!")
        return None
