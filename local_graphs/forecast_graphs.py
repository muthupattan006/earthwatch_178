import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "output"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# SHARED STYLE (used by both graphs so layout stays consistent
# and doesn't get duplicated per-graph)
# ============================================================

AXIS_STYLE = dict(
    showgrid=True,
    gridcolor="#e9edf3",
    showline=True,
    linecolor="#c9d2de",
    mirror=True,
    zeroline=False
)

TICK_FORMAT = "%d%b %H:%M"   # -> "19Sep 05:30"


def _padded_range(series, pad_ratio=0.15, floor_at_zero=False):
    """
    Compute a tight y-axis range around the data instead of
    always starting at 0 (matches the target graph style).

    floor_at_zero=True is used for bar-type data (e.g. rainfall)
    where the baseline should stay at 0.
    """

    data_min = float(series.min())
    data_max = float(series.max())

    span = data_max - data_min

    if span == 0:
        span = 1.0

    pad = span * pad_ratio

    low = 0 if floor_at_zero else data_min - pad
    high = data_max + pad

    return [low, high]


def _apply_common_layout(fig, y_range, legend_title=None):
    """
    Applies the shared "no heading, tight grid, bordered plot"
    layout to a figure. Does NOT set a title -- headings are
    intentionally not rendered on these graphs.
    """

    fig.update_layout(

        title=None,

        xaxis=dict(
            title="",
            tickformat=TICK_FORMAT,
            tickangle=-45,
            **AXIS_STYLE
        ),

        yaxis=dict(
            title="",
            range=y_range,
            **AXIS_STYLE
        ),

        hovermode="closest",

        template="plotly_white",

        plot_bgcolor="white",

        height=500,

        margin=dict(
            l=55,
            r=25,
            t=45,
            b=90
        ),

        showlegend=True,

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )


PLOTLY_CONFIG = {
    "responsive": True,
    "displaylogo": False,
    "scrollZoom": True,
    "modeBarButtonsToRemove": [
        "lasso2d",
        "select2d"
    ]
}


# ============================================================
# TEMPERATURE FORECAST
# ============================================================

def import_temperature_forecast_data():
    """
    Real temperature forecast data entry point.

    Returns:
        pandas.DataFrame -> if actual data is available
        None             -> if actual data is unavailable

    NOTE: not connected yet. Do not assume a source/schema here
    until one has actually been provided.
    """

    return None


def get_simulated_temperature_data():

    data = {

        "Time_stamp": [
            "2026-09-21 05:30", "2026-09-21 08:30", "2026-09-21 11:30",
            "2026-09-21 14:30", "2026-09-21 17:30", "2026-09-21 20:30",
            "2026-09-21 23:30", "2026-09-22 02:30", "2026-09-22 05:30",
            "2026-09-22 08:30", "2026-09-22 11:30", "2026-09-22 14:30",
            "2026-09-22 17:30", "2026-09-22 20:30", "2026-09-22 23:30",
            "2026-09-23 02:30", "2026-09-23 05:30", "2026-09-23 08:30",
            "2026-09-23 11:30", "2026-09-23 14:30", "2026-09-23 17:30",
            "2026-09-23 20:30", "2026-09-23 23:30", "2026-09-24 02:30",
            "2026-09-24 05:30"
        ],

        "Temperature": [
            18.7, 21.5, 23.0, 23.9, 21.3, 20.4, 19.9,
            19.4, 19.3, 19.6, 25.0, 25.5, 21.2, 19.9, 17.9,
            16.5, 16.2, 19.7, 23.9, 23.4, 19.9, 17.4, 17.7,
            17.3, 17.0
        ]
    }

    df = pd.DataFrame(data)

    df["Time_stamp"] = pd.to_datetime(df["Time_stamp"])

    return df


def get_temperature_data():

    print("\nAttempting to import actual temperature forecast data...")

    actual_data = import_temperature_forecast_data()

    if actual_data is not None:
        print("Actual temperature forecast data loaded.")
        return actual_data

    print("Actual temperature forecast data unavailable.")
    print("Using simulated temperature forecast data.")

    return get_simulated_temperature_data()


