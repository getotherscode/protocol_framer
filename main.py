from depacketizer import depacketizer, get_bin_file_path, parse_bin_file_size
from serial_transport import serial_transmit, serial_receive, serial_get
from crc import get_modbus_crc16
from enum import Enum
from dataclasses import dataclass
import serial
import time

PACK_SIZE       = 1024                                      # do not beyond 65535
UINT16_MAX      = 65535
UINT8_MAX       = 256

SERIAL_NAME     = "COM7"                                    # only need key words
SERIAL_BAUDRATE = 115200 
SERIAL_TIMEOUT  = 0.05

DEVICE_ADDR     = 9

class Message_Type(Enum):
    MSG_INIT           = 1
    MSG_PACK_INFO_RQST = 2
    MSG_PACK_RQST      = 3
    MSG_FINISH         = 4

class OTA_State(Enum):
    OTA_INIT           = 1
    OTA_PACK_INFO_RQST = 2
    OTA_PACK_RQST      = 3
    OTA_FINISH         = 4

@dataclass
class OTA_OBJ:
    state: int = 0
    pack_idx: int = 0

def pack_message(dev_addr:int, cmd:int, data_len:int, data:bytearray) -> bytearray:
    frame = bytearray()

    if dev_addr > UINT8_MAX:
        raise ValueError(f" device id beyond {UINT16_MAX} !!! ")
    frame.append(dev_addr)

    if cmd > UINT8_MAX:
        raise ValueError(f" cmd beyond {UINT16_MAX} !!! ")
    frame.append(cmd)

    if data_len > UINT16_MAX:
        raise ValueError(f" data length beyond {UINT16_MAX} !!! ")
    data_len_high, data_len_low = data_len.to_bytes(2, 'big')
    frame.append(data_len_high)
    frame.append(data_len_low)

    if bytearray is not None:
        frame.extend(bytearray)

    crc_low, crc_high = get_modbus_crc16(frame)
    frame.append(crc_low)
    frame.append(crc_high)

def ota_task(my_serial: serial.Serial, path: list[str]):

    match OTA_OBJ.state:
        case OTA_State.OTA_INIT:
            init_frame: bytearray = pack_message(DEVICE_ADDR, Message_Type.MSG_INIT, 0, None)
            serial_transmit(my_serial, init_frame)

        case OTA_State.OTA_PACK_INFO_RQST:
            file_size = parse_bin_file_size(path)
            pack_num: int  = file_size / PACK_SIZE
            if file_size % PACK_SIZE: pack_num += 1

            pack_info: bytearray = bytearray()
            pack_info.append(pack_num.to_bytes(2, 'big'))
            pack_info.append(PACK_SIZE.to_bytes(2, 'big'))
            info_frame: bytearray = pack_message(DEVICE_ADDR, Message_Type.MSG_PACK_INFO_RQST, 4, pack_info)
            serial_transmit(my_serial, info_frame)

        case OTA_State.OTA_PACK_RQST:
            data_frame: bytearray = bytearray()
            if OTA_OBJ.pack_idx > UINT16_MAX:
                raise ValueError(f" pack index beyond {UINT16_MAX} !!! ")
            pack_idx_high, pack_idx_low = OTA_OBJ.pack_idx.to_bytes(2, 'big')
            data_frame.append(pack_idx_high)
            data_frame.append(pack_idx_low)
            data_frame.append(depacketizer(PACK_SIZE, path, OTA_OBJ.pack_idx))

            pack_frame: bytearray = pack_message(DEVICE_ADDR, Message_Type.MSG_PACK_INFO_RQST, PACK_SIZE+2, pack_frame)
            serial_transmit(my_serial, pack_frame)
            print(f"send pack {OTA_OBJ.pack_idx}, fireware length = {len(data_frame-2)}")

        case OTA_State.OTA_FINISH:
            finish_frame = pack_message(DEVICE_ADDR, Message_Type.MSG_FINISH, 0, None)
            serial_transmit(my_serial, finish_frame)
            print("OTA process finish !!!")

    my_serial.close()


def main():
    my_serial       = serial_get(SERIAL_NAME, SERIAL_BAUDRATE, SERIAL_TIMEOUT)
    bin_file_path   = get_bin_file_path()
    recv: bytearray = bytearray()
    cmd_offset: int = 1
    pack_idx_offset1: int = 4
    pack_idx_offset2: int = 5
    cmd: int = None

    while True:
        ota_task(my_serial, bin_file_path)
        if serial_receive(my_serial, recv):
            cmd = recv[cmd_offset]
        else:
            cmd = None
            time.sleep(1)

        match cmd:
            case Message_Type.MSG_PACK_INFO_RQST: 
                OTA_OBJ.state = OTA_State.OTA_PACK_INFO_RQST

            case Message_Type.MSG_PACK_RQST: 
                OTA_OBJ.state = OTA_State.OTA_PACK_RQST
                OTA_OBJ.pack_idx = (recv[pack_idx_offset1] << 8) + recv[pack_idx_offset2]

            case Message_Type.MSG_FINISH: 
                OTA_OBJ.state = OTA_State.OTA_FINISH 
                break
        



if __name__ ==  "__main__":
    main()