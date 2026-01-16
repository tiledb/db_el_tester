from machine import Pin, SPI
import time

class MCP3208:
    def __init__(self, spi, cs_pin, vref=3.3):
        """
        Initialize MCP3208 ADC driver
        
        Args:
            spi: Initialized SPI bus instance
            cs_pin: GPIO pin for Chip Select
            vref: Reference voltage (default 3.3V)
        """
        self.spi = spi
        self.cs = Pin(cs_pin, Pin.OUT)
        self.cs.value(1)  # Deselect chip
        self.vref = vref
        
    def read_channel(self, channel):
        """
        Read a single channel (0-7)
        
        Args:
            channel: Channel number (0-7)
            
        Returns:
            tuple: (raw_value, voltage)
        """
        if not 0 <= channel <= 7:
            raise ValueError("Channel must be 0-7")

        self.cs.value(0)  # Select chip

        # Build command bytes
        byte1 = 0b00000110 | ((channel & 0b100) >> 2)
        byte2 = (channel & 0b011) << 6
        w_buf = bytearray([byte1, byte2, 0x00])
        r_buf = bytearray(3)

        self.spi.write_readinto(w_buf, r_buf)
        self.cs.value(1)  # Deselect chip

        # Extract 12-bit value
        raw_value = ((r_buf[1] & 0b00001111) << 8) | r_buf[2]
        voltage = (raw_value / 4095) * self.vref
        
        return (raw_value, voltage)
    
    def read_all_channels(self):
        """
        Read all 8 channels
        
        Returns:
            list: List of tuples (channel, raw_value, voltage) for all channels
        """
        results = []
        for ch in range(8):
            raw, voltage = self.read_channel(ch)
            results.append((ch, raw, voltage))
        return results
    
    def read_channel_raw(self, channel):
        """Read channel and return only raw value (0-4095)"""
        return self.read_channel(channel)[0]
    
    def read_channel_voltage(self, channel):
        """Read channel and return only voltage"""
        return self.read_channel(channel)[1]
    
    def validate_spi_connection(self):
        """
        Test SPI communication by sending dummy data
        
        Returns:
            bool: True if SPI communication appears functional
        """
        try:
            self.cs.value(0)
            self.spi.write(bytearray([0xFF, 0xFF]))
            data = self.spi.read(2)
            self.cs.value(1)
            return data == b'\xff\xff'  # Expect all 1s if MISO is pulled high
        except:
            return False