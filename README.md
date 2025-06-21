Here are some examples of how I practised python-can library in various examples
# [Voltage data CAN communication](./Voltage%20check/)

### **Goal**

> I'm simulating and testing how a Battery Management System (BMS) would send voltage data over the CAN bus. I want to:
>
> * Send voltage readings via CAN (like 3.8 V or 4.3 V)
> * Receive those messages
> * Check whether the voltages are within a safe range (2.5 V to 4.2 V)
> * Optionally decode them using a DBC if needed

---

### **What I Did (Step-by-Step)**

#### 1. **Set Up the Environment**

Since I don't have admin rights to use `vcan0`, I used `python-can`’s `virtual` interface. It lets me simulate a CAN bus fully in Python without hardware or root permissions.

```python
can.Bus(interface='virtual', channel='test_channel', receive_own_messages=True)
```

This creates a virtual bus I can both send to and listen from.

---

#### 2. **Built a Sender Function**

In `utils.py`, I wrote `simulate_voltage_message(bus, voltage)`:

> I take a floating-point voltage (e.g., 3.8 V), convert it to an integer in millivolts (e.g., 3800), and send it on the CAN bus encoded as 2 bytes.

That simulates a real battery sensor broadcasting data over the network.

---

#### 3. **Built a Receiver & Diagnostic Function**

Then I wrote `voltage_diagnostic(bus)`:

> I listen for a message, decode the voltage value from the two bytes, and check if it's between 2.5 and 4.2 V.

If the voltage is outside the range, I log a warning and print something like:

```text
Voltage out of range: 4.300 V
```

Otherwise, I just log the received value.

---

#### 4. **Logged Everything**

I added `logging.basicConfig(...)` to log everything to `logs/voltage.log` so I could trace the test history, especially any failures.

Before configuring the logger, I made sure the `logs/` folder exists:

```python
os.makedirs("logs", exist_ok=True)
```

---

#### 5. **Ran All of It in `main.py`**

In `main.py`, I listed a few voltages to test:

```python
voltages_to_test = [3.8, 4.3, 2.2, 3.95]
```

> I loop over them, send each as a CAN message, and run the diagnostic right after. I added a small delay between sends.

```python
for voltage in voltages_to_test:
    simulate_voltage_message(bus, voltage)
    time.sleep(0.2)
    voltage_diagnostic(bus)
```

---

#### 6. **Integrated DBC Decoding**

I wrote a `dbc_loader.py` to load a DBC file and decode the message using `cantools`. The code checks:

> “If a DBC is available, decode the raw CAN data into signal values (like Voltage: 3.8 V).”

This helps later if I have a full BMS message with multiple signals.

---

### **What It Achieves**

> I now have a modular Python-based test system that:

* Simulates a battery sending voltage over CAN
* Validates the message against safety rules
* Logs results
* Is future-proof for decoding via DBC


# [CAN Fault Simulation Script](./CAN%20Voltage%20fault%20check)

### **What I'm Doing**

I'm simulating how a **Battery Management System (BMS)** would behave on a CAN bus, especially how it handles **voltage signals** and **fault codes** like overvoltage or undervoltage.

Since I don't have real hardware, I'm using a **virtual CAN bus** in Python to test the logic.

---

### **How I Structured It**

I broke the script into clean, modular functions for clarity and reuse.

---

### 1. `setup_can_bus()`

This sets up a **virtual CAN interface** (`vcan0`) using `python-can`.
Even though there’s no real hardware, it behaves like a real CAN bus so I can send and receive messages just for testing.

```python
bus = can.Bus(channel='vcan0', interface='virtual')
```

If setup fails, I return `None` and skip the simulation.

---

### 2. `encode_voltage_mV(voltage)`

This function takes a voltage in volts (like 3.7 V) and converts it to **millivolts** (e.g., 3700 mV), then **encodes it into two bytes** (big-endian).

Why? Because most real CAN protocols send voltages as raw integer data, not floats.

---

### 3. `get_fault_code(voltage)`

Here I define my **fault logic**:

* Voltage > 4.2 V → overvoltage → fault code `0x01`
* Voltage < 3.0 V → undervoltage → fault code `0x02`
* Otherwise → everything's normal → code `0x00`

It’s just a simplified version of a typical BMS decision-making rule.

---

### 4. `main()`

This is where I pull it all together:

* I create a list of **test voltages**: some normal, some faulty
* For each voltage:

  * I encode the voltage
  * I get the fault code
  * I send **two CAN messages**:

    * One with the voltage data (on ID `0x200`)
    * One with the fault code (on ID `0x201`)
  * I print out what I just sent, for visibility

I also add a small `0.5s` delay between messages to simulate a real-time flow.

If I hit `Ctrl+C`, it gracefully shuts down the CAN bus.

---

### **Sample Output Looks Like**

```bash
[1] Voltage=3.70V | Fault=0x00
[2] Voltage=4.30V | Fault=0x01
[3] Voltage=2.90V | Fault=0x02
```

---

### **Why I Wrote It This Way**

