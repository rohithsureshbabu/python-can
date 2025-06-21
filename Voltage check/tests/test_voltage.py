import pytest
from utils import convert_voltage_from_bytes

@pytest.mark.parametrize("data_bytes,expected_voltage", [
    (b'\x0F\xA0', 4.0),     # 4000 mV
    (b'\x0B\xB8', 3.0),     # 3000 mV
    (b'\x10\x68', 4.2),     # 4200 mV
])
def test_voltage_conversion(data_bytes, expected_voltage):
    assert convert_voltage_from_bytes(data_bytes) == pytest.approx(expected_voltage, 0.01)
