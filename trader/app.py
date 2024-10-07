import dash
from dash import dcc, html, no_update
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

from .trader import Trader

app = dash.Dash(__name__)
tdr = Trader()

# Layout with a hidden store
app.layout = html.Div([
    html.Button(id='add-data-button', children="Add Data"),
    dcc.Dropdown([el[1] for el in tdr.broker.api.get_instruments()], 'EUR_USD', id='instruments-dropdown'),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
    dcc.Store(id='data-store'),
    html.Div(id='candlestick-subplot'),
])

@app.callback(
    Input('add-data-button', 'n_clicks'),
    State('instruments-dropdown', 'value')
)
def add_data(n, instrument):
    tdr.add_data([instrument])

# Callback to update the store data with the latest from Trader
@app.callback(
    Output('data-store', 'data'),
    Input('interval-component', 'n_intervals'),
    State('data-store', 'data')  # Get the previously stored data
)
def update_data_store(n, store):
    new_data = ';'.join([str(d) for d in tdr.data])
    if store:
        _, current_data = store
        has_updated = not (current_data == new_data)
    else:
        has_updated = True
    return has_updated, new_data


# Callback to update the graph when the data in the store changes
@app.callback(
    Output('candlestick-subplot', 'children'),
    Input('data-store', 'data'),
    State('candlestick-subplot', 'children')  # Preserve zoom/layout settings
)
def update_graphs(data_store, current_figure):
    has_data_changed, _ = data_store
    if not has_data_changed:
        return no_update  # No updates if data is unchanged

    figures = []
    for i, data in enumerate(tdr.data):
        fig = go.Figure(data=[
            go.Candlestick(x=data.df.index, open=data.df.open, high=data.df.high, low=data.df.low, close=data.df.close)
        ])
        fig.update_layout(title=str(data), xaxis_rangeslider_visible=False)

        figures.append(dcc.Graph(id=f'graph-{i}', figure=fig))
    return figures

app.run_server(debug=True)

print("http://127.0.0.1:8050/")

