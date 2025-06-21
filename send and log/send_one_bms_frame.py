import os
import can

def build_bms_frame(voltage_v, temperature_c, fault_flag, status_code):
    voltage_raw = int(voltage_v * 1000)
    temp_raw = int(temperature_c * 10)
    fault_byte = 1 if fault_flag else 0
    status_byte = status_code & 0xFF

    data = (
        voltage_raw.to_bytes(2, "big") +
        temp_raw.to_bytes(2, "big", signed=True) +
        bytes([fault_byte, status_byte, 0x00, 0x00])
    )

    return can.Message(arbitration_id=0x123, data=data, is_extended_id=False)

def send_one():
    os.makedirs("logs", exist_ok=True)

    # Create bus
    bus = can.Bus(interface="virtual", channel="test_channel", receive_own_messages=True)

    # Logger
    logger = can.Logger("send and log/logs/bms_log.asc")
    notifier = can.Notifier(bus, [logger])

    voltage = 3.72
    temperature = 26.4
    fault = False
    status = 1

    msg = build_bms_frame(voltage, temperature, fault, status)

    try:
        bus.send(msg)
        print(f"Sent BMS frame on {bus.channel_info}")
        print(f"Raw data: {list(msg.data)}")
    except can.CanError as e:
        print(f"Failed to send: {e}")
    finally:
        notifier.stop()   
        bus.shutdown()    # Explicitly shutdown to avoid warning

if __name__ == "__main__":
    send_one()