def temperature_forecast_graph(forecast_data, location_name=None):
    """
    location_name is accepted but NOT rendered on the graph
    (no heading is shown). It is kept as a parameter only so a
    caller can attach it to the figure/output metadata later if
    needed -- the dashboard/frontend owns displaying location,
    not the graph itself.
    """

    df = forecast_data.copy()

    required_columns = ["Time_stamp", "Temperature"]

    missing_columns = [c for c in required_columns if c not in df.columns]

    if missing_columns:
        raise ValueError(
            "Missing required forecast columns: " + str(missing_columns)
        )

    df["Time_stamp"] = pd.to_datetime(df["Time_stamp"])
    df = df.sort_values("Time_stamp").reset_index(drop=True)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["Time_stamp"],
            y=df["Temperature"],
            mode="lines+markers",
            name="Temperature (Deg.C)",
            line=dict(color="#ff4f81", width=2.5),
            marker=dict(size=7, color="#ff4f81"),
            fill="tozeroy",
            fillcolor="rgba(255, 79, 129, 0.18)",
            hovertemplate=(
                "<b>%{x|%d-%b-%Y %H:%M}</b><br>"
                "Temperature (Deg.C): %{y:.2f}"
                "<extra></extra>"
            )
        )
    )

    y_range = _padded_range(df["Temperature"], pad_ratio=0.15)

    _apply_common_layout(fig, y_range)

    if location_name:
        fig.update_layout(meta={"location": location_name})

    output_file = os.path.join(OUTPUT_DIR, "temperature_forecast.html")

    fig.write_html(
        output_file,
        include_plotlyjs=True,
        full_html=True,
        config=PLOTLY_CONFIG
    )

    print("\nTemperature forecast graph created:")
    print(output_file)

    return fig


# ============================================================
# RAINFALL FORECAST
# ============================================================

def import_rainfall_forecast_data():
    """
    Real rainfall forecast data entry point.

    Returns:
        pandas.DataFrame -> if actual data is available
        None             -> if actual data is unavailable

    NOTE: not connected yet -- the file has not been received.
    Do not assume a source/schema until one is actually provided.
    """

    return None


def get_simulated_rainfall_data():

    data = {

        "Time_stamp": [
            "2026-09-21 05:30", "2026-09-21 08:30", "2026-09-21 11:30",
            "2026-09-21 14:30", "2026-09-21 17:30", "2026-09-21 20:30",
            "2026-09-21 23:30", "2026-09-22 02:30", "2026-09-22 05:30",
            "2026-09-22 08:30", "2026-09-22 11:30", "2026-09-22 14:30",
            "2026-09-22 17:30", "2026-09-22 20:30", "2026-09-22 23:30",
            "2026-09-23 02:30", "2026-09-23 05:30", "2026-09-23 08:30",
            "2026-09-23 11:30", "2026-09-23 14:30", "2026-09-23 17:30",
            "2026-09-23 20:30", "2026-09-23 23:30", "2026-09-24 02:30",
            "2026-09-24 05:30"
        ],

        "Rain": [
            0.0, 0.0, 1.8, 6.9, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.9, 0.0, 0.0, 4.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.8, 0.5, 0.0,
            0.3, 0.0
        ]
    }

    df = pd.DataFrame(data)

    df["Time_stamp"] = pd.to_datetime(df["Time_stamp"])

    return df


def get_rainfall_data():

    print("\nAttempting to import actual rainfall forecast data...")

    actual_data = import_rainfall_forecast_data()

    if actual_data is not None:
        print("Actual rainfall forecast data loaded.")
        return actual_data

    print("Actual rainfall forecast data unavailable.")
    print("Using simulated rainfall forecast data.")

    return get_simulated_rainfall_data()


