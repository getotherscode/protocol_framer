import crcmod

def get_modbus_crc16(frame: bytearray) -> bytes:
    modbus_crc16_func = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    modbus_crc16 = modbus_crc16_func(frame) & 0xFFFF
    return modbus_crc16.to_bytes(2, 'little')

def check_modbus_crc16(frame: bytes) -> bool:
    frame_len = len(frame)
    if frame_len > 2:
        crc = (frame[frame_len - 1] << 8) + frame[frame_len - 2]
        crc_check = get_modbus_crc16(bytearray(frame))
        if crc == crc_check:
            return True
    return False