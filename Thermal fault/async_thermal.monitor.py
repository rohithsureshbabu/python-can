import asyncio
import can
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from can.notifier import MessageRecipient

# --- Logging setup ---
logging.basicConfig(
    filename="Thermal fault/logs/async_thermal.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Thermal thresholds (°C)
TEMP_MIN = 0    
TEMP_MAX = 60 
SCALING = 10     # 0.1°C resolution: 250 = 25.0°C

def decode_temperature(data: bytes) -> float:
    """Convert 2-byte temperature value (0.1 °C resolution) to float."""
    raw = int.from_bytes(data[:2], byteorder="big", signed=True)
    return raw / SCALING

def print_temperature(msg: can.Message) -> None:
    temp = decode_temperature(msg.data)
    print(f"Received Temp: {temp:.1f} °C (ID: 0x{msg.arbitration_id:X})")

    if temp < TEMP_MIN or temp > TEMP_MAX:
        warning = f"Thermal fault: {temp:.1f} °C"
        print(warning)
        logging.warning(warning)
    else:
        logging.info(f"Temperature OK: {temp:.1f} °C")

async def temperature_simulator(bus: can.Bus) -> None:
    """Sends a range of normal and fault temperatures to simulate thermal behavior."""
    import random

    print("Simulating thermal profile...")
    for _ in range(12):
        simulated_temp = random.choice([22.5, 35.0, 59.9, -5.0, 65.5])  # mixed healthy + fault
        raw = int(simulated_temp * SCALING)
        data = raw.to_bytes(2, byteorder="big", signed=True) + b'\x00' * 6  # total 8 bytes
        msg = can.Message(arbitration_id=0x200, data=data, is_extended_id=False)
        try:
            bus.send(msg)
            logging.info(f"Sent temperature: {simulated_temp:.1f} °C")
        except can.CanError as e:
            logging.error(f"Send failed: {e}")
        await asyncio.sleep(0.4)

async def main() -> None:
    with can.Bus(interface="virtual", channel="thermal_channel", receive_own_messages=True) as bus:
        reader = can.AsyncBufferedReader()
        logger = can.Logger("Thermal fault/logs/thermal_capture.asc")

        listeners: list[MessageRecipient] = [
            print_temperature,
            reader,
            logger,
        ]

        notifier = can.Notifier(bus, listeners, loop=asyncio.get_running_loop())
        try:
            await temperature_simulator(bus)
            # Optionally, process buffered CAN traffic
            while True:
                msg = await reader.get_message()
                print(f"[Buffered] ID: {msg.arbitration_id:X}")
                await asyncio.sleep(0.1)

        finally:
            notifier.stop()

if __name__ == "__main__":
    asyncio.run(main())