def rainfall_forecast_graph(forecast_data, location_name=None):
    """
    Same contract note as temperature_forecast_graph: location_name
    is accepted but not rendered as a heading.
    """

    df = forecast_data.copy()

    required_columns = ["Time_stamp", "Rain"]

    missing_columns = [c for c in required_columns if c not in df.columns]

    if missing_columns:
        raise ValueError(
            "Missing required forecast columns: " + str(missing_columns)
        )

    df["Time_stamp"] = pd.to_datetime(df["Time_stamp"])
    df = df.sort_values("Time_stamp").reset_index(drop=True)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["Time_stamp"],
            y=df["Rain"],
            name="Rain (mm)",
            marker=dict(
                color="#6fa8dc",
                line=dict(color="#2f80ed", width=1)
            ),
            hovertemplate=(
                "<b>%{x|%d-%b-%Y %H:%M}</b><br>"
                "Rain (mm): %{y:.2f}"
                "<extra></extra>"
            )
        )
    )

    y_range = _padded_range(df["Rain"], pad_ratio=0.1, floor_at_zero=True)

    _apply_common_layout(fig, y_range)

    if location_name:
        fig.update_layout(meta={"location": location_name})

    output_file = os.path.join(OUTPUT_DIR, "rainfall_forecast.html")

    fig.write_html(
        output_file,
        include_plotlyjs=True,
        full_html=True,
        config=PLOTLY_CONFIG
    )

    print("\nRainfall forecast graph created:")
    print(output_file)

    return fig


# ============================================================
# WIND SPEED & DIRECTION FORECAST
# ============================================================

def import_wind_forecast_data():
    """
    Real wind forecast data entry point.

    Returns:
        pandas.DataFrame -> if actual data is available
        None             -> if actual data is unavailable

    NOTE: not connected yet. Do not assume a source/schema here
    until one has actually been provided. This is a FORECAST
    wind graph -- separate from the existing NIWE anemometer
    windrose (local_graphs/wind_analysis.py), which stays as is.
    """

    return None


def get_simulated_wind_data():

    data = {

        "Time_stamp": [
            "2026-09-21 05:30", "2026-09-21 08:30", "2026-09-21 11:30",
            "2026-09-21 14:30", "2026-09-21 17:30", "2026-09-21 20:30",
            "2026-09-21 23:30", "2026-09-22 02:30", "2026-09-22 05:30",
            "2026-09-22 08:30", "2026-09-22 11:30", "2026-09-22 14:30",
            "2026-09-22 17:30", "2026-09-22 20:30", "2026-09-22 23:30",
            "2026-09-23 02:30", "2026-09-23 05:30", "2026-09-23 08:30",
            "2026-09-23 11:30", "2026-09-23 14:30", "2026-09-23 17:30",
            "2026-09-23 20:30", "2026-09-23 23:30", "2026-09-24 02:30",
            "2026-09-24 05:30"
        ],

        "WindSpeed": [
            3.6, 2.1, 3.8, 5.1, 7.4, 3.3, 5.9,
            4.4, 3.9, 6.3, 8.3, 8.1, 8.0, 7.1, 6.5,
            6.9, 8.5, 6.3, 5.8, 8.8, 9.2, 8.6, 9.1,
            8.9, 9.2
        ],

        "WindDir": [
            250, 190, 260, 130, 170, 240, 255,
            140, 220, 240, 150, 140, 100, 95, 105,
            110, 60, 100, 90, 70, 65, 55, 50,
            60, 45
        ]
    }

    df = pd.DataFrame(data)

    df["Time_stamp"] = pd.to_datetime(df["Time_stamp"])

    return df


def get_wind_data():

    print("\nAttempting to import actual wind forecast data...")

    actual_data = import_wind_forecast_data()

    if actual_data is not None:
        print("Actual wind forecast data loaded.")
        return actual_data

    print("Actual wind forecast data unavailable.")
    print("Using simulated wind forecast data.")

    return get_simulated_wind_data()