* It’s modular — I can reuse the fault code logic or voltage encoder in other scripts.
* It simulates what a real BMS would do in response to sensor data.
* I can extend this easily to include current, temperature, etc.
* It’s a great way to **test logic before touching real ECUs or HIL systems**.


# [Asynchronous thermal fault moitoring script](./Thermal%20fault)
### **What I'm Doing**

> I built an **asynchronous Python tool** to simulate and monitor **thermal data over a virtual CAN bus**. It mimics how a Battery Management System (BMS) or ECU might send and log **temperature signals**, and how the software should react when those values go out of bounds — like overheating or undercooling.

This is great for testing thermal fault handling logic in a real-time, non-blocking way using `asyncio`.

---

### **How I Structured the Code**

---

#### Logging Setup

Right at the top, I set up logging to a file:

```python
logging.basicConfig(
    filename="Thermal fault1/logs/async_thermal.log",
    ...
)
```

> This keeps a record of all temperature events, including faults, in a persistent log.

---

#### Thresholds

I defined a **normal range** for operating temperatures:

```python
TEMP_MIN = 0      # Anything below = undercooling
TEMP_MAX = 60     # Anything above = overheating
```

The temperature is encoded in **tenths of a degree** (like 250 = 25.0°C), so I set:

```python
SCALING = 10
```

---

#### `decode_temperature()` and `print_temperature()`

I wrote a function to **decode 2-byte signed temperature data**, and another to:

* Print it out
* Check if it’s within the safe range
* Log warnings if it’s not

> If the temp is outside the range, I print and log:

```text
Thermal fault: 65.5 °C
```

---

#### `temperature_simulator()`

This function **generates fake thermal readings** and sends them on the CAN bus.

```python
simulated_temp = random.choice([22.5, 35.0, 59.9, -5.0, 65.5])
```

So some are safe, and others deliberately cause thermal faults. I encode each as 2 bytes (with padding to 8 bytes), and send it on ID `0x200`.

> I added a small delay with `await asyncio.sleep(0.4)` to space out the messages.

---

#### `main()` Function

This is where everything connects:

* I create a **virtual CAN bus** called `"thermal_channel"`
* I set up three asynchronous listeners:

  * `print_temperature` → shows + logs decoded temperatures
  * `AsyncBufferedReader()` → stores received messages
  * `Logger(...)` → writes to a `.asc` log file (common in CAN tools)

These listeners are registered to a `Notifier`, which handles incoming messages asynchronously using Python's `asyncio` event loop.

Then I run the `temperature_simulator()` and keep listening for messages indefinitely.

---

### **What This Achieves**

* I'm **generating realistic CAN thermal messages** in a non-blocking way.
* I’m **detecting faults live**, and logging them.
* The tool could be connected to other test systems or used in CI to check for thermal fault handling.


# [Test Automation](./Test%20Automation/)

## **What I'm Doing**

> I wrote a Python-based test automation script to simulate and validate **basic BMS overvoltage detection logic**. This version encodes the input voltage using **millivolt scaling** and constructs a proper **8-byte CAN frame**, just like a real embedded system would.
>
> The test sends the frame over a **virtual CAN bus**, evaluates the logic, and outputs a CSV report summarizing each test case's results.

---

### **How It Works — Step by Step**

---

#### `bms_test(voltage)`

This function simulates the logic that a real BMS might use to determine if an overvoltage fault should be raised.

* I first **encode the voltage** in millivolts as 2 bytes (big endian)
* If the voltage is over 4.2 V, I set **fault byte = `0x01`**
* The full CAN payload is then packed as:

  ```
  [voltage_MSB, voltage_LSB, fault_flag, 0x00, 0x00, 0x00, 0x00, 0x00]
  ```

This structure mirrors what you'd expect from a production-grade ECU communicating over CAN.

---

#### CAN Bus Setup

I use `python-can` to connect to a virtual CAN interface:

```python
bus = can.Bus(channel='vcan0', interface='virtual')
```

If that fails (due to permissions or missing setup), I skip sending CAN messages but still run the logic and report.

---

#### Test Cases

Each test case defines:

* a test ID (for traceability)
* an input voltage
* the **expected fault flag value** (not full CAN data anymore)

Example:

```python
{"test_id": "TC_BMS_OV_003", "voltage": 4.3, "expected_fault": 0x01}
```

So I can now evaluate just the **fault byte** (byte index 2 in the 8-byte payload), which reflects how actual diagnostics systems compare DTC flags.

---

#### Running the Tests

For every test case:

1. I generate the simulated CAN message using `bms_test()`
2. Extract the **fault byte** (byte 2)
3. Compare it against the expected fault code
4. Store the result as Pass/Fail

If the virtual bus is working, I send the message over CAN as part of the simulation.

---

#### Saving the Results

I write the result of each test into a CSV report:

```python
Test Automation/bms_test_report.csv
```

Each row includes:

* Test ID
* Input voltage
* Expected fault flag (hex)
* Actual fault flag (hex)
* Test outcome

This output is clean, version-controlled, and easily usable in CI or QA pipelines.



# [BMS frame construction and logging](./send%20and%20log/)

Here’s how I would explain this **BMS Frame Construction and Logging Script** in simple, first-person terms — like I’m walking through it in an interview or showing a teammate.

