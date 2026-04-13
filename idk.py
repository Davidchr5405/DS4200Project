import pandas as pd
import altair as alt

# -----------------------------
# 1. Load the 201608 Hubway file
# -----------------------------
df = pd.read_csv("helpme/DS4200Project/201608-hubway-tripdata.csv")

# -----------------------------
# 2. Clean column names
# -----------------------------
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Check columns (optional)
print(df.columns)

# -----------------------------
# 3. Convert time + extract hour
# -----------------------------
df["starttime"] = pd.to_datetime(df["starttime"], errors="coerce")
df["hour"] = df["starttime"].dt.hour

# -----------------------------
# 4. Clean user type
# -----------------------------
df["usertype"] = df["usertype"].str.strip().str.lower()

def fix_user_type(x):
    if x == "subscriber":
        return "Member"
    elif x == "customer":
        return "Casual"
    else:
        return None

df["rider_type"] = df["usertype"].apply(fix_user_type)

# Drop missing
df = df.dropna(subset=["rider_type", "hour", "tripduration"])

# Convert duration to minutes
df["trip_minutes"] = df["tripduration"] / 60

# -----------------------------
# 5. Chart 1: Stacked bar (rides by hour)
# -----------------------------
rides_by_hour = (
    df.groupby(["hour", "rider_type"])
      .size()
      .reset_index(name="ride_count")
)

chart1 = alt.Chart(rides_by_hour).mark_bar().encode(
    x=alt.X("hour:O", title="Hour of Day"),
    y=alt.Y("ride_count:Q", title="Number of Rides"),
    color=alt.Color("rider_type:N", title="Rider Type"),
    tooltip=["hour", "rider_type", "ride_count"]
).properties(
    title="Number of Bluebikes Rides by Hour (Member vs Casual)",
    width=700,
    height=400
)

# -----------------------------
# 6. Chart 2: Avg duration
# -----------------------------
avg_duration = (
    df.groupby("rider_type")["trip_minutes"]
      .mean()
      .reset_index()
)

chart2 = alt.Chart(avg_duration).mark_bar().encode(
    x=alt.X("rider_type:N", title="Rider Type"),
    y=alt.Y("trip_minutes:Q", title="Avg Trip Duration (Minutes)"),
    color="rider_type:N",
    tooltip=[alt.Tooltip("trip_minutes:Q", format=".2f")]
).properties(
    title="Average Trip Duration by Rider Type",
    width=500,
    height=400
)

# -----------------------------
# 7. Save charts
# -----------------------------
chart1.save("rides_by_hour_member_vs_casual.html")
chart2.save("avg_duration_member_vs_casual.html")

print("Charts saved!")
