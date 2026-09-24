# ============================================================
# EarthWatch - Live Data Handler
# ============================================================
#
# Arduino  -->  arduino.py (ArduinoReader)
#                   |
#                   v
#            live_data.py (background thread)
#                   |
#                   v
#            buffer.py (LiveBuffer)
#                   |
#                   v
#            Dashboard / API
#
# This file is intentionally thin: it owns NO buffer and NO
# serial-connection logic of its own. It just runs
# arduino.py's reader in a background thread and pushes
# whatever it returns into buffer.py's live_buffer.
# ============================================================

import threading
import time
from datetime import datetime

from Live_data.arduino_reader import ArduinoReader
from Live_data.buffer import live_buffer


# ============================================================
# LIVE DATA CONTROLLER
# ============================================================

class LiveDataController:

    def __init__(self, port=None, baud_rate=None):

        # Only override arduino.py's defaults if explicitly passed
        kwargs = {}
        if port is not None:
            kwargs["port"] = port
        if baud_rate is not None:
            kwargs["baud_rate"] = baud_rate

        self.reader = ArduinoReader(**kwargs)

        self.running = False
        self.reader_thread = None

    # --------------------------------------------------------
    # Process one JSON packet from the Arduino
    # --------------------------------------------------------

    def process_packet(self, packet):

        if not isinstance(packet, dict):
            return False

        # ----------------------------------------------------
        # Ignore Arduino startup/status messages
        # Example: {"status":"system_ready", "device_id":"NODE_01"}
        # ----------------------------------------------------

        if "status" in packet and "risk" not in packet:

            print(f"[ARDUINO STATUS] {packet.get('status')}")

            return False

        # ----------------------------------------------------
        # Add Python-side reception timestamp
        # ----------------------------------------------------

        packet["_received_at"] = datetime.now().isoformat()

        # ----------------------------------------------------
        # Add reading to the shared buffer
        # ----------------------------------------------------

        live_buffer.add(packet)
        print(f"[WINDOW] size={live_buffer.size()} latest={live_buffer.latest()}")

        print(
            f"[BUFFER] "
            f"readings={live_buffer.size()} "
            f"risk={packet.get('risk', {}).get('score', 'N/A')} "
            f"status={packet.get('risk', {}).get('status', 'N/A')}"
        )

        return True

    # --------------------------------------------------------
    # Background read loop
    # --------------------------------------------------------

    def read_loop(self):

        self.running = True

        while self.running:

            packet = self.reader.read_json()

            if packet is not None:
                self.process_packet(packet)

            # read_json() already blocks up to SERIAL_TIMEOUT via
            # readline(), so no extra sleep needed here. If the
            # serial connection drops, arduino.py's read_line()
            # catches SerialException and returns None, so this
            # loop keeps running rather than crashing - reconnect
            # logic can be added in arduino.py if you deploy this
            # unattended in the field.

    # --------------------------------------------------------
    # Start
    # --------------------------------------------------------

    def start(self):

        if not self.reader.connect():
            return False

        if self.running:
            print("Live data reader is already running.")
            return True

        # Arduino boards often reset when Serial opens
        time.sleep(2)

        self.reader_thread = threading.Thread(
            target=self.read_loop,
            daemon=True
        )
        self.reader_thread.start()

        print("Live data reader started.")

        return True

    # --------------------------------------------------------
    # Stop
    # --------------------------------------------------------

    def stop(self):

        self.running = False

        if self.reader_thread is not None:
            self.reader_thread.join(timeout=2)

        self.reader.close()

        print("Live data reader stopped.")


# ============================================================
# GLOBAL CONTROLLER
# ============================================================

controller = LiveDataController()


# ============================================================
# PUBLIC FUNCTIONS
# (same names as before, so nothing else in your project breaks)
# ============================================================

def start_live_data():
    """Start Arduino -> Serial -> Buffer pipeline."""
    return controller.start()


def stop_live_data():
    """Stop Arduino live-data reader."""
    controller.stop()


def get_latest_data():
    """Return the newest Arduino reading."""
    return live_buffer.latest()


def get_live_history(count=100):
    """Return the latest N readings."""
    return live_buffer.get_latest(count)


def get_buffer_size():
    """Return number of readings currently stored."""
    return live_buffer.size()


def clear_live_buffer():
    """Clear all stored live readings."""
    live_buffer.clear()


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    print()
    print("Starting EarthWatch live-data system...")
    print()

    started = start_live_data()

    if not started:

        print("Live-data system could not start.")

    else:

        try:

            while True:
                time.sleep(1)

        except KeyboardInterrupt:

            print()
            print("Stopping EarthWatch live-data system...")

            stop_live_data()