---

### **What I'm Doing**

> I’m simulating how a Battery Management System (BMS) would construct and send a full **diagnostic CAN frame**, which includes:

* voltage
* temperature
* a fault flag
* a status code

I then send that frame over a **virtual CAN bus**, and I log it in an `.asc` file — the same format tools like Vector CANalyzer or CANoe use.

---

### **Breakdown of How It Works**

---

#### `build_bms_frame(...)`

This function builds a properly structured CAN message. It takes in four inputs:

* `voltage_v`: the battery voltage (e.g., 3.72 V)
* `temperature_c`: battery temp (e.g., 26.4 °C)
* `fault_flag`: a boolean for whether a fault exists
* `status_code`: an 8-bit status number (could mean charging, idle, etc.)

Here's how each field gets packed:

* Voltage is multiplied by 1000 → stored in 2 bytes (millivolts)
* Temperature is scaled to 0.1 °C and stored in 2 bytes (signed)
* Fault flag becomes a single byte: `0x00` or `0x01`
* Status is one byte
* I pad the rest with zeros to make the total data **8 bytes** (required for CAN)

So it builds a message like:

```python
[0x0E, 0x88, 0x01, 0x08, 0x00, 0x01, 0x00, 0x00]
```

---

#### `send_one()`

This is the main function. It does a few things:

1. **Creates a `logs/` folder** if it doesn't exist
2. **Sets up a virtual CAN bus** on `test_channel`
3. Initializes a CAN **Logger** to capture everything sent and write it into:

   ```
   send and log/logs/bms_log.asc
   ```
4. Sends a **single message** with sample values:

   * Voltage = `3.72 V`
   * Temp = `26.4 °C`
   * Fault = `False`
   * Status = `1` (could mean “operational” or “charging” etc.)
5. Prints:

   * Confirmation of the send
   * Raw byte data for visibility
6. Cleanly **stops the notifier** and **shuts down the bus** (important to prevent background threads from hanging)

---

### **What This Demonstrates**

> This shows how I can:

* Construct real-world CAN payloads using signal scaling and byte packing
* Use `python-can` to send data over a test interface
* Log the traffic in `.asc` format — something test tools or diagnostics software can parse
* Clean up resources properly (e.g., `notifier.stop()`, `bus.shutdown()`)

This is a mini example of what a BMS would do internally — assemble sensor readings, encode them, and broadcast them cyclically or event-based.



# [BMS fast-charging safety test script](./BMS%20fault%20check/)

Here’s how I would explain this **BMS fast-charging safety test script** in a clear, human, first-person way — just like I’d do in an interview or when presenting it to a colleague:

---

### **What I'm Doing**

> I built a Python test harness to simulate and verify how a **Battery Management System (BMS)** detects faults under **fast charging conditions**. The script checks key safety parameters — voltage, current, and temperature — and ensures the BMS logic raises the correct fault flags when thresholds are violated.

---

### **Step-by-Step Walkthrough**

---

#### 🔹 `bms_test(...)`

This function contains the **core BMS logic** I want to simulate and test. I check:

1. **Overvoltage**: If the voltage is > 4.2 V, raise fault code `0x01`
2. **Overcurrent**: If the current is over ±30 A, raise `0x03`
3. **Overtemperature or thermal asymmetry**:

   * If any temp is > 60 °C
   * Or if the temp difference between two cells is > 7 °C
     → then raise fault code `0x02`

Each condition adds an entry to:

* `faults`: a list of fault descriptions
* `messages`: a list of CAN messages that represent fault responses

---

#### Virtual CAN Setup

I use `python-can` to connect to a **virtual CAN interface**:

```python
bus = can.Bus(channel='vcan0', interface='virtual')
```

If it fails (e.g., no vcan support), I print a fallback message and skip sending.

---

#### Test Case Definitions

I defined **four test scenarios** inspired by real-world fast-charging conditions — some pass, some intentionally trigger faults.

Each test has:

* A `test_id` (for traceability)
* Inputs: voltage, current, temp1, temp2, SOC
* `expected` output: what fault codes should be raised in each of the 3 monitored categories (voltage, current, temperature)

---

#### Test Execution Loop

For each test:

1. I call `bms_test()` with the test inputs
2. I compare the actual `data` in each message to the expected output
3. I classify the test as `"Pass"` or `"Fail"` based on match
4. If a CAN bus is active, I send all the fault messages (ID + data)

This mimics how we’d verify firmware behavior for safety in early-stage BMS software testing.

---

#### Logging and Reporting

Finally, I collect all the test results into a list of dictionaries and convert it to a **CSV test report** using `pandas`:

```python
df.to_csv("BMS fault check/bms_fast_charge_test_report.csv", index=False)
```

The report contains:

* All inputs
* Detected faults (if any)
* Test outcome (Pass/Fail)

---

### **What This Shows**

> This script is a small, testable simulation of what a BMS safety module might do during fast charging. It shows I can:

* Implement safety logic based on field measurements
* Wrap that logic into test cases
* Automate test execution and logging
* Integrate the logic with CAN messaging for traceability or real-system interaction



