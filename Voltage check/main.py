from utils import simulate_voltage_message, voltage_diagnostic
import can
import time
from dbc_loader import load_dbc

# Load DBC once globally
db = load_dbc()

if __name__ == "__main__":
    voltages_to_test = [3.8, 4.3, 2.2, 3.95]

    with can.Bus(interface='virtual', channel='test_channel', receive_own_messages=True) as bus:
        for voltage in voltages_to_test:
            simulate_voltage_message(bus, voltage)
            time.sleep(0.2)
            voltage_diagnostic(bus, db)  # Pass dbc database to the diagnostic
