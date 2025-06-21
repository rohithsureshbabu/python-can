import can
import time

def setup_can_bus():
    """Initialize a virtual CAN bus"""
    try:
        bus = can.Bus(channel='vcan0', interface='virtual')
        print("Connected to virtual CAN bus (vcan0)")
        return bus
    except Exception as e:
        print(f"Failed to connect to CAN bus: {e}")
        return None

def encode_voltage_mV(voltage):
    """Convert voltage in V to 2-byte integer big endian representation."""
    mV = int(voltage * 1000)
    return [(mV >> 8) & 0xFF, mV & 0xFF]

def get_fault_code(voltage):
    """Return fault code based on voltage level."""
    if voltage > 4.2:
        return 0x01  # Overvoltage
    elif voltage < 3.0:
        return 0x02  # Undervoltage
    else:
        return 0x00  # No fault

def main():
    bus = setup_can_bus()
    if not bus:
        return

    # Simulate voltages (in volts)
    voltages = [3.7, 4.3, 2.9, 4.0, 3.2] 

    print("Starting CAN fault simulation...")
    try:
        for i, v in enumerate(voltages):
            voltage_data = encode_voltage_mV(v)
            fault_code = get_fault_code(v)

            msg_voltage = can.Message(arbitration_id=0x200, data=voltage_data + [0x00]*6, is_extended_id=False)
            msg_fault = can.Message(arbitration_id=0x201, data=[fault_code] + [0x00]*7, is_extended_id=False)

            bus.send(msg_voltage)
            bus.send(msg_fault)

            print(f"[{i+1}] Voltage={v:.2f}V | Fault=0x{fault_code:02X}")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Interrupted.")

    finally:
        bus.shutdown()
        print("CAN bus shutdown complete.")

if __name__ == "__main__":
    main()
