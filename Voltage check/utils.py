import can
import logging
import os

# Create logs directory 
os.makedirs("logs", exist_ok=True)

# Voltage validation settings 
VOLTAGE_MIN = 2.5  
VOLTAGE_MAX = 4.2 
SCALING = 1000     # Conversion factor: volts <-> millivolts

# Configure logging 
logging.basicConfig(
    filename="Voltage check/logs/voltage.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def simulate_voltage_message(bus, voltage):

    raw = int(voltage * SCALING)  
    data = raw.to_bytes(2, byteorder="big")  # Encode as 2 bytes
    msg = can.Message(arbitration_id=0x101, data=data, is_extended_id=False)

    try:
        bus.send(msg)
        logging.info(f"Sent voltage: {voltage:.3f} V")
    except can.CanError as e:
        logging.error(f"Send failed: {e}")

def convert_voltage_from_bytes(data):
    """
    Converts 2-byte CAN data to float voltage.
    """
    raw = int.from_bytes(data[:2], byteorder="big")
    return raw / SCALING

def voltage_diagnostic(bus, dbc=None):
    """
    Receives one CAN message and validates the voltage.
    Optionally decodes using DBC if provided.
    """
    msg = bus.recv(timeout=1.0)
    if msg is None:
        print("No CAN message received.")
        logging.warning("No CAN message received.")
        return

    voltage = convert_voltage_from_bytes(msg.data)
    print(f"Received voltage: {voltage:.3f} V")
    logging.info(f"Received voltage: {voltage:.3f} V")

    if not (VOLTAGE_MIN <= voltage <= VOLTAGE_MAX):
        warning = f"Voltage out of range: {voltage:.3f} V"
        print(warning)
        logging.warning(warning)

    if dbc:
        try:
            decoded = dbc.get_message_by_frame_id(msg.arbitration_id).decode(msg.data)
            print("Decoded DBC values:", decoded)
        except Exception as e:
            logging.warning(f"DBC decoding failed: {e}")
