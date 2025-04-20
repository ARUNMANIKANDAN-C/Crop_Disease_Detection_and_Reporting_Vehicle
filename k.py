import smbus

bus = smbus.SMBus(1)
address = 0x68

try:
    who_am_i = bus.read_byte_data(address, 0x75)
    print(f"WHO_AM_I register: 0x{who_am_i:02X}")
except Exception as e:
    print("Failed to read from MPU6050:", e)
