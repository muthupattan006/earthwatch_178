#arduino.py
import json
import serial


# ============================================================
# CONFIGURATION
# ============================================================

SERIAL_PORT = "COM11"       # CHANGE THIS
BAUD_RATE = 115200
SERIAL_TIMEOUT = 1


# ============================================================
# ARDUINO READER
# ============================================================

class ArduinoReader:

    def __init__(
        self,
        port=SERIAL_PORT,
        baud_rate=BAUD_RATE
    ):

        self.port = port
        self.baud_rate = baud_rate
        self.timeout = SERIAL_TIMEOUT

        self.serial_connection = None


    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    def connect(self):

        try:

            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout
            )

            print(
                f"[ARDUINO] Connected to {self.port}"
            )

            return True

        except serial.SerialException as error:

            print(
                f"[ARDUINO] Connection failed: {error}"
            )

            return False


    # --------------------------------------------------------
    # READ ONE LINE
    # --------------------------------------------------------

    def read_line(self):

        if self.serial_connection is None:

            return None

        try:

            line = (
                self.serial_connection
                .readline()
                .decode(
                    "utf-8",
                    errors="ignore"
                )
                .strip()
            )

            if not line:
                return None

            return line

        except serial.SerialException as error:

            print(
                f"[ARDUINO] Serial error: {error}"
            )

            return None


    # --------------------------------------------------------
    # READ JSON PACKET
    # --------------------------------------------------------

    def read_json(self):

        line = self.read_line()

        if line is None:
            return None

        try:

            packet = json.loads(line)

            return packet

        except json.JSONDecodeError:

            print(
                "[ARDUINO] Invalid JSON:"
            )

            print(line)

            return None


    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    def close(self):

        if self.serial_connection is not None:

            self.serial_connection.close()

            self.serial_connection = None

            print(
                "[ARDUINO] Connection closed"
            )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    reader = ArduinoReader()

    if reader.connect():

        print(
            "[ARDUINO] Waiting for sensor data..."
        )

        try:

            while True:

                packet = reader.read_json()

                if packet is not None:

                    print(
                        "[ARDUINO DATA]"
                    )

                    print(packet)

        except KeyboardInterrupt:

            print(
                "\nStopping Arduino reader..."
            )

        finally:

            reader.close()