import os
import re
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import matplotlib.pyplot as plt
from windrose import WindroseAxes
from config import VALIDATED_DATA_PATH, VISUAL_OUTPUT, SUMMARY_REPORT


# ============================================================
# LOAD VALIDATED DATA
# ============================================================

def load_validated_data():
    return pd.read_csv(
        VALIDATED_DATA_PATH,
        parse_dates=["Time_stamp"]
    )


# ============================================================
# GRAPH 1 — TEMPERATURE + WIND SPEED TIME SERIES
# ============================================================

def time_series_graph(df=None):
    """
    Generate the existing Temperature + Wind Speed time-series graph.

    Uses:
        - first TEMP...AVG column
        - first WSS...AVG column

    Output:
        VISUAL_OUTPUT/time_series_graph.html
    """

    if df is None:
        df = load_validated_data().copy()
    else:
        df = df.copy()

    df = df.sort_values("Time_stamp")

    # Detect time frequency
    differences = df["Time_stamp"].diff().dropna()

    if differences.empty:
        raise ValueError("Not enough timestamp data to determine frequency.")

    inferred_freq = differences.mode().iloc[0]
    print(f"Detected time frequency: {inferred_freq}")

    # Reindex so missing time periods are visible as gaps
    full_index = pd.date_range(
        start=df["Time_stamp"].min(),
        end=df["Time_stamp"].max(),
        freq=inferred_freq
    )

    df = (
        df.set_index("Time_stamp")
          .reindex(full_index)
    )

    df.index.name = "Time_stamp"

    # Select relevant columns
    temp_cols = [
        col for col in df.columns
        if "TEMP" in col and "AVG" in col
    ]

    wind_cols = [
        col for col in df.columns
        if "WSS" in col
        and "AVG" in col
        and not col.startswith("FLAG_")
    ]

    selected_columns = temp_cols[:1] + wind_cols[:1]
    labels = ["Temperature (C)", "Wind Speed (m/s)"]
    colors = ["orange", "royalblue"]

    if len(selected_columns) < 2:
        raise ValueError(
            "TEMP or WSS AVG column not found. Cannot generate time-series graph."
        )

    # Plotly traces
    traces = [
        go.Scatter(
            x=df.index,
            y=df[col],
            mode="lines",
            name=label,
            line=dict(color=color),
            connectgaps=False
        )
        for col, label, color in zip(
            selected_columns,
            labels,
            colors
        )
    ]

    color_legend = (
        "<b>Color Guide</b><br>"
        f"<span style='color:orange'>{selected_columns[0]}</span><br>"
        f"<span style='color:royalblue'>{selected_columns[1]}</span>"
    )

    layout = go.Layout(
        title="Time Series Graph: Temperature & Wind Speed",
        xaxis=dict(
            title="Time",
            rangeslider=dict(visible=True)
        ),
        yaxis=dict(title="Sensor Values"),
        hovermode="closest",
        annotations=[
            dict(
                xref="paper",
                yref="paper",
                x=1.05,
                y=1,
                showarrow=False,
                align="left",
                text=color_legend,
                bordercolor="gray",
                borderwidth=1,
                bgcolor="white",
                opacity=0.85
            )
        ]
    )

    fig = go.Figure(
        data=traces,
        layout=layout
    )

    os.makedirs(VISUAL_OUTPUT, exist_ok=True)

    visual_path = os.path.join(
        VISUAL_OUTPUT,
        "time_series_graph.html"
    )

    fig.write_html(
        visual_path,
        include_plotlyjs="cdn"
    )

    summary_text = (
        f"\n[Graph: time_series_graph.html]\n"
        f"  Auto-detected frequency: {inferred_freq}\n"
        f"  Columns plotted: {', '.join(selected_columns)}\n"
        f"  Total records (with gaps): {len(df)}\n"
        f"  Date Range: {df.index.min()} to {df.index.max()}\n"
        f"  Graph saved at: {visual_path}\n"
    )

    os.makedirs(
        os.path.dirname(SUMMARY_REPORT),
        exist_ok=True
    )

    with open(SUMMARY_REPORT, "a") as f:
        f.write(summary_text)

    print(f"Time-series graph saved: {visual_path}")

    return df


# ============================================================
# GRAPH 2 — WINDROSE
# ============================================================

def extract_wind_height(col_name):
    """
    Extract sensor height from:
        WIND_WSS_050_S_01_AVG
        WIND_WDS_048_N_01_AVG
    """

    match = re.search(
        r"WIND_(?:WSS|WDS)_(\d+)_",
        col_name
    )

    return int(match.group(1)) if match else None


