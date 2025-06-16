import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timezone
import cloudscraper  # does not work with requests module

# Forex factory constants
IMPACT_TYPES = {"Non-Economic": 0, "Low Impact Expected": 1, "Medium Impact Expected": 2, "High Impact Expected": 3}
CURRENCIES = {"AUD": 1, "CAD": 2, "CHF": 3, "CNY": 4, "EUR": 5, "GBP": 6, "JPY": 7, "NZD": 8, "USD": 9}
EVENT_TYPES = {"Growth": 1, "Inflation": 2, "Employment": 3, "Central Bank": 4, "Bonds": 5,
               "Housing": 7, "Consumer Surveys": 8, "Business Surveys": 9, "Speeches": 10, "Misc": 11}

scraper = cloudscraper.create_scraper()
scraper.get(r"https://www.forexfactory.com/calendar")
cookies = scraper.cookies.get_dict()

url = r"https://www.forexfactory.com/calendar/apply-settings/1?navigation=0"

def get_economic_data(
    begin_date: str = None,
    end_date: str = None,
    currencies: list = None,
    event_types: list = None,
    impacts: list = None,
    utc: bool = True,
    raw_output: bool = False,
) -> pd.DataFrame:
    """
    Fetches economic event data from ForexFactory.

    Constraints:
    - **Only 2 months of data** can be fetched at once.
    - If `end_date` is not specified, **only `begin_date` is fetched**.
    - If no date filters are specified, **the default view is the current week**.

    Args:
        begin_date (str, optional): Start date in ISO format (YYYY-MM-DD).
        end_date (str, optional): End date in ISO format (YYYY-MM-DD).
        currencies (list[str | int], optional): List of currency codes or indices.
        event_types (list[str | int], optional): List of event types (names or indices).
        impacts (list[str | int], optional): List of impact levels (names or indices).
        utc (bool, optional): If `True`, converts timestamps to UTC. Default is `True`.
        raw_output (bool, optional): If `True`, returns raw API output without modifications. Default is `False`.

    Returns:
        pd.DataFrame: DataFrame containing:
            - `datetime` (Timestamp)
            - `currency` (str)
            - `name` (str) – Event name
            - `impact` (int) – Impact level (0-3)

    To get valid values for `currencies`, `event_types`, and `impacts`:
        - `IMPACT_TYPES`
        - `CURRENCIES`
        - `EVENT_TYPES`
    """

    # feature to make use of both names and indices for currencies, event types, and impacts
    def map_values(values, mapping, name):
        if values is None:
            return None
        mapped_values = []
        for value in values:
            if isinstance(value, int) and value in mapping.values():
                mapped_values.append(value)
            elif isinstance(value, str) and value in mapping:
                mapped_values.append(mapping[value])
            else:
                raise ValueError(f"Invalid {name}: {value}")
        return mapped_values

    # convert input filters (allowing both names and indices)
    mapped_currencies = map_values(currencies, CURRENCIES, "currency")
    mapped_event_types = map_values(event_types, EVENT_TYPES, "event type")
    mapped_impacts = map_values(impacts, IMPACT_TYPES, "impact level")

    # add query parameters, if none are provided, the default view is this week with all currencies and event types
    payload = {
        "begin_date": begin_date,
        "end_date": end_date,
        "currencies": mapped_currencies,
        "event_types": mapped_event_types,
        "impacts": mapped_impacts
    }

    # warn max 2 months
    if begin_date and end_date:
        if (datetime.fromisoformat(end_date) - datetime.fromisoformat(begin_date)).days > 60:
            print("Warning: Max 2 months of data can be requested")

    # request
    response = scraper.post(url, cookies=cookies, json=payload)

    days = response.json()["days"]
    events = [event for day in days for event in day["events"]]  # flatten nested events
    df_news = pd.DataFrame(events)

    df_news["datetime"] = df_news["dateline"].map(datetime.fromtimestamp)
    if utc:
        local_time = datetime.now()
        utc_time = datetime.now(timezone.utc)
        utc_offset = local_time - utc_time.replace(tzinfo=None)
        df_news["datetime"] = df_news["datetime"] - utc_offset
    df_news.set_index("datetime", inplace=True)

    # return raw output if requested
    if raw_output:
        return df_news

    df_news["impact"] = df_news["impactTitle"].map(IMPACT_TYPES)

    # delete some columns
    df_news = df_news[["currency", "name", "impact", "actual", "previous", "revision", "forecast"]]

    return df_news
