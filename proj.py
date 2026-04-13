import pandas as pd
import folium
from folium.plugins import HeatMap, HeatMapWithTime
import webbrowser
import os


CSV_PATH = "ds4200 proj/201608-hubway-tripdata.csv"  
OUTPUT = "bluebikes_heatmap.html"


def load(path):
    df = pd.read_csv(path)

    # normalize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # parse timestamps
    df["starttime"] = pd.to_datetime(df["starttime"], errors="coerce")
    df["stoptime"] = pd.to_datetime(df["stoptime"], errors="coerce")
    df["start_hour"] = df["starttime"].dt.hour

    # drop rows missing coordinates
    df = df.dropna(subset=[
        "start_station_latitude", "start_station_longitude",
        "end_station_latitude", "end_station_longitude",
    ])

    return df


def station_stats(df):
    grouped = (
        df.groupby(["start_station_id", "start_station_name",
                     "start_station_latitude", "start_station_longitude"])
        .agg(
            total_trips=("tripduration", "count"),
            subscribers=("usertype", lambda x: (x == "Subscriber").sum()),
            customers=("usertype", lambda x: (x == "Customer").sum()),
            avg_duration=("tripduration", "mean"),
        )
        .reset_index()
    )
    return grouped


def heatmap_points(df, usertype=None):
    sub = df.copy()
    if usertype:
        sub = sub[sub["usertype"] == usertype]
    points = (
        sub.groupby(["start_station_latitude", "start_station_longitude"])
        .size()
        .reset_index(name="count")
    )
    return points[["start_station_latitude", "start_station_longitude", "count"]].values.tolist()


def heatmap_by_hour(df):
    hourly = []
    for h in range(24):
        hour_df = df[df["start_hour"] == h]
        pts = (
            hour_df.groupby(["start_station_latitude", "start_station_longitude"])
            .size()
            .reset_index(name="count")
        )
        hourly.append(pts[["start_station_latitude", "start_station_longitude", "count"]].values.tolist())
    return hourly


def build_map(df):
    m = folium.Map(
    location=[42.3601, -71.0889],
    zoom_start=13,
    tiles="CartoDB positron",
)

    stats = station_stats(df)

    # All riders heatmap
    all_pts = heatmap_points(df)
    HeatMap(
        all_pts,
        name="All Riders (Heatmap)",
        radius=20,
        blur=15,
        max_zoom=15,
    ).add_to(m)

    # Subscriber heatmap
    sub_pts = heatmap_points(df, "Subscriber")
    fg_sub = folium.FeatureGroup(name="Subscribers (Heatmap)", show=False)
    HeatMap(
        sub_pts,
        radius=20,
        blur=15,
        max_zoom=15,
    ).add_to(fg_sub)
    fg_sub.add_to(m)

    # Customer heatmap
    cust_pts = heatmap_points(df, "Customer")
    fg_cust = folium.FeatureGroup(name="Customers (Heatmap)", show=False)
    HeatMap(
        cust_pts,
        radius=20,
        blur=15,
        max_zoom=15,
    ).add_to(fg_cust)
    fg_cust.add_to(m)

    # Time slider
    hourly_pts = heatmap_by_hour(df)
    non_empty = [h for h in hourly_pts if len(h) > 0]
    if len(non_empty) > 1:
        HeatMapWithTime(
            hourly_pts,
            name="Time Slider (All Riders)",
            index=[f"{h:02d}:00" for h in range(24)],
            radius=20,
            auto_play=False,
            max_opacity=0.8,
            speed_step=1,
        ).add_to(m)

    # Circle markers with popups
    fg_circles = folium.FeatureGroup(name="Station Markers", show=True)
    max_trips = stats["total_trips"].max() if len(stats) > 0 else 1

    for _, row in stats.iterrows():
        ratio = row["subscribers"] / row["total_trips"] if row["total_trips"] > 0 else 0.5
        r = int(255 * (1 - ratio))
        g = int(200 * ratio)
        b = int(100 * ratio)
        color = f"#{r:02x}{g:02x}{b:02x}"

        radius = 5 + 20 * (row["total_trips"] / max_trips)

        popup_html = (
            f"<b>{row['start_station_name']}</b><br>"
            f"Total trips: {int(row['total_trips'])}<br>"
            f"Subscribers: {int(row['subscribers'])}<br>"
            f"Customers: {int(row['customers'])}<br>"
            f"Avg duration: {row['avg_duration']:.0f}s"
        )

        folium.CircleMarker(
            location=[row["start_station_latitude"], row["start_station_longitude"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
        ).add_to(fg_circles)

    fg_circles.add_to(m)

    # Layer control
    folium.LayerControl(collapsed=False).add_to(m)

    return m


if __name__ == "__main__":
    df = load(CSV_PATH)

    m = build_map(df)

    m.save(OUTPUT)
    print(f"Saved to {OUTPUT}")

    webbrowser.open("file://" + os.path.abspath(OUTPUT))