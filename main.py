from depacketizer import depacketizer
from serial_transport import serial_transmit, serial_get
import crcmod
import time

PACK_SIZE       = 1024                                      # do not beyond 65535
UINT16_MAX      = 65535
UINT8_MAX       = 256

SERIAL_NAME     = "COM7"                                    # only need key words
SERIAL_BAUDRATE = 115200 
SERIAL_TIMEOUT  = 1

DEVICE_ADDR     = 9

OTA_INIT        = 1
OTA_PACK_INFO   = 2
OTA_PACK_RQST   = 3
ORA_FINISH      = 4

def main():

    my_serial = serial_get(SERIAL_NAME, SERIAL_BAUDRATE, SERIAL_TIMEOUT)

    for pack_idx, pack in depacketizer(PACK_SIZE):

        frame = bytearray()

        if DEVICE_ADDR > UINT8_MAX:
            raise ValueError(f" device id beyond {UINT16_MAX} !!! ")
        frame.append(DEVICE_ADDR)

        if OTA_PACK_RQST > UINT8_MAX:
            raise ValueError(f" cmd beyond {UINT16_MAX} !!! ")
        frame.append(OTA_PACK_RQST)

        if PACK_SIZE > UINT16_MAX:
            raise ValueError(f" pack size beyond {UINT16_MAX} !!! ")
        pack_size_high, pack_size_low = PACK_SIZE.to_bytes(2, 'big')
        frame.append(pack_size_high)
        frame.append(pack_size_low)

        if pack_idx > UINT16_MAX:
            raise ValueError(f" pack index beyond {UINT16_MAX} !!! ")
        pack_idx_high, pack_idx_low = pack_idx.to_bytes(2, 'big')
        frame.append(pack_idx_high)
        frame.append(pack_idx_low)

        frame.extend(pack)

        modbus_crc16_func = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
        modbus_crc16 = modbus_crc16_func(frame) & 0xFFFF
        crc_low, crc_high = modbus_crc16.to_bytes(2, 'little')
        frame.append(crc_low)
        frame.append(crc_high)
        
        serial_transmit(my_serial, frame)
        print(f"send pack {pack_idx}")
        time.sleep(1)

    my_serial.close()



if __name__ ==  "__main__":
    main()