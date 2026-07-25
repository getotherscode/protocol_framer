import serial
import serial.tools.list_ports
from crc import check_modbus_crc16

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


def serial_transmit(port: serial.Serial, data: bytes):
    transmit_len = port.write(data)
    if transmit_len != len(data):
        raise RuntimeError(f" transmit is not complete, actually transmit number is {transmit_len} ")

def serial_receive(port: serial.Serial, data:bytearray) -> bool:
    port.open()
    read_bytes = port.read()                                # max read block time = timeout
    port.close()
    
    if check_modbus_crc16(bytearray(read_bytes)):
        data = bytearray(read_bytes)
        print(f" INFO: serial read data {data} ")
        return True
    else:
        print(f" ABNORMAL: serial data crc error {read_bytes} ")
        return False
