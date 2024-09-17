from trader.algos.directional_change import *

instruments = ['EUR_USD', 'GBP_USD', 'USD_CHF', 'AUD_USD']
start_date = '2024-07-29'
end_date = '2024-08-20'
granularity = 'H1'
price = 'M'

if API_INSTALLED:
    api = tpqoa.tpqoa((Path('..') / 'trader' / 'config' / 'oanda.cfg').resolve().__str__())

# fetch or load data
list_of_df_data = []
for instr in instruments:
    print(instr, end='')
    file_path = Path('..') / 'data' / f'{instr}_{start_date}_{end_date}_{granularity}_{price}.csv'
    if not os.path.exists(file_path):
        print(" >> fetching from api", end='')
        if not API_INSTALLED:
            raise api_not_installed_error
        # fetch and rename columns
        df_data = (
            api.get_history(
                instrument=instr, start=start_date, end=end_date, granularity=granularity, price=price, localize=False)
            .rename(
                columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'volume': 'Volume'}))
        # save
        df_data.to_csv(file_path)
        print(f" >> saved to file >> {file_path}")
    else:
        print(" >> loading from file")
        df_data = pd.read_csv(file_path, index_col='time', parse_dates=True)

    list_of_df_data.append(df_data)

# plot data
fig, axs = plt.subplots(nrows=len(instruments), ncols=1, figsize=(10, len(instruments) * 4))
# axs should be a list - isn't the case if len(instruments) == 1
if len(instruments) == 1:
    axs = [axs]
# plot
for ax, df_data, instrument in zip(axs, list_of_df_data, instruments):
    ax.set_title(instrument)
    plot_data_mpl(df_data, ax)
fig.tight_layout()

# run directional change on all data
list_of_dc = []
for df_data, ax in zip(list_of_df_data, axs):
    sigma = df_data.close.iloc[0] * 0.001
    dc = DirectionalChange(sigma).get_extremes(df_data)
    dc.plot(ax)
    list_of_dc.append(dc)

# sigma factor slider
def update(val):
    for ax, dc, df_data in zip(axs, list_of_dc, list_of_df_data):
        sig = df_data.close.iloc[0] * val
        dc.get_extremes(df_data, sigma=sig).plot(ax)

# slider
axcolor = 'lightgoldenrodyellow'
axsig = plt.axes([0.15, 0.95, 0.65, 0.03], facecolor=axcolor)
ssig = Slider(axsig, 'Sigma', 0.0001, 0.01, valinit=0.001, valstep=0.0001)
ssig.on_changed(update)

plt.show()