def wind_forecast_graph(forecast_data, location_name=None):
    """
    Same contract note as the other forecast graphs: location_name
    is accepted but not rendered as a heading.

    Bars = wind speed. Triangle markers above each bar = wind
    direction, rotated to the compass bearing in WindDir.
    """

    df = forecast_data.copy()

    required_columns = ["Time_stamp", "WindSpeed", "WindDir"]

    missing_columns = [c for c in required_columns if c not in df.columns]

    if missing_columns:
        raise ValueError(
            "Missing required forecast columns: " + str(missing_columns)
        )

    df["Time_stamp"] = pd.to_datetime(df["Time_stamp"])
    df["WindSpeed"] = pd.to_numeric(df["WindSpeed"], errors="coerce")
    df["WindDir"] = pd.to_numeric(df["WindDir"], errors="coerce")

    df = df.dropna(subset=["Time_stamp", "WindSpeed", "WindDir"])
    df = df.sort_values("Time_stamp").reset_index(drop=True)

    fig = go.Figure()

    # ------------------------------------------------------
    # WIND SPEED BARS
    # ------------------------------------------------------

    fig.add_trace(
        go.Bar(
            x=df["Time_stamp"],
            y=df["WindSpeed"],
            name="Wind Speed (m/s) & Direction (deg-N)",
            marker=dict(
                color="#20c9a6",
                line=dict(color="#168fb5", width=1.5)
            ),
            customdata=df["WindDir"],
            hovertemplate=(
                "<b>%{x|%d-%b-%Y %H:%M}</b><br>"
                "WindSpeed: %{y:.2f} m/s<br>"
                "WindDir: %{customdata:.2f} deg-N"
                "<extra></extra>"
            )
        )
    )

    # ------------------------------------------------------
    # WIND DIRECTION ARROWS (placed just above each bar)
    # ------------------------------------------------------

    arrow_height = (
        df["WindSpeed"].max() * 0.06
        if len(df) > 0
        else 1
    )

    arrow_y = df["WindSpeed"] + arrow_height

    # FIX: hovertemplate must be one fixed string -- it can't be
    # built by splicing a per-row Series into it with "+". Both
    # values now travel through customdata instead so the
    # %{customdata[0]} / %{customdata[1]} placeholders pick the
    # correct row automatically.
    arrow_customdata = np.stack(
        [df["WindSpeed"].to_numpy(), df["WindDir"].to_numpy()],
        axis=-1
    )

    fig.add_trace(
        go.Scatter(
            x=df["Time_stamp"],
            y=arrow_y,
            mode="markers",
            name="Wind Direction",
            marker=dict(
                symbol="triangle-up",
                size=13,
                color="#8e2ca0",
                line=dict(width=0),
                angle=df["WindDir"]
            ),
            customdata=arrow_customdata,
            hovertemplate=(
                "<b>%{x|%d-%b-%Y %H:%M}</b><br>"
                "WindSpeed: %{customdata[0]:.2f} m/s<br>"
                "WindDir: %{customdata[1]:.2f} deg-N"
                "<extra></extra>"
            ),
            showlegend=False
        )
    )

    # rangemode="tozero" keeps the bar baseline at 0, but still pad
    # the top so the direction arrows have headroom above the tallest bar.
    y_range = _padded_range(df["WindSpeed"], pad_ratio=0.25, floor_at_zero=True)

    _apply_common_layout(fig, y_range)

    if location_name:
        fig.update_layout(meta={"location": location_name})

    output_file = os.path.join(OUTPUT_DIR, "wind_forecast.html")

    fig.write_html(
        output_file,
        include_plotlyjs=True,
        full_html=True,
        config=PLOTLY_CONFIG
    )

    print("\nWind forecast graph created:")
    print(output_file)

    return fig
# ============================================================
# HUMIDITY & CLOUDINESS DATA
# ============================================================

def import_humidity_forecast_data():
    """
    Real humidity/cloudiness forecast data entry point.

    Returns:
        pandas.DataFrame -> if actual data is available
        None             -> if actual data is unavailable

    NOTE: not connected yet. Do not assume a source/schema here
    until one has actually been provided.
    """

    return None


def get_simulated_humidity_data():

    data = {

        "Time_stamp": [
            "2026-09-21 05:30", "2026-09-21 08:30", "2026-09-21 11:30",
            "2026-09-21 14:30", "2026-09-21 17:30", "2026-09-21 20:30",
            "2026-09-21 23:30", "2026-09-22 02:30", "2026-09-22 05:30",
            "2026-09-22 08:30", "2026-09-22 11:30", "2026-09-22 14:30",
            "2026-09-22 17:30", "2026-09-22 20:30", "2026-09-22 23:30",
            "2026-09-23 02:30", "2026-09-23 05:30", "2026-09-23 08:30",
            "2026-09-23 11:30", "2026-09-23 14:30", "2026-09-23 17:30",
            "2026-09-23 20:30", "2026-09-23 23:30", "2026-09-24 02:30",
            "2026-09-24 05:30"
        ],

        "Humidity": [
            92, 76, 68, 75, 93, 99, 100,
            98, 94, 84, 54, 82, 88, 91, 72,
            66, 62, 55, 52, 51, 60, 56, 55,
            64, 84
        ],

        "Cloudiness": [
            90, 85, 88, 82, 95, 97, 99,
            96, 92, 88, 45, 90, 85, 60, 55,
            40, 35, 30, 25, 15, 20, 18, 22,
            15, 10
        ]
    }

    df = pd.DataFrame(data)

    df["Time_stamp"] = pd.to_datetime(df["Time_stamp"])

    return df


