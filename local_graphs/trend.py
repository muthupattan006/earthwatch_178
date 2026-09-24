# ============================================================
# EARTHWATCH - DYNAMIC TEMPERATURE TREND ANALYSIS
# ============================================================

import math

import pandas as pd
import plotly.graph_objects as go

from config import TREND_DATA_PATH, VISUAL_OUTPUT


# ============================================================
# TEST LOCATION
# ============================================================

# Temporary test coordinate.
# Later, Harshini's frontend will provide these values.

CENTER_LAT = 11.35
CENTER_LON = 76.79


# ============================================================
# ANALYSIS CONFIGURATION
# ============================================================

# Radius around the selected coordinate, in kilometres.
#
# Change this later if required.
# This is NOT a map radius; it defines which WRF grid
# observations are included in the analysis.

RADIUS_KM = 15.0


# Maximum number of points sent to Plotly.
# This protects the browser if the selected radius contains
# a very large number of WRF observations.

MAX_PLOT_POINTS = 5000


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine_distance(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate distance between two geographic coordinates.

    Returns:
        Distance in kilometres.
    """

    earth_radius_km = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius_km * c


# ============================================================
# IMPORT WRF DATA
# ============================================================

def import_wrf_data():
    """
    Load the complete WRF CSV dataset.

    All required WRF variables are imported once so that
    additional graphs can be added later without changing
    the importer.
    """

    try:

        print("\n")
        print("=" * 60)
        print("LOADING WRF DATA")
        print("=" * 60)

        print(f"\nFile:")
        print(TREND_DATA_PATH)

        # ----------------------------------------------------
        # Load the complete WRF dataset
        # ----------------------------------------------------

        df = pd.read_csv(
            TREND_DATA_PATH
        )

        print(
            f"\nRows loaded: "
            f"{len(df):,}"
        )

        # ----------------------------------------------------
        # Convert available numerical variables
        # ----------------------------------------------------

        numeric_columns = [
            "lat",
            "lon",
            "t2",
            "psfc",
            "rainc",
            "rainnc",
            "swdown",
            "clflo",
            "clfmi",
            "clfhi",
            "rh2",
            "ws10",
            "wd10"
        ]

        for column in numeric_columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        # ----------------------------------------------------
        # Convert temperature
        # Kelvin -> Celsius
        # ----------------------------------------------------

        if "t2" in df.columns:

            df["Temperature"] = (
                df["t2"] - 273.15
            )

        # ----------------------------------------------------
        # Remove records without coordinates
        # ----------------------------------------------------

        df = df.dropna(
            subset=[
                "lat",
                "lon"
            ]
        )

        print(
            f"Valid WRF records: "
            f"{len(df):,}"
        )

        if "time" in df.columns:

            print(
                f"Unique timestamps: "
                f"{df['time'].nunique():,}"
            )

        print(
            f"Columns available: "
            f"{len(df.columns)}"
        )

        return df

    except FileNotFoundError:

        print("\nERROR:")
        print(
            "WRF file was not found."
        )

        print(
            f"Expected path:\n"
            f"{TREND_DATA_PATH}"
        )

        return None

    except Exception as error:

        print(
            "\nERROR while loading WRF data:"
        )

        print(error)

        return None
# ============================================================
# SELECT NEARBY WRF COORDINATES
# ============================================================

def select_nearby_coordinates(
    data,
    center_lat,
    center_lon,
    radius_km
):
    """
    Select all WRF observations within the specified
    radius around the selected coordinate.

    The original latitude and longitude are retained for
    Plotly hover information.
    """

    print("\n")
    print("=" * 60)
    print("SELECTING NEARBY WRF COORDINATES")
    print("=" * 60)

    print(
        f"\nCenter latitude : {center_lat}"
    )

    print(
        f"Center longitude: {center_lon}"
    )

    print(
        f"Radius          : {radius_km} km"
    )

    # --------------------------------------------------------
    # First apply a cheap bounding-box filter.
    #
    # This prevents us from calculating Haversine distance
    # for every single row in a very large CSV.
    # --------------------------------------------------------

    latitude_range = radius_km / 111.0

    longitude_scale = max(
        math.cos(
            math.radians(center_lat)
        ),
        0.01
    )

    longitude_range = (
        radius_km
        / (111.0 * longitude_scale)
    )

    candidate_data = data[
        (
            data["lat"]
            .between(
                center_lat - latitude_range,
                center_lat + latitude_range
            )
        )
        &
        (
            data["lon"]
            .between(
                center_lon - longitude_range,
                center_lon + longitude_range
            )
        )
    ].copy()

    print(
        f"\nBounding-box candidates: "
        f"{len(candidate_data):,}"
    )

    if candidate_data.empty:

        print(
            "\nNo WRF coordinates found "
            "inside the bounding region."
        )

        return candidate_data

    # --------------------------------------------------------
    # Exact Haversine distance
    # --------------------------------------------------------

    candidate_data["Distance_km"] = candidate_data.apply(
        lambda row: haversine_distance(
            center_lat,
            center_lon,
            row["lat"],
            row["lon"]
        ),
        axis=1
    )

    nearby_data = candidate_data[
        candidate_data["Distance_km"] <= radius_km
    ].copy()

    # --------------------------------------------------------
    # Sort by time and then coordinate.
    # --------------------------------------------------------

    nearby_data = nearby_data.sort_values(
        by=[
            "time",
            "Distance_km",
            "lat",
            "lon"
        ]
    )

    print(
        f"WRF coordinates inside radius: "
        f"{len(nearby_data):,}"
    )

    if not nearby_data.empty:

        print(
            f"Nearest coordinate distance: "
            f"{nearby_data['Distance_km'].min():.3f} km"
        )

        print(
            f"Farthest coordinate distance: "
            f"{nearby_data['Distance_km'].max():.3f} km"
        )

    return nearby_data


# ============================================================
# PLOT DATA PREPARATION
# ============================================================

def prepare_plot_data(data):
    """
    Prepare the nearby WRF observations for Plotly.

    If there are too many observations, reduce the number
    of plotted points without changing the underlying data.
    """

    if data.empty:
        return data

    if len(data) <= MAX_PLOT_POINTS:

        return data.copy()

    print(
        f"\nSelected region contains "
        f"{len(data):,} observations."
    )

    print(
        f"Reducing plotted observations to "
        f"{MAX_PLOT_POINTS:,} for browser performance."
    )
# ============================================================
# TEMPERATURE TREND GRAPH
# ============================================================

def temperature_trend_graph(
    data,
    center_lat,
    center_lon,
    radius_km
):
    """
    Create the dynamic temperature graph.

    X-axis:
        WRF observation count

    Y-axis:
        Temperature in °C

    Hover:
        Latitude
        Longitude
        Temperature
        Distance from selected coordinate
        Time
    """

    if data is None or data.empty:

        print(
            "\nTemperature graph skipped:"
            "\nNo nearby WRF temperature data."
        )

        return

    # --------------------------------------------------------
    # Prepare plot data
    # --------------------------------------------------------

    plot_data = prepare_plot_data(
        data
    )

    # --------------------------------------------------------
    # Plot index / observation count
    # --------------------------------------------------------

    plot_data = plot_data.reset_index(
        drop=True
    )

    plot_data["Observation"] = (
        plot_data.index + 1
    )

    print(
        f"\nPlotting "
        f"{len(plot_data):,} temperature observations."
    )

    # --------------------------------------------------------
    # Plotly figure
    # --------------------------------------------------------

    figure = go.Figure()

    figure.add_trace(
        go.Scattergl(

            x=plot_data["Observation"],

            y=plot_data["Temperature"],

            mode="lines+markers",

            # ------------------------------------------------
            # VERMILION
            # ------------------------------------------------

            line=dict(
                color="#E34234",
                width=2
            ),

            marker=dict(
                color="#E34234",
                size=5
            ),

            # ------------------------------------------------
            # Hover information
            # ------------------------------------------------

            customdata=plot_data[
                [
                    "time",
                    "lat",
                    "lon",
                    "Distance_km"
                ]
            ],

            hovertemplate=(
                "<b>Temperature</b><br>"
                "Observation: %{x}<br>"
                "Time: %{customdata[0]}<br>"
                "Temperature: %{y:.2f} °C<br>"
                "Latitude: %{customdata[1]:.5f}° N<br>"
                "Longitude: %{customdata[2]:.5f}° E<br>"
                "Distance: %{customdata[3]:.2f} km"
                "<extra></extra>"
            ),

            name="Temperature"
        )
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    figure.update_layout(

        title=(
            "Temperature Trend"
            f" — {radius_km:.0f} km radius"
        ),

        xaxis=dict(

            title="WRF observations",

            # ------------------------------------------------
            # MOVING / ROLLING WINDOW
            # ------------------------------------------------

            rangeslider=dict(
                visible=True
            ),

            rangeselector=dict(

                buttons=[

                    dict(
                        count=100,
                        label="100",
                        step="all",
                        stepmode="backward"
                    ),

                    dict(
                        count=250,
                        label="250",
                        step="all",
                        stepmode="backward"
                    ),

                    dict(
                        count=500,
                        label="500",
                        step="all",
                        stepmode="backward"
                    ),

                    dict(
                        step="all",
                        label="All"
                    )
                ]
            )
        ),

        yaxis=dict(
            title="Temperature (°C)"
        ),

        template="plotly_white",

        hovermode="closest",

        margin=dict(
            l=70,
            r=40,
            t=80,
            b=100
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_path = (
        VISUAL_OUTPUT
        / "temperature_trend.html"
    )

    figure.write_html(
        output_path,
        include_plotlyjs=True
    )

    print(
        "\nTemperature graph saved:"
    )

    print(output_path)
    # --------------------------------------------------------
    # Preserve temporal ordering while reducing the number
    # of rendered points.
    # --------------------------------------------------------

    step = math.ceil(
        len(data) / MAX_PLOT_POINTS
    )

    plot_data = data.iloc[::step].copy()

    return plot_data
# ============================================================
# WIND FREQUENCY DISTRIBUTION
# ============================================================

def wind_frequency_distribution(
    data,
    center_lat,
    center_lon,
    radius_km
):
    """
    Create the wind-speed frequency distribution.

    Uses the same WRF observations selected for the
    dynamic wind trend.

    X-axis:
        Wind speed (m/s)

    Y-axis:
        Frequency (%)
    """

    if data is None or data.empty:
        print(
            "\nWind frequency distribution skipped:"
            "\nNo nearby WRF wind data."
        )
        return

    # --------------------------------------------------------
    # Prepare data
    # --------------------------------------------------------

    plot_data = data.copy()

    plot_data["WindSpeed"] = pd.to_numeric(
        plot_data["ws10"],
        errors="coerce"
    )

    plot_data = plot_data.dropna(
        subset=["WindSpeed"]
    )

    if plot_data.empty:
        print(
            "\nWind frequency distribution skipped:"
            "\nNo valid wind-speed observations."
        )
        return

    # --------------------------------------------------------
    # Wind-speed bins
    # --------------------------------------------------------

    bin_width = 0.5

    min_speed = plot_data["WindSpeed"].min()
    max_speed = plot_data["WindSpeed"].max()

    bins = pd.interval_range(
        start=0,
        end=max_speed + bin_width,
        freq=bin_width,
        closed="left"
    )

    frequency = pd.cut(
        plot_data["WindSpeed"],
        bins=[interval.left for interval in bins] +
             [bins[-1].right],
        right=False
    )

    frequency_counts = (
        frequency
        .value_counts(sort=False)
    )

    frequency_percent = (
        frequency_counts
        / frequency_counts.sum()
        * 100
    )

    # --------------------------------------------------------
    # Bin labels
    # --------------------------------------------------------

    labels = [
        f"{interval.left:.1f}–{interval.right:.1f}"
        for interval in frequency_counts.index
    ]

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=labels,
            y=frequency_percent.values,

            hovertemplate=(
                "<b>Wind Speed</b><br>"
                "Range: %{x} m/s<br>"
                "Frequency: %{y:.2f}%"
                "<extra></extra>"
            ),

            name="Frequency"
        )
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    figure.update_layout(

        title=(
            "Wind Speed Frequency Distribution"
            f" — {radius_km:.0f} km radius"
        ),

        xaxis=dict(
            title="Wind Speed (m/s)"
        ),

        yaxis=dict(
            title="Frequency (%)"
        ),

        template="plotly_white",

        hovermode="closest",

        margin=dict(
            l=70,
            r=40,
            t=80,
            b=100
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_path = (
        VISUAL_OUTPUT /
        "wind_frequency_distribution.html"
    )

    figure.write_html(
        output_path,
        include_plotlyjs=True,
        config={
            "responsive": True,
            "displaylogo": False,
            "scrollZoom": True
        }
    )

    print(
        "\nWind frequency distribution saved:"
    )

    print(output_path)
# ============================================================
# MAIN RUNNER
# ============================================================

def run_trend_analysis():

    print("\n")
    print("=" * 60)
    print("EARTHWATCH DYNAMIC TEMPERATURE ANALYSIS")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Load actual WRF data
    # --------------------------------------------------------

    data = import_temperature_data()

    if data is None:

        print(
            "\nAnalysis stopped."
        )

        return

    # --------------------------------------------------------
    # 2. Temporary test coordinate
    #
    #    Later Harshini supplies these two values.
    # --------------------------------------------------------

    center_lat = CENTER_LAT
    center_lon = CENTER_LON

    # --------------------------------------------------------
    # 3. Select WRF coordinates around location
    # --------------------------------------------------------

    nearby_data = select_nearby_coordinates(
        data=data,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=RADIUS_KM
    )

    if nearby_data.empty:

        print(
            "\nNo temperature data found "
            "for the selected coordinate."
        )

        return

    # --------------------------------------------------------
    # 4. Generate temperature trend
    # --------------------------------------------------------

    temperature_trend_graph(
        data=nearby_data,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=RADIUS_KM
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("TEMPERATURE ANALYSIS COMPLETED")
    print("=" * 60)

    print(
        f"\nCenter:"
        f" {center_lat}° N, "
        f"{center_lon}° E"
    )

    print(
        f"Radius:"
        f" {RADIUS_KM} km"
    )

    print(
        f"WRF observations selected:"
        f" {len(nearby_data):,}"
    )

    print(
        "\nOutput:"
        f"\n{VISUAL_OUTPUT / 'temperature_trend.html'}"
    )

# ============================================================
# RAINFALL TREND GRAPH
# ============================================================

def rainfall_trend_graph(
    data,
    center_lat,
    center_lon,
    radius_km
):
    """
    Create the dynamic rainfall trend.

    Rainfall:
        rainc + rainnc

    X-axis:
        WRF observation count

    Y-axis:
        Rainfall value

    Hover:
        Time
        Latitude
        Longitude
        Distance
        Rainfall
    """

    if data is None or data.empty:
        print(
            "\nRainfall graph skipped:"
            "\nNo nearby WRF rainfall data."
        )
        return

    plot_data = prepare_plot_data(data)

    plot_data = plot_data.reset_index(drop=True)

    plot_data["Observation"] = (
        plot_data.index + 1
    )

    # --------------------------------------------------------
    # Rainfall
    # --------------------------------------------------------

    plot_data["Rainfall"] = (
        pd.to_numeric(
            plot_data["rainc"],
            errors="coerce"
        ).fillna(0)
        +
        pd.to_numeric(
            plot_data["rainnc"],
            errors="coerce"
        ).fillna(0)
    )

    plot_data = plot_data.dropna(
        subset=["Rainfall"]
    )

    # --------------------------------------------------------
    # Rolling rainfall
    # --------------------------------------------------------

    ROLLING_WINDOW = 10

    plot_data["RollingRainfall"] = (
        plot_data["Rainfall"]
        .rolling(
            window=ROLLING_WINDOW,
            min_periods=1
        )
        .mean()
    )

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    figure = go.Figure()

    # Actual rainfall
    figure.add_trace(
        go.Scattergl(
            x=plot_data["Observation"],
            y=plot_data["Rainfall"],

            mode="lines+markers",

            line=dict(
                width=1.5
            ),

            marker=dict(
                size=4
            ),

            customdata=plot_data[
                [
                    "time",
                    "lat",
                    "lon",
                    "Distance_km"
                ]
            ],

            hovertemplate=(
                "<b>Rainfall</b><br>"
                "Observation: %{x}<br>"
                "Time: %{customdata[0]}<br>"
                "Rainfall: %{y:.3f}<br>"
                "Latitude: %{customdata[1]:.5f}° N<br>"
                "Longitude: %{customdata[2]:.5f}° E<br>"
                "Distance: %{customdata[3]:.2f} km"
                "<extra></extra>"
            ),

            name="Rainfall"
        )
    )

    # Rolling mean
    figure.add_trace(
        go.Scattergl(
            x=plot_data["Observation"],
            y=plot_data["RollingRainfall"],

            mode="lines",

            line=dict(
                width=3
            ),

            name=f"{ROLLING_WINDOW}-observation rolling mean",

            hovertemplate=(
                "<b>Rolling Rainfall</b><br>"
                "Observation: %{x}<br>"
                "Rolling mean: %{y:.3f}"
                "<extra></extra>"
            )
        )
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    figure.update_layout(

        title=(
            "Rainfall Trend"
            f" — {radius_km:.0f} km radius"
        ),

        xaxis=dict(
            title="WRF observations"
        ),

        yaxis=dict(
            title="Rainfall"
        ),

        template="plotly_white",

        hovermode="closest",

        margin=dict(
            l=70,
            r=40,
            t=80,
            b=70
        )
    )

    output_path = (
        VISUAL_OUTPUT /
        "rainfall_trend.html"
    )

    figure.write_html(
        output_path,
        include_plotlyjs=True,
        config={
            "responsive": True,
            "displaylogo": False,
            "scrollZoom": True
        }
    )

    print(
        "\nRainfall graph saved:"
    )

    print(output_path)
# ============================================================
# WIND TREND GRAPH
# ============================================================

def wind_trend_graph(
    data,
    center_lat,
    center_lon,
    radius_km
):
    """
    Create the dynamic wind trend.

    Wind speed:
        ws10

    Wind direction:
        wd10

    X-axis:
        WRF observation count

    Y-axis:
        Wind speed

    Hover:
        Time
        Latitude
        Longitude
        Distance
        Wind speed
        Wind direction
    """

    if data is None or data.empty:
        print(
            "\nWind graph skipped:"
            "\nNo nearby WRF wind data."
        )
        return

    plot_data = prepare_plot_data(data)

    plot_data = plot_data.reset_index(drop=True)

    plot_data["Observation"] = (
        plot_data.index + 1
    )

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    plot_data["WindSpeed"] = pd.to_numeric(
        plot_data["ws10"],
        errors="coerce"
    )

    plot_data["WindDirection"] = pd.to_numeric(
        plot_data["wd10"],
        errors="coerce"
    )

    plot_data = plot_data.dropna(
        subset=[
            "WindSpeed",
            "WindDirection"
        ]
    )

    # --------------------------------------------------------
    # Rolling wind speed
    # --------------------------------------------------------

    ROLLING_WINDOW = 10

    plot_data["RollingWindSpeed"] = (
        plot_data["WindSpeed"]
        .rolling(
            window=ROLLING_WINDOW,
            min_periods=1
        )
        .mean()
    )

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    figure = go.Figure()

    # Wind speed
    figure.add_trace(
        go.Scattergl(
            x=plot_data["Observation"],
            y=plot_data["WindSpeed"],

            mode="lines+markers",

            line=dict(
                width=1.5
            ),

            marker=dict(
                size=4
            ),

            customdata=plot_data[
                [
                    "time",
                    "lat",
                    "lon",
                    "Distance_km",
                    "WindDirection"
                ]
            ],

            hovertemplate=(
                "<b>Wind</b><br>"
                "Observation: %{x}<br>"
                "Time: %{customdata[0]}<br>"
                "Wind speed: %{y:.2f} m/s<br>"
                "Wind direction: %{customdata[4]:.1f}°<br>"
                "Latitude: %{customdata[1]:.5f}° N<br>"
                "Longitude: %{customdata[2]:.5f}° E<br>"
                "Distance: %{customdata[3]:.2f} km"
                "<extra></extra>"
            ),

            name="Wind speed"
        )
    )

    # Rolling mean
    figure.add_trace(
        go.Scattergl(
            x=plot_data["Observation"],
            y=plot_data["RollingWindSpeed"],

            mode="lines",

            line=dict(
                width=3
            ),

            name=f"{ROLLING_WINDOW}-observation rolling mean",

            hovertemplate=(
                "<b>Rolling Wind Speed</b><br>"
                "Observation: %{x}<br>"
                "Rolling mean: %{y:.2f} m/s"
                "<extra></extra>"
            )
        )
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    figure.update_layout(

        title=(
            "Wind Trend"
            f" — {radius_km:.0f} km radius"
        ),

        xaxis=dict(
            title="WRF observations"
        ),

        yaxis=dict(
            title="Wind Speed (m/s)"
        ),

        template="plotly_white",

        hovermode="closest",

        margin=dict(
            l=70,
            r=40,
            t=80,
            b=70
        )
    )

    output_path = (
        VISUAL_OUTPUT /
        "wind_trend.html"
    )

    figure.write_html(
        output_path,
        include_plotlyjs=True,
        config={
            "responsive": True,
            "displaylogo": False,
            "scrollZoom": True
        }
    )

    print(
        "\nWind graph saved:"
    )

    print(output_path)

# ============================================================
# SURFACE PRESSURE ANOMALY — BAR CHART
# ============================================================

def pressure_anomaly_bar_graph(
    data,
    center_lat,
    center_lon,
    radius_km
):
    """
    Create a surface-pressure anomaly bar chart.

    Pressure anomaly:
        ΔP = P - mean(P)

    X-axis:
        WRF observation

    Y-axis:
        Pressure anomaly (hPa)
    """

    if data is None or data.empty:
        print(
            "\nPressure anomaly graph skipped:"
            "\nNo nearby WRF pressure data."
        )
        return

    plot_data = prepare_plot_data(data).copy()

    # --------------------------------------------------------
    # Convert pressure: Pa -> hPa
    # --------------------------------------------------------

    plot_data["Pressure_hPa"] = pd.to_numeric(
        plot_data["psfc"],
        errors="coerce"
    ) / 100.0

    plot_data = plot_data.dropna(
        subset=["Pressure_hPa"]
    )

    if plot_data.empty:
        print(
            "\nPressure anomaly graph skipped:"
            "\nNo valid surface-pressure data."
        )
        return

    # --------------------------------------------------------
    # Calculate regional mean and anomaly
    # --------------------------------------------------------

    mean_pressure = plot_data["Pressure_hPa"].mean()

    plot_data["Pressure_Anomaly"] = (
        plot_data["Pressure_hPa"]
        - mean_pressure
    )

    plot_data = plot_data.reset_index(
        drop=True
    )

    plot_data["Observation"] = (
        plot_data.index + 1
    )

    # --------------------------------------------------------
    # Bar chart
    # --------------------------------------------------------

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=plot_data["Observation"],
            y=plot_data["Pressure_Anomaly"],

            customdata=plot_data[
                [
                    "time",
                    "lat",
                    "lon",
                    "Distance_km",
                    "Pressure_hPa"
                ]
            ],

            hovertemplate=(
                "<b>Surface Pressure Anomaly</b><br>"
                "Observation: %{x}<br>"
                "Time: %{customdata[0]}<br>"
                "Pressure: %{customdata[4]:.2f} hPa<br>"
                "Anomaly: %{y:.2f} hPa<br>"
                "Latitude: %{customdata[1]:.5f}° N<br>"
                "Longitude: %{customdata[2]:.5f}° E<br>"
                "Distance: %{customdata[3]:.2f} km"
                "<extra></extra>"
            ),

            name="Pressure anomaly"
        )
    )

    # --------------------------------------------------------
    # Zero reference line
    # --------------------------------------------------------

    figure.add_hline(
        y=0,
        line_width=2,
        line_dash="dash"
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    figure.update_layout(

        title=(
            "Surface Pressure Anomaly"
            f" — {radius_km:.0f} km radius"
        ),

        xaxis=dict(
            title="WRF observations"
        ),

        yaxis=dict(
            title="Pressure anomaly (hPa)"
        ),

        template="plotly_white",

        hovermode="closest",

        margin=dict(
            l=70,
            r=40,
            t=80,
            b=80
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_path = (
        VISUAL_OUTPUT /
        "pressure_anomaly.html"
    )

    figure.write_html(
        output_path,
        include_plotlyjs=True,
        config={
            "responsive": True,
            "displaylogo": False,
            "scrollZoom": True
        }
    )

    print(
        "\nPressure anomaly graph saved:"
    )

    print(output_path)


# ============================================================
# SURFACE PRESSURE DISTRIBUTION — BOX PLOT
# ============================================================

def pressure_distribution_box_graph(
    data,
    center_lat,
    center_lon,
    radius_km
):
    """
    Create a surface-pressure box plot by distance zone.

    Zones:
        0–5 km
        5–10 km
        10–15 km
    """

    if data is None or data.empty:
        print(
            "\nPressure distribution skipped:"
            "\nNo nearby WRF pressure data."
        )
        return

    plot_data = prepare_plot_data(data).copy()

    # --------------------------------------------------------
    # Convert pressure: Pa -> hPa
    # --------------------------------------------------------

    plot_data["Pressure_hPa"] = pd.to_numeric(
        plot_data["psfc"],
        errors="coerce"
    ) / 100.0

    plot_data = plot_data.dropna(
        subset=[
            "Pressure_hPa",
            "Distance_km"
        ]
    )

    if plot_data.empty:
        print(
            "\nPressure distribution skipped:"
            "\nNo valid pressure data."
        )
        return

    # --------------------------------------------------------
    # Create distance zones
    # --------------------------------------------------------

    def distance_zone(distance):

        if distance <= 5:
            return "0–5 km"

        elif distance <= 10:
            return "5–10 km"

        else:
            return "10–15 km"

    plot_data["DistanceZone"] = (
        plot_data["Distance_km"]
        .apply(distance_zone)
    )

    # --------------------------------------------------------
    # Box plot
    # --------------------------------------------------------

    figure = go.Figure()

    zone_order = [
        "0–5 km",
        "5–10 km",
        "10–15 km"
    ]

    for zone in zone_order:

        zone_data = plot_data[
            plot_data["DistanceZone"] == zone
        ]

        if zone_data.empty:
            continue

        figure.add_trace(
            go.Box(
                y=zone_data["Pressure_hPa"],

                name=zone,

                boxpoints="outliers",

                customdata=zone_data[
                    [
                        "time",
                        "lat",
                        "lon",
                        "Distance_km"
                    ]
                ],

                hovertemplate=(
                    "<b>Surface Pressure</b><br>"
                    "Pressure: %{y:.2f} hPa<br>"
                    "Time: %{customdata[0]}<br>"
                    "Latitude: %{customdata[1]:.5f}° N<br>"
                    "Longitude: %{customdata[2]:.5f}° E<br>"
                    "Distance: %{customdata[3]:.2f} km"
                    "<extra></extra>"
                )
            )
        )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    figure.update_layout(

        title=(
            "Surface Pressure Distribution by Distance"
            f" — {radius_km:.0f} km radius"
        ),

        xaxis=dict(
            title="Distance from selected coordinate"
        ),

        yaxis=dict(
            title="Surface Pressure (hPa)"
        ),

        template="plotly_white",

        hovermode="closest",

        margin=dict(
            l=70,
            r=40,
            t=80,
            b=80
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_path = (
        VISUAL_OUTPUT /
        "pressure_distribution.html"
    )

    figure.write_html(
        output_path,
        include_plotlyjs=True,
        config={
            "responsive": True,
            "displaylogo": False,
            "scrollZoom": True
        }
    )

    print(
        "\nPressure distribution graph saved:"
    )

    print(output_path)
# ============================================================
# MAIN RUNNER
# ============================================================

def run_trend_analysis():

    print("\n")
    print("=" * 60)
    print("EARTHWATCH DYNAMIC TREND ANALYSIS")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Load WRF data
    # --------------------------------------------------------

    data = import_wrf_data()

    if data is None:
        print("\nAnalysis stopped.")
        return

    # --------------------------------------------------------
    # 2. Selected coordinate
    # --------------------------------------------------------
    # Temporary test coordinate.
    # Later Harshini's frontend will provide these values.

    center_lat = CENTER_LAT
    center_lon = CENTER_LON

    # --------------------------------------------------------
    # 3. Select WRF observations around the coordinate
    # --------------------------------------------------------

    nearby_data = select_nearby_coordinates(
        data=data,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=RADIUS_KM
    )

    if nearby_data.empty:
        print(
            "\nNo WRF observations found "
            "for the selected coordinate."
        )
        return

    # --------------------------------------------------------
    # 4. Generate temperature trend
    # --------------------------------------------------------

    temperature_trend_graph(
        data=nearby_data,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=RADIUS_KM
    )

    # --------------------------------------------------------
    # 5. Generate rainfall trend
    # --------------------------------------------------------

    rainfall_trend_graph(
        data=nearby_data,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=RADIUS_KM
    )

    # --------------------------------------------------------
    # 6. Generate wind trend
    # --------------------------------------------------------

    wind_trend_graph(
        data=nearby_data,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=RADIUS_KM
    )
    # --------------------------------------------------------
    # 7. Generate wind frequency distribution
    # --------------------------------------------------------

    wind_frequency_distribution(
        data=nearby_data,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=RADIUS_KM
    )
    # --------------------------------------------------------
    # Surface pressure analysis
    # --------------------------------------------------------

    pressure_anomaly_bar_graph(
        data=nearby_data,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=RADIUS_KM
    )

    pressure_distribution_box_graph(
        data=nearby_data,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=RADIUS_KM
    )
    # --------------------------------------------------------
    # 7. Summary
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("EARTHWATCH TREND ANALYSIS COMPLETED")
    print("=" * 60)

    print(
        f"\nCenter:"
        f" {center_lat}° N, "
        f"{center_lon}° E"
    )

    print(
        f"Radius:"
        f" {RADIUS_KM} km"
    )

    print(
        f"WRF observations selected:"
        f" {len(nearby_data):,}"
    )

    print("\nGenerated graphs:")

    print(
        f"Temperature:"
        f"\n{VISUAL_OUTPUT / 'temperature_trend.html'}"
    )

    print(
        f"\nRainfall:"
        f"\n{VISUAL_OUTPUT / 'rainfall_trend.html'}"
    )

    print(
        f"\nWind:"
        f"\n{VISUAL_OUTPUT / 'wind_trend.html'}"
    )
