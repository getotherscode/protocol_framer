import crcmod

def get_modbus_crc16(frame: bytearray) -> bytes:
    modbus_crc16_func = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    modbus_crc16 = modbus_crc16_func(frame) & 0xFFFF
    return modbus_crc16.to_bytes(2, 'little')

def check_modbus_crc16(frame: bytes) -> bool:
    frame_len = len(frame)
    if frame_len > 2:
        crc = frame[frame_len - 1] + (frame[frame_len - 2] << 8)
        check_slice = frame[0:len(frame)-2]
        # print(f"check slice: {check_slice.hex(' ')}")

        crc_bytes = get_modbus_crc16(bytearray(check_slice))
        crc_check = crc_bytes[1] + (crc_bytes[0] << 8)
        # print(f"get crc: {crc}, check crc: {crc_check}")
        
        if crc == crc_check:
            return True
    return False

def modbus_crc16_update(data: bytearray, crc: int) -> bytes:
    for byte in data:
        crc ^= byte

        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1

    return crc & 0xFFFF