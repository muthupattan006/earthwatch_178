"""
EarthWatch - Sensor Nowcasting Engine

Reads recent sensor data from the live buffer and generates
short-term nowcasts for all supported sensor parameters.

Current sensors:
    - Temperature
    - Humidity
    - Pressure
    - Water Level
    - Water Rate
    - Soil Moisture
    - Tilt X
    - Tilt Y
    - Tilt Rate
    - MQ2 Gas

The current implementation uses a trend-based nowcasting method.
It does not require machine-learning libraries.
"""

from datetime import datetime, timedelta
from math import isfinite

from Live_data.buffer import live_buffer


# ============================================================
# SENSOR CONFIGURATION
# ============================================================

SENSOR_FIELDS = {
    "temperature": ("environment", "temperature"),
    "humidity": ("environment", "humidity"),
    "pressure": ("environment", "pressure"),

    "water_level": ("water", "level"),
    "water_rate": ("water", "rate"),

    "soil_moisture": ("soil", "moisture"),

    "tilt_x": ("ground", "tilt_x"),
    "tilt_y": ("ground", "tilt_y"),
    "tilt_rate": ("ground", "tilt_rate"),

    "mq2": ("gas", "mq2_raw"),
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_nested_value(packet, path):
    """
    Safely retrieve a nested value from a sensor packet.

    Example:
        get_nested_value(packet, ("environment", "temperature"))

    returns:
        27.4
    """

    value = packet

    try:
        for key in path:
            value = value[key]

        return value

    except (KeyError, TypeError):
        return None


def parse_timestamp(packet):
    """
    Get the timestamp stored by live_data.py.

    live_data.py adds:
        packet["_received_at"] = datetime.now().isoformat()
    """

    timestamp = packet.get("_received_at")

    if not timestamp:
        return None

    try:
        return datetime.fromisoformat(timestamp)
    except (ValueError, TypeError):
        return None


def clean_sensor_history(readings, field_path):
    """
    Extract valid timestamp/value pairs for one sensor.
    """

    result = []

    for packet in readings:

        if not isinstance(packet, dict):
            continue

        timestamp = parse_timestamp(packet)

        value = get_nested_value(packet, field_path)

        if timestamp is None:
            continue

        if value is None:
            continue

        try:
            value = float(value)
        except (ValueError, TypeError):
            continue

        if not isfinite(value):
            continue

        result.append({
            "timestamp": timestamp,
            "value": value
        })

    return result


# ============================================================
# TREND CALCULATION
# ============================================================

def calculate_linear_trend(history):
    """
    Calculate the recent trend using simple linear regression.

    Returns:
        slope

    The slope represents change in sensor value per second.
    """

    if len(history) < 2:
        return 0.0

    first_time = history[0]["timestamp"]

    x_values = []
    y_values = []

    for point in history:

        seconds = (
            point["timestamp"] - first_time
        ).total_seconds()

        x_values.append(seconds)
        y_values.append(point["value"])

    n = len(x_values)

    mean_x = sum(x_values) / n
    mean_y = sum(y_values) / n

    numerator = 0.0
    denominator = 0.0

    for x, y in zip(x_values, y_values):

        numerator += (x - mean_x) * (y - mean_y)
        denominator += (x - mean_x) ** 2

    if denominator == 0:
        return 0.0

    slope = numerator / denominator

    return slope


# ============================================================
# NOWCAST GENERATION
# ============================================================

def generate_sensor_nowcast(
    history,
    horizon_seconds=300,
    future_points=20
):
    """
    Generate a short-term nowcast for one sensor.

    Parameters:
        history:
            Recent observed sensor values.

        horizon_seconds:
            How far into the future to predict.
            Default = 5 minutes.

        future_points:
            Number of predicted points.

    Returns:
        observed data
        predicted data
    """

    if not history:
        return {
            "observed": [],
            "nowcast": []
        }

    # Calculate current trend
    slope = calculate_linear_trend(history)

    # Last observed point
    last_point = history[-1]

    last_time = last_point["timestamp"]
    last_value = last_point["value"]

    # --------------------------------------------------------
    # OBSERVED DATA
    # --------------------------------------------------------

    observed = []

    for point in history:

        observed.append({
            "timestamp": point["timestamp"].isoformat(),
            "value": round(point["value"], 4)
        })

    # --------------------------------------------------------
    # FUTURE DATA
    # --------------------------------------------------------

    nowcast = []

    interval = horizon_seconds / future_points

    for i in range(1, future_points + 1):

        seconds_ahead = interval * i

        future_time = (
            last_time +
            timedelta(seconds=seconds_ahead)
        )

        # ----------------------------------------------------
        # DAMPED TREND
        #
        # Instead of allowing the trend to explode indefinitely,
        # gradually reduce its influence as we move further
        # into the future.
        # ----------------------------------------------------

        damping = 1.0 / (
            1.0 + (seconds_ahead / horizon_seconds)
        )

        predicted_value = (
            last_value +
            slope *
            seconds_ahead *
            damping
        )

        nowcast.append({
            "timestamp": future_time.isoformat(),
            "value": round(predicted_value, 4)
        })

    return {
        "observed": observed,
        "nowcast": nowcast
    }


# ============================================================
# ALL SENSOR NOWCASTS
# ============================================================

def generate_all_nowcasts(
    readings,
    history_count=100,
    horizon_seconds=300,
    future_points=20
):
    """
    Generate nowcasts for every supported sensor.

    Returns all graphs together.
    """

    # Use only the latest readings
    recent_readings = readings[-history_count:]

    result = {}

    for sensor_name, field_path in SENSOR_FIELDS.items():

        history = clean_sensor_history(
            recent_readings,
            field_path
        )

        result[sensor_name] = generate_sensor_nowcast(
            history=history,
            horizon_seconds=horizon_seconds,
            future_points=future_points
        )

    return result


# ============================================================
# RISK INFORMATION
# ============================================================

def get_latest_risk(readings):
    """
    Extract the latest risk information from the buffer.
    """

    if not readings:
        return {
            "water": 0,
            "soil": 0,
            "tilt": 0,
            "water_rate": 0,
            "tilt_rate": 0,
            "score": 0,
            "status": "NO DATA",
            "hazard": "NONE"
        }

    latest = readings[-1]

    risk = latest.get("risk", {})

    return {
        "water": risk.get("water", 0),
        "soil": risk.get("soil", 0),
        "tilt": risk.get("tilt", 0),
        "water_rate": risk.get("water_rate", 0),
        "tilt_rate": risk.get("tilt_rate", 0),
        "score": risk.get("score", 0),
        "status": risk.get("status", "UNKNOWN"),
        "hazard": risk.get("hazard", "NONE")
    }


# ============================================================
# MAIN FUNCTION USED BY FASTAPI
# ============================================================

def get_live_nowcast(
    latitude=None,
    longitude=None,
    history_count=100,
    horizon_seconds=300,
    future_points=20
):
    """
    Get the complete nowcasting response.

    This is the function that main.py / FastAPI can call.
    """

    readings = live_buffer.get_all()

    # Generate predictions for all sensors
    sensor_nowcasts = generate_all_nowcasts(
        readings=readings,
        history_count=history_count,
        horizon_seconds=horizon_seconds,
        future_points=future_points
    )

    # Get current risk
    risk = get_latest_risk(readings)

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    response = {
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "generated_at": datetime.now().isoformat(),

        "history_count": min(
            len(readings),
            history_count
        ),

        "horizon_seconds": horizon_seconds,

        "sensors": sensor_nowcasts,

        "risk": risk
    }

    return response


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print(" EarthWatch Sensor Nowcasting")
    print("==========================================")
    print()

    readings = live_buffer.get_all()

    print(f"Readings available: {len(readings)}")

    if not readings:

        print("No sensor data available yet.")
        print("Start live_data.py first.")

    else:

        result = get_live_nowcast(
            history_count=100,
            horizon_seconds=300,
            future_points=20
        )

        print()
        print("Nowcasting generated successfully.")
        print()

        for sensor_name, data in result["sensors"].items():

            print(
                f"{sensor_name}: "
                f"{len(data['observed'])} observed, "
                f"{len(data['nowcast'])} predicted"
            )

        print()
        print("Risk:")
        print(result["risk"])