import can
import time
import csv

# Simulate voltage encoding as 2 bytes (millivolts)
def encode_voltage(voltage_v):
    voltage_mV = int(voltage_v * 1000)
    return voltage_mV.to_bytes(2, byteorder="big")

def bms_test(voltage):
    """Simulate BMS fault detection based on voltage."""
    voltage_bytes = encode_voltage(voltage)

    if voltage > 4.2:
        fault_flag = 0x01  # Overvoltage bit set
    else:
        fault_flag = 0x00

    # Construct 8-byte CAN dataframe:
    # Byte 0-1: voltage (mV)
    # Byte 2: fault flag
    # Byte 3-7: reserved
    data = voltage_bytes + bytes([fault_flag]) + bytes(5)
    return {
        "id": 0x201,
        "data": data,
        "fault": "Overvoltage" if fault_flag else "None"
    }

# Set up CAN bus (virtual)
try:
    bus = can.Bus(channel='vcan0', interface='virtual')
    print("Connected to virtual CAN bus.")
except:
    print("Using mock bus for demo.")
    bus = None

# Define test cases
test_cases = [
    {"test_id": "TC_BMS_OV_001", "voltage": 3.7, "expected_fault": 0x00},
    {"test_id": "TC_BMS_OV_002", "voltage": 4.2, "expected_fault": 0x00},
    {"test_id": "TC_BMS_OV_003", "voltage": 4.3, "expected_fault": 0x01},
]

# Run tests
results = []
for test in test_cases:
    result = bms_test(test["voltage"])
    actual_fault_flag = result["data"][2]  # Byte 2 contains the fault as per template
    status = "Pass" if actual_fault_flag == test["expected_fault"] else "Fail"

    results.append({
        "Test ID": test["test_id"],
        "Voltage (V)": test["voltage"],
        "Expected Fault": hex(test["expected_fault"]),
        "Actual Fault": hex(actual_fault_flag),
        "Status": status
    })

    if bus:
        msg = can.Message(arbitration_id=result["id"], data=result["data"], is_extended_id=False)
        bus.send(msg)
    time.sleep(0.1)

# Save report
with open("Test Automation/bms_test_report.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["Test ID", "Voltage (V)", "Expected Fault", "Actual Fault", "Status"])
    writer.writeheader()
    writer.writerows(results)

if bus:
    bus.shutdown()
