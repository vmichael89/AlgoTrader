import datetime
import json
import re
import pandas as pd
import cloudscraper

scraper = cloudscraper.create_scraper()
url = r"https://www.forexfactory.com/calendar?week=dec01.2024"

response = scraper.get(url)

events_matches = re.findall(r'"events":\[(\{[^\]]*\})\]', response.text)
parsed_data = json.loads("[" + ",".join(events_matches) + "]")

df = pd.DataFrame(parsed_data)

utc_correction = datetime.datetime.now() - datetime.datetime.utcnow()

df["datetime"] = df["dateline"].map(datetime.datetime.fromtimestamp) - utc_correction

df = df[["datetime", "currency", "name", "impactTitle"]]
# important columns:
# name
# currency
# impactTitle
# datetime



#####

import os
os.chdir("../trader")
from trader.trader import Trader

trader = Trader()
trader.add_broker('oanda')
trader.add_data(['EUR_USD'], granularities="1min", start="2024-11-24", end="2024-11-30")
fig = trader.data[0].plot()



######

from plotly.graph_objects import Scatter

# Define color mapping for impact levels
impact_color_map = {
    "Low Impact Expected": "yellow",
    "Medium Impact Expected": "orange",
    "High Impact Expected": "red",
    "Non-Economic": "gray",  # Optional, for non-economic events
}

# Filter the DataFrame for EUR and USD data
filtered_df = df.loc[df["currency"].isin(["EUR", "USD"])]

# Add events as scatter markers on the candlestick chart
fig.add_trace(
    Scatter(
        x=filtered_df["datetime"],
        y=[fig.data[0].high.max()] * len(filtered_df),  # Position markers above the chart's upper limit
        mode="markers+text",
        text=filtered_df["name"],
        textposition="top center",
        marker=dict(
            size=10,
            color="red",  # Adjust marker color if needed
            symbol="circle"
        ),
        name="Events"
    )
)

# Add vertical lines for events
for i, row in filtered_df.iterrows():
    fig.add_shape(
        type="line",
        x0=row["datetime"],
        x1=row["datetime"],
        y0=fig.data[0].high.min(),
        y1=fig.data[0].high.max(),
        line=dict(
            color=impact_color_map.get(row["impactTitle"], "black"),  # Default to black if impactTitle is missing
            width=1,  # Adjust line width if needed
            dash="dot",
        ),
        name="Event Line"
    )

# Show the updated figure
fig.show(renderer="browser")


# Filtere nur EUR und USD
filtered_df = df[df['currency'].isin(['EUR', 'USD'])]
# Funktion zum Formatieren von datetime
def format_datetime(dt):
    return f"{dt.year},{dt.month},{dt.day},{dt.hour},{dt.minute},0"
# Gruppiere nach `impactTitle` und erstelle Pakete
result = {}
for impact, group in filtered_df.groupby('impactTitle'):
    formatted_times = group['datetime'].apply(pd.to_datetime).apply(format_datetime)
    result[impact] = "GMT;" + ";".join(formatted_times)
# Ergebnisse anzeigen oder speichern
for impact, formatted_data in result.items():
    print(f"Impact: {impact}")
    print(formatted_data)
    print("\n")