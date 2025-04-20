import smbus
import time

# MPU6050 Registers and Address
MPU_ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

# Initialize I2C (SMBus)
bus = smbus.SMBus(1)  # For RPi models with I2C-1

# Wake up the MPU6050
bus.write_byte_data(MPU_ADDR, PWR_MGMT_1, 0)

def read_raw_data(addr):
    high = bus.read_byte_data(MPU_ADDR, addr)
    low = bus.read_byte_data(MPU_ADDR, addr+1)
    value = (high << 8) | low
    if value > 32768:
        value -= 65536
    return value

while True:
    # Accelerometer values
    acc_x = read_raw_data(ACCEL_XOUT_H)
    acc_y = read_raw_data(ACCEL_XOUT_H + 2)
    acc_z = read_raw_data(ACCEL_XOUT_H + 4)

    # Gyroscope values
    gyro_x = read_raw_data(GYRO_XOUT_H)
    gyro_y = read_raw_data(GYRO_XOUT_H + 2)
    gyro_z = read_raw_data(GYRO_XOUT_H + 4)

    # Convert to g and deg/s
    Ax = acc_x / 16384.0
    Ay = acc_y / 16384.0
    Az = acc_z / 16384.0

    Gx = gyro_x / 131.0
    Gy = gyro_y / 131.0
    Gz = gyro_z / 131.0

    print(f"Accelerometer: Ax={Ax:.2f}g Ay={Ay:.2f}g Az={Az:.2f}g")
    print(f"Gyroscope:     Gx={Gx:.2f}°/s Gy={Gy:.2f}°/s Gz={Gz:.2f}°/s\n")

    time.sleep(0.5)