def get_humidity_data():

    print("\nAttempting to import actual humidity/cloudiness forecast data...")

    actual_data = import_humidity_forecast_data()

    if actual_data is not None:
        print("Actual humidity/cloudiness forecast data loaded.")
        return actual_data

    print("Actual humidity/cloudiness forecast data unavailable.")
    print("Using simulated humidity/cloudiness forecast data.")

    return get_simulated_humidity_data()


# ============================================================
# HUMIDITY & CLOUDINESS FORECAST GRAPH
# ============================================================

def humidity_cloudiness_forecast_graph(forecast_data):

    df = forecast_data.copy()

    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = [
        "Time_stamp",
        "Humidity",
        "Cloudiness"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required forecast columns: "
            + str(missing_columns)
        )

    # --------------------------------------------------------
    # PREPARE DATA
    # --------------------------------------------------------

    df["Time_stamp"] = pd.to_datetime(
        df["Time_stamp"]
    )

    df["Humidity"] = pd.to_numeric(
        df["Humidity"],
        errors="coerce"
    )

    df["Cloudiness"] = pd.to_numeric(
        df["Cloudiness"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "Time_stamp",
            "Humidity",
            "Cloudiness"
        ]
    )

    df = df.sort_values(
        "Time_stamp"
    ).reset_index(
        drop=True
    )

    # ========================================================
    # FIGURE
    # ========================================================

    fig = go.Figure()

    # --------------------------------------------------------
    # HUMIDITY BARS
    # --------------------------------------------------------

    fig.add_trace(
        go.Bar(

            x=df["Time_stamp"],

            y=df["Humidity"],

            name="Humidity (%)",

            marker=dict(

                color="#ffc107",

                line=dict(
                    color="#ff8c00",
                    width=1.5
                )
            ),

            hovertemplate=(

                "<b>%{x|%d-%b-%Y %H:%M}</b><br>"

                "Humidity: %{y:.2f}%"

                "<extra></extra>"
            )
        )
    )

    # ========================================================
    # WEATHER ICONS
    # ========================================================

    # Icons are positioned according to cloudiness.
    #
    # 0–20   : sunny
    # 21–50  : partly cloudy
    # 51–80  : cloudy
    # 81–100 : heavy/cloudy
    #
    # These are display icons only.

    def weather_icon(cloudiness):

        if cloudiness <= 20:
            return "☀️"

        elif cloudiness <= 50:
            return "🌤️"

        elif cloudiness <= 80:
            return "⛅"

        else:
            return "☁️"

    icons = [
        weather_icon(value)
        for value in df["Cloudiness"]
    ]

    # --------------------------------------------------------
    # ICON HEIGHT
    # --------------------------------------------------------

    icon_y = [

        min(
            humidity + 7,
            108
        )

        for humidity in df["Humidity"]
    ]

    # --------------------------------------------------------
    # ICON TRACE
    # --------------------------------------------------------

    fig.add_trace(

        go.Scatter(

            x=df["Time_stamp"],

            y=icon_y,

            mode="text",

            text=icons,

            textfont=dict(
                size=20
            ),

            name="Cloudiness (%)",

            customdata=df["Cloudiness"],

            hovertemplate=(

                "<b>%{x|%d-%b-%Y %H:%M}</b><br>"

                "Cloudiness: %{customdata:.2f}%"

                "<extra></extra>"
            )
        )
    )

    # ========================================================
    # LAYOUT
    # ========================================================

    fig.update_layout(

        title=dict(

            text="Humidity (%) & Cloudiness (%)",

            x=0.01,

            xanchor="left",

            font=dict(
                size=18
            )
        ),

        xaxis=dict(

            title="",

            tickformat="%d-%b %H:%M",

            tickangle=-45,

            showgrid=True,

            gridcolor="rgba(150,150,150,0.25)",

            zeroline=False
        ),

        yaxis=dict(

            title="",

            range=[
                0,
                110
            ],

            dtick=10,

            showgrid=True,

            gridcolor="rgba(150,150,150,0.25)",

            zeroline=False
        ),

        hovermode="closest",

        template="plotly_white",

        height=500,

        margin=dict(

            l=55,

            r=25,

            t=80,

            b=90
        ),

        showlegend=True,

        # ----------------------------------------------------
        # CENTERED LEGEND
        # ----------------------------------------------------

        legend=dict(

            orientation="h",

            yanchor="bottom",

            y=1.02,

            xanchor="center",

            x=0.5
        )
    )

    # ========================================================
    # INTERACTIVE CONFIGURATION
    # ========================================================

    config = {

        "responsive": True,

        "displaylogo": False,

        "scrollZoom": True,

        "modeBarButtonsToRemove": [

            "lasso2d",

            "select2d"
        ]
    }

    # ========================================================
    # SAVE
    # ========================================================

    output_file = os.path.join(

        OUTPUT_DIR,

        "humidity_cloudiness_forecast.html"
    )

    fig.write_html(

        output_file,

        include_plotlyjs=True,

        full_html=True,

        config=config
    )

    print(
        "\nHumidity & cloudiness graph created:"
    )

    print(
        output_file
    )

    return fig



