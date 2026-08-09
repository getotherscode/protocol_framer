from depacketizer import depacketizer, get_bin_file_path, parse_bin_file_size
from serial_transport import serial_transmit, serial_receive, serial_get
from crc import get_modbus_crc16, modbus_crc16_update
from enum import IntEnum
from dataclasses import dataclass
import serial
import time

PACK_SIZE       = 1024                                      # do not beyond 65535
UINT16_MAX      = 65535
UINT8_MAX       = 256

SERIAL_NAME     = "COM3"                                    # only need key words
SERIAL_BAUDRATE = 115200 
SERIAL_TIMEOUT  = 0.05

DEVICE_ADDR     = 9

class Message_Type(IntEnum):                                # do not use the Enum, distinguish with C-lang
    MSG_INIT           = 1
    MSG_PACK_INFO_RQST = 2
    MSG_PACK_RQST      = 3
    MSG_FINISH         = 4

class OTA_State(IntEnum):
    OTA_INIT           = 0
    OTA_PACK_INFO_RQST = 1
    OTA_PACK_RQST      = 2
    OTA_FINISH         = 3
    OTA_WAIT           = 4

@dataclass
class OTA_OBJ:
    state: int = 0
    pack_idx: int = 0
    total_pack: int = 0
    last_pack_len: int = 0
    crc: int = 0xFFFF

ota_obj = OTA_OBJ()

def pack_message(dev_addr:int, cmd:int, data_len:int, data:bytearray | None) -> bytes:
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

    if data is not None:
        frame.extend(data)

    crc_low, crc_high = get_modbus_crc16(frame)
    frame.append(crc_low)
    frame.append(crc_high)

    return bytes(frame)                                   # append message use bytearray(variable) fixed use bytes

def ota_task(my_serial: serial.Serial, path: list[str]):

    match ota_obj.state:
        case OTA_State.OTA_INIT:
            print(f"OTA STATE: OTA_INIT")
            init_frame: bytes = pack_message(DEVICE_ADDR, Message_Type.MSG_INIT, 0, bytearray())
            serial_transmit(my_serial, init_frame)
            time.sleep(1)

        case OTA_State.OTA_PACK_INFO_RQST:
            print(f"OTA STATE: OTA_PACK_INFO_RQST")
            file_size: int = parse_bin_file_size(path)
            ota_obj.total_pack = int(file_size / PACK_SIZE)
            ota_obj.last_pack_len = file_size % PACK_SIZE
            if ota_obj.last_pack_len != 0: 
                ota_obj.total_pack += 1

            pack_info: bytearray = bytearray()
            pack_info.extend(ota_obj.total_pack.to_bytes(2, 'big'))
            pack_info.extend(PACK_SIZE.to_bytes(2, 'big'))
            info_frame: bytes = pack_message(DEVICE_ADDR, Message_Type.MSG_PACK_INFO_RQST, 4, pack_info)
            serial_transmit(my_serial, info_frame)
            ota_obj.state = OTA_State.OTA_WAIT

        case OTA_State.OTA_PACK_RQST:
            print(f"OTA STATE: OTA_PACK_RQST")
            data_frame: bytearray = bytearray()
            if ota_obj.pack_idx > UINT16_MAX:
                raise ValueError(f" pack index beyond {UINT16_MAX} !!! ")

            print(f"send pack idx = {ota_obj.pack_idx}")
            data_frame.extend(ota_obj.pack_idx.to_bytes(2, 'big'))
            depack_start_addr = (ota_obj.pack_idx - 1) * PACK_SIZE

            unpack: bytes
            if ota_obj.pack_idx == ota_obj.total_pack:
                data_frame.extend(ota_obj.last_pack_len.to_bytes(2,"big"))
                unpack = depacketizer(ota_obj.last_pack_len, path, depack_start_addr)
                data_frame.extend(unpack)
            else:
                data_frame.extend(PACK_SIZE.to_bytes(2,"big"))
                unpack = depacketizer(PACK_SIZE, path, depack_start_addr)
                data_frame.extend(unpack)

            print(f"unpack crc = {modbus_crc16_update(bytearray(unpack), ota_obj.crc)}")

            pack_frame: bytes = pack_message(DEVICE_ADDR, Message_Type.MSG_PACK_RQST, PACK_SIZE + 4, data_frame)
            serial_transmit(my_serial, pack_frame)
            print(f"fireware length = {len(data_frame) - 4}")
            ota_obj.state = OTA_State.OTA_WAIT

        case OTA_State.OTA_FINISH:
            print(f"OTA STATE: OTA_FINISH")
            finish_frame: bytes
            finish_frame = pack_message(DEVICE_ADDR, Message_Type.MSG_FINISH, 0, bytearray())
            serial_transmit(my_serial, finish_frame)
            print("OTA process finish !!!")

        case OTA_State.OTA_WAIT:
            print(f"OTA STATE: OTA_WAIT")
            time.sleep(1)


def main():
    my_serial       = serial_get(SERIAL_NAME, SERIAL_BAUDRATE, SERIAL_TIMEOUT)
    bin_file_path   = get_bin_file_path()
    recv: bytes = None
    cmd_offset: int = 1
    pack_idx_offset1: int = 4
    pack_idx_offset2: int = 5
    cmd: int = None

    while True:
        ota_task(my_serial, bin_file_path)
        recv = serial_receive(my_serial)
        if recv is not None :
            cmd = recv[cmd_offset]
            match cmd:
                case Message_Type.MSG_INIT:
                    ota_obj.state = OTA_State.OTA_WAIT

                case Message_Type.MSG_PACK_INFO_RQST: 
                    ota_obj.state = OTA_State.OTA_PACK_INFO_RQST

                case Message_Type.MSG_PACK_RQST: 
                    ota_obj.state = OTA_State.OTA_PACK_RQST
                    ota_obj.pack_idx = (recv[pack_idx_offset1] << 8) + recv[pack_idx_offset2]

                case Message_Type.MSG_FINISH: 
                    ota_obj.state = OTA_State.OTA_FINISH 
                    break

    my_serial.close()
        



if __name__ ==  "__main__":
    main()