def find_wind_pair(df, preferred_direction_height=48,
                   preferred_speed_height=50,
                   max_difference=2):
    """
    Find the wind-direction / wind-speed pair.

    For the current NIWE visualization we prefer:
        Direction = 48 m
        Speed    = 50 m

    If those exact heights are not available, the closest valid pair
    within max_difference is selected.
    """

    all_cols = df.columns.tolist()

    wss_cols = [
        col for col in all_cols
        if "WIND_WSS_" in col
        and col.endswith("_AVG")
        and not col.startswith("FLAG_")
    ]

    wds_cols = [
        col for col in all_cols
        if "WIND_WDS_" in col
        and col.endswith("_AVG")
        and not col.startswith("FLAG_")
    ]

    speed_height_map = {}
    direction_height_map = {}

    for col in wss_cols:
        height = extract_wind_height(col)
        if height is not None:
            speed_height_map.setdefault(height, []).append(col)

    for col in wds_cols:
        height = extract_wind_height(col)
        if height is not None:
            direction_height_map.setdefault(height, []).append(col)

    # First try the exact pair used in the existing NIWE graph
    if (
        preferred_direction_height in direction_height_map
        and preferred_speed_height in speed_height_map
        and abs(
            preferred_direction_height -
            preferred_speed_height
        ) <= max_difference
    ):
        return (
            preferred_direction_height,
            preferred_speed_height,
            direction_height_map[preferred_direction_height][0],
            speed_height_map[preferred_speed_height][0]
        )

    # Otherwise find the closest available pair
    available_pairs = []

    for dh in direction_height_map:
        for sh in speed_height_map:
            difference = abs(dh - sh)

            if difference <= max_difference:
                available_pairs.append(
                    (
                        difference,
                        dh,
                        sh,
                        direction_height_map[dh][0],
                        speed_height_map[sh][0]
                    )
                )

    if not available_pairs:
        raise ValueError(
            "No valid wind direction/speed pair found "
            f"within {max_difference} m."
        )

    available_pairs.sort(
        key=lambda x: (
            x[0],
            abs(x[1] - preferred_direction_height),
            abs(x[2] - preferred_speed_height)
        )
    )

    _, dh, sh, direction_col, speed_col = available_pairs[0]

    return dh, sh, direction_col, speed_col


def windrose_graph(df=None):
    """
    Generate the existing NIWE windrose.

    Preferred current prototype:
        Direction = 48 m
        Speed    = 50 m

    Output:
        VISUAL_OUTPUT/windrose_48m_50m.png
    """

    if df is None:
        df = load_validated_data().copy()
    else:
        df = df.copy()

    os.makedirs(VISUAL_OUTPUT, exist_ok=True)
    os.makedirs(
        os.path.dirname(SUMMARY_REPORT),
        exist_ok=True
    )

    dh, sh, direction_col, speed_col = find_wind_pair(df)

    subset = df[
        [direction_col, speed_col]
    ].dropna()

    if subset.empty:
        raise ValueError(
            f"No valid data for direction {dh} m "
            f"and speed {sh} m."
        )

    data_count = len(subset)
    avg_speed = subset[speed_col].mean()
    max_speed = subset[speed_col].max()
    avg_direction = subset[direction_col].mean()

    fig = plt.figure(figsize=(12, 10))
    ax = WindroseAxes.from_ax(fig=fig)

    ax.bar(
        subset[direction_col],
        subset[speed_col],
        normed=True,
        opening=0.8,
        edgecolor="white",
        bins=6
    )

    ax.set_legend(
        title="Wind Speed (m/s)"
    )

    ax.set_title(
        f"Wind Rose - Direction {dh}m + Speed {sh}m",
        fontsize=14,
        pad=20
    )

    image_path = os.path.join(
        VISUAL_OUTPUT,
        f"windrose_{dh}m_{sh}m.png"
    )

    plt.savefig(
        image_path,
        bbox_inches="tight",
        dpi=300
    )

    plt.close()

    print(f"Windrose saved: {image_path}")

    # Append windrose information to the same summary report
    with open(SUMMARY_REPORT, "a") as f:
        f.write(
            f"\n[Graph: windrose_{dh}m_{sh}m.png]\n"
            f"  Direction Column: {direction_col}\n"
            f"  Speed Column: {speed_col}\n"
            f"  Valid Data Points: {data_count:,}\n"
            f"  Average Wind Speed: {avg_speed:.2f} m/s\n"
            f"  Maximum Wind Speed: {max_speed:.2f} m/s\n"
            f"  Average Wind Direction: {avg_direction:.1f}°\n"
            f"  Image Saved: {image_path}\n"
        )

    return image_path


# ============================================================
# COMBINED LOCAL WIND ANALYSIS
# ============================================================

def run_wind_analysis():
    """
    Run both local graphs from the same validated dataset.

    1. Temperature + Wind Speed time series
    2. NIWE Windrose
    """

    print("\n==============================================")
    print("EARTHWATCH LOCAL WIND ANALYSIS")
    print("==============================================")

    df = load_validated_data()

    print(f"Validated records loaded: {len(df):,}")
    print(
        f"Date range: "
        f"{df['Time_stamp'].min()} -> "
        f"{df['Time_stamp'].max()}"
    )

    print("\n[1/2] Generating time-series graph...")
    time_series_graph(df)

    print("\n[2/2] Generating windrose...")
    windrose_graph(df)

    print("\n==============================================")
    print("Both graphs generated successfully.")
    print(f"Output directory: {VISUAL_OUTPUT}")
    print("==============================================")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_wind_analysis()