# ============================================================
# SURFACE PRESSURE DATA
# ============================================================

def import_surface_pressure_forecast_data():
    """
    Real surface pressure forecast data entry point.

    Returns:
        pandas.DataFrame -> if actual data is available
        None             -> if actual data is unavailable

    NOTE: not connected yet. Do not assume a source/schema here
    until one has actually been provided.
    """

    return None


def get_simulated_surface_pressure_data():

    data = {

        "Time_stamp": [
            "2026-09-21 05:30", "2026-09-21 08:30", "2026-09-21 11:30",
            "2026-09-21 14:30", "2026-09-21 17:30", "2026-09-21 20:30",
            "2026-09-21 23:30", "2026-09-22 02:30", "2026-09-22 05:30",
            "2026-09-22 08:30", "2026-09-22 11:30", "2026-09-22 14:30",
            "2026-09-22 17:30", "2026-09-22 20:30", "2026-09-22 23:30",
            "2026-09-23 02:30", "2026-09-23 05:30", "2026-09-23 08:30",
            "2026-09-23 11:30", "2026-09-23 14:30", "2026-09-23 17:30",
            "2026-09-23 20:30", "2026-09-23 23:30", "2026-09-24 02:30",
            "2026-09-24 05:30"
        ],

        "SurfacePressure": [
            1005.90, 1004.20, 1005.50, 1007.95, 1007.65, 1006.60, 1006.35,
            1006.15, 1005.85, 1006.15, 1006.80, 1007.50, 1007.35, 1006.45, 1006.55,
            1006.15, 1006.05, 1005.85, 1006.25, 1006.50, 1006.25, 1006.35, 1006.95,
            1006.00, 1005.55
        ]
    }

    df = pd.DataFrame(data)

    df["Time_stamp"] = pd.to_datetime(df["Time_stamp"])

    return df


def get_surface_pressure_data():

    print("\nAttempting to import actual surface pressure forecast data...")

    actual_data = import_surface_pressure_forecast_data()

    if actual_data is not None:
        print("Actual surface pressure forecast data loaded.")
        return actual_data

    print("Actual surface pressure forecast data unavailable.")
    print("Using simulated surface pressure forecast data.")

    return get_simulated_surface_pressure_data()


# ============================================================
# SURFACE PRESSURE DEVIATION FROM 1000 hPa
# ============================================================

