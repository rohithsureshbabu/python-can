import can
import time
import pandas as pd

def bms_test(voltage, current, temp1, temp2, soc):
    """Simulate BMS fault detection for fast charging conditions - overvoltage, overcurrent, overtemperature"""
    faults = []
    messages = []
    
    # Overvoltage check (>4.2V)
    if voltage > 4.2:
        faults.append(f"Overvoltage: {voltage}V")
        messages.append({"id": 0x201, "data": [0x01], "fault": "Overvoltage"})
    else:
        messages.append({"id": 0x201, "data": [0x00], "fault": "None"})

    # Overcurrent check (>±30 A) (Both Directions)
    if abs(current) > 30:
        faults.append(f"Overcurrent: {current}A")
        messages.append({"id": 0x204, "data": [0x03], "fault": "Overcurrent"})
    else:
        messages.append({"id": 0x204, "data": [0x00], "fault": "None"})

    # Overtemperature or asymmetry check (>60°C or >7°C diff)
    if temp1 > 60 or temp2 > 60 or abs(temp1 - temp2) > 7:
        faults.append(f"Overtemperature: {temp1}°C, {temp2}°C, Diff: {abs(temp1-temp2)}°C")
        messages.append({"id": 0x202, "data": [0x02], "fault": "Overtemperature"})
    else:
        messages.append({"id": 0x202, "data": [0x00], "fault": "None"})

    return messages, faults

# Connect to virtual CAN 
try:
    bus = can.Bus(channel='vcan0', interface='virtual')
except:
    print("Using mock bus for demo")
    bus = None

test_cases = [
    {
        "test_id": "TC_BMS_FAST_001",
        "voltage": 3.7,
        "current": 20,
        "temp1": 40,
        "temp2": 41,
        "soc": 50,
        "expected": [{"id": 0x201, "data": [0x00]}, {"id": 0x204, "data": [0x00]}, {"id": 0x202, "data": [0x00]}]
    },
    {
        "test_id": "TC_BMS_FAST_002",
        "voltage": 4.3,
        "current": 25,
        "temp1": 50,
        "temp2": 50,
        "soc": 90,
        "expected": [{"id": 0x201, "data": [0x00]}, {"id": 0x204, "data": [0x00]}, {"id": 0x202, "data": [0x00]}]
    },
    {
        "test_id": "TC_BMS_FAST_003",
        "voltage": 4.0,
        "current": 35,
        "temp1": 55,
        "temp2": 55,
        "soc": 80,
        "expected": [{"id": 0x201, "data": [0x00]}, {"id": 0x204, "data": [0x03]}, {"id": 0x202, "data": [0x00]}]
    },
    {
        "test_id": "TC_BMS_FAST_004",
        "voltage": 4.0,
        "current": 20,
        "temp1": 65,
        "temp2": 57,
        "soc": 85,
        "expected": [{"id": 0x201, "data": [0x00]}, {"id": 0x204, "data": [0x00]}, {"id": 0x202, "data": [0x02]}]
    }
]

# Execute tests
results = []
for test in test_cases:
    messages, faults = bms_test(test["voltage"], test["current"], test["temp1"], test["temp2"], test["soc"])
    status = "Pass" if all(msg["data"] == exp["data"] for msg, exp in zip(messages, test["expected"])) else "Fail"
    results.append({
        "Test ID": test["test_id"],
        "Voltage (V)": test["voltage"],
        "Current (A)": test["current"],
        "Temp1 (°C)": test["temp1"],
        "Temp2 (°C)": test["temp2"],
        "SOC (%)": test["soc"],
        "Faults": "; ".join(faults) if faults else "None",
        "Status": status
    })
    if bus:
        for msg in messages:
            can_msg = can.Message(arbitration_id=msg["id"], data=msg["data"], is_extended_id=False)
            bus.send(can_msg)
    time.sleep(0.1)

# Save report
df = pd.DataFrame(results)
df.to_csv("BMS fault check/bms_fast_charge_test_report.csv", index=False)
if bus:
    bus.shutdown()