def surface_pressure_deviation_graph(forecast_data):

    df = forecast_data.copy()

    # --------------------------------------------------------
    # REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = [
        "Time_stamp",
        "SurfacePressure"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required forecast columns: "
            + str(missing_columns)
        )

    # --------------------------------------------------------
    # PREPARE DATA
    # --------------------------------------------------------

    df["Time_stamp"] = pd.to_datetime(
        df["Time_stamp"]
    )

    df["SurfacePressure"] = pd.to_numeric(
        df["SurfacePressure"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "Time_stamp",
            "SurfacePressure"
        ]
    )

    df = df.sort_values(
        "Time_stamp"
    ).reset_index(
        drop=True
    )

    # --------------------------------------------------------
    # DEVIATION FROM 1000 hPa
    # --------------------------------------------------------

    df["PressureDeviation"] = (
        df["SurfacePressure"] - 1000.0
    )

    # ========================================================
    # CREATE FIGURE
    # ========================================================

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=df["Time_stamp"],

            y=df["PressureDeviation"],

            mode="lines+markers",

            name="Surface Pressure Deviation from 1000hPa",

            # ------------------------------------------------
            # BLACK LINE
            # ------------------------------------------------

            line=dict(
                color="black",
                width=2
            ),

            # ------------------------------------------------
            # YELLOW CIRCULAR POINTS
            # ------------------------------------------------

            marker=dict(
                symbol="circle",
                size=7,
                color="#ffd000",

                line=dict(
                    color="black",
                    width=2
                )
            ),

            # ------------------------------------------------
            # YELLOW FILLED AREA
            # ------------------------------------------------

            fill="tozeroy",

            fillcolor="#ffd000",

            # ------------------------------------------------
            # HOVER
            # ------------------------------------------------

            hovertemplate=(

                "<b>%{x|%d-%b-%Y %H:%M}</b><br>"

                "Surface Pressure Deviation: "
                "%{y:.2f} hPa"

                "<extra></extra>"
            )
        )
    )

    # ========================================================
    # LAYOUT
    # ========================================================

    fig.update_layout(

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title=dict(

            text=(
                "Surface Pressure Deviation "
                "from 1000hPa"
            ),

            x=0.01,

            xanchor="left",

            font=dict(
                size=18
            )
        ),

        # ----------------------------------------------------
        # X AXIS
        # ----------------------------------------------------

        xaxis=dict(

            title="",

            tickformat="%d-%b %H:%M",

            tickangle=-45,

            showgrid=True,

            gridcolor="rgba(150,150,150,0.25)",

            zeroline=False
        ),

        # ----------------------------------------------------
        # Y AXIS
        # ----------------------------------------------------

        yaxis=dict(

            title="",

            showgrid=True,

            gridcolor="rgba(150,150,150,0.25)",

            zeroline=False
        ),

        # ----------------------------------------------------
        # HOVER
        # ----------------------------------------------------

        hovermode="closest",

        # ----------------------------------------------------
        # PLOT STYLE
        # ----------------------------------------------------

        template="plotly_white",

        height=500,

        margin=dict(

            l=60,

            r=25,

            t=80,

            b=90
        ),

        # ----------------------------------------------------
        # LEGEND
        # ----------------------------------------------------

        showlegend=True,

        legend=dict(

            orientation="h",

            yanchor="bottom",

            y=1.02,

            xanchor="center",

            x=0.5
        )
    )

    # ========================================================
    # INTERACTIVE CONFIGURATION
    # ========================================================

    config = {

        "responsive": True,

        "displaylogo": False,

        "scrollZoom": True,

        "modeBarButtonsToRemove": [

            "lasso2d",

            "select2d"
        ]
    }

    # ========================================================
    # SAVE HTML
    # ========================================================

    output_file = os.path.join(

        OUTPUT_DIR,

        "surface_pressure_deviation.html"
    )

    fig.write_html(

        output_file,

        include_plotlyjs=True,

        full_html=True,

        config=config
    )

    print(
        "\nSurface pressure deviation graph created:"
    )

    print(
        output_file
    )

    return fig

# ============================================================
# MAIN GRAPH EXECUTION
# ============================================================

def run_forecast_analysis(location_name=None):

    temperature_data = get_temperature_data()
    temperature_forecast_graph(
        temperature_data,
        location_name=location_name
    )

    rainfall_data = get_rainfall_data()
    rainfall_forecast_graph(
        rainfall_data,
        location_name=location_name
    )

    wind_data = get_wind_data()
    wind_forecast_graph(
        wind_data,
        location_name=location_name
    )

    humidity_data = get_humidity_data()
    humidity_cloudiness_forecast_graph(
        humidity_data
    )

    surface_pressure_data = get_surface_pressure_data()
    surface_pressure_deviation_graph(
        surface_pressure_data
    )
# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    run_forecast_analysis()


