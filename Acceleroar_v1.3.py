import datetime
import random
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from yzutil import YzDataClient
from yzutil import TaylorDB


# Retrieve tick data
def load_tick_data(instrument_id):
    # Initialize the data api and retrieve tick data
    tl = TaylorDB('47.100.224.135')
    df = tl.query_ticks(instrument_id, '2019-10-22 08:55:00','2019-10-22 16:00:00',
                        columns=['instrument_id', 'exchange_time', 'last_price', 'volume', 'turnover'])
    return df


# calculate 'vwap', 'delta_vwap' and 'ddelta_vwap' (delta of delta_vwap)
def vwap_calculator(df, freq_str):
    """This function calculates volume weighted average price ('vwap'), change/delta of vwap ('delta_vwap') and
    change of delta_vwap ('ddelta_vwap) based on different time frequencies.

    Args:
        df (DataFrame): tick data retrieved from TaylorDB
        freq_str (str): time frequency string such as '10S' (10 seconds) or '1Min' (1 Minute)

    Returns:
        resample_trading_df (DataFrame): data frame that contains vwap, delta_vwap and ddelta_vwap with user-specified
                                            frequency window, excluding tea break and lunch break data
    """

    # Step1, resample data set into user-specified frequencies, e.g. 10 seconds ('10S'), 1 minute ('1Min')

    # 'pad' method: propagate last valid observation forward to next valid obs
    resample_df = df.set_index('exchange_time').resample(freq_str).pad()
    resample_df.iloc[0] = df.set_index('exchange_time').iloc[0]
    resample_df['volume_shift'] = resample_df['volume'].shift(1)
    resample_df['turnover_shift'] = resample_df['turnover'].shift(1)

    # Step2, EXCLUDE data occurs during tea break and lunch break
    date_time_list = str(resample_df.index[0]).split(' ')

    # morning break from 10:15:00 to 10:30:00
    morning_break_start = date_time_list[0] + ' 10:15:00'
    morning_break_start = datetime.datetime.strptime(morning_break_start, '%Y-%m-%d %H:%M:%S')
    morning_break_end = date_time_list[0] + ' 10:30:00'
    morning_break_end = datetime.datetime.strptime(morning_break_end, '%Y-%m-%d %H:%M:%S')

    # lunch break from 11:30:00 to 13:30:00
    lunch_break_start = date_time_list[0] + ' 11:30:00'
    lunch_break_start = datetime.datetime.strptime(lunch_break_start, '%Y-%m-%d %H:%M:%S')
    lunch_break_end = date_time_list[0] + ' 13:30:00'
    lunch_break_end = datetime.datetime.strptime(lunch_break_end, '%Y-%m-%d %H:%M:%S')

    # create selection index for tea break and lunch break
    morning_break_index = (resample_df.index > morning_break_start) & (resample_df.index <= morning_break_end)
    lunch_break_index = (resample_df.index > lunch_break_start) & (resample_df.index <= lunch_break_end)

    # extract product_id from instrument_id to decide if there is a tea break for the product
    instr_id = resample_df['instrument_id'][0]
    product_id = instr_id[0:-4] if instr_id[-4].isdigit() else instr_id[0:-3]

    if product_id not in ['IC', 'IF', 'IH', 'T', 'TF', 'TS']:
        # select data by data index (for products with tea break)
        resample_trading_df = resample_df[~morning_break_index & ~lunch_break_index]
        # no tea break for the following 6 products
    elif product_id in ['IC', 'IF', 'IH', 'T', 'TF', 'TS']:
        resample_trading_df = resample_df[~lunch_break_index]
    else:
        print('Error: product_id out of range. Please try another one.')

    # Step3, calculate volume weighted average price ('vwap') and delta of vwap

    # calculate 'vwap' and use 'ffill' method to fill the NaN value
    resample_trading_df['vwap'] = (resample_trading_df['turnover'] - resample_trading_df['turnover_shift']) / (
                resample_trading_df['volume'] - resample_trading_df['volume_shift'])
    resample_trading_df = resample_trading_df.fillna(method='ffill')

    # calculate delta of 'vwap', i.e. change of vwap period by period
    resample_trading_df['delta_vwap'] = resample_trading_df['vwap'] - resample_trading_df['vwap'].shift(1)

    # calculate delta of delta of 'vwap', i.e. change of change of vwap period by period
    resample_trading_df['ddelta_vwap'] = resample_trading_df['delta_vwap'] - resample_trading_df['delta_vwap'].shift(1)

    return resample_trading_df.round(2)


# Initialize data api
yz = YzDataClient("bruce@yangzeinvest.com", "bruce123")

# Get info of all the main contracts
all_main_contracts_df = yz.get_roll_feature('TEZA2', 'trade_code', shift=0)

# Get id for produects only traded on Shanghai Futures Exchange ('SHFE') and Dailian Commodity Exchange ('DCE')
shfe_dce_index = (yz.products['exchange'] == 'SHFE') | (yz.products['exchange'] == 'DCE')
products_shfe_dce = pd.DataFrame(yz.products[shfe_dce_index]['product_id'])

products_id_shfe_dce = products_shfe_dce.applymap(lambda x: x.split('.')[0])
products_id_shfe_dce.rename(columns={'product_id': 'product_short_id'}, inplace=True)

# Randomly select 6 products
random_id_list = random.sample(list(products_id_shfe_dce['product_short_id']), 6)

# Retrieve tick data of main contract from randomly select product
# for product_id in random_id_list:
product_id = random_id_list[0]
instrument_id = all_main_contracts_df[product_id][-1]
ticks_df = load_tick_data(instrument_id)
resample_trading_df = vwap_calculator(ticks_df, '1Min')
resample_trading_10S_df = vwap_calculator(ticks_df, '10S')
resample_trading_6M_df = vwap_calculator(ticks_df, '6Min')

# Initialize figure with subplots
fig = make_subplots(rows=4, cols=3,
                    subplot_titles=('10 Seconds Window', '1 Minute Window', '6 Minutes Window'))

# Add traces for 10S
exchange_time_10S = resample_trading_10S_df.index

fig.add_trace(go.Scatter(x=exchange_time_10S, y=resample_trading_10S_df['last_price'],
                         name='last_price', line=dict(color='rgb(99,110,250)')), row=1, col=1)
fig.add_trace(go.Scatter(x=exchange_time_10S, y=resample_trading_10S_df['vwap'],
                         name='vwap', line=dict(color='rgb(239,85,59)')), row=2, col=1)
fig.add_trace(go.Scatter(x=exchange_time_10S, y=resample_trading_10S_df['delta_vwap'],
                         name='delta_vwap', line=dict(color='rgb(0,204,150)')), row=3, col=1)
fig.add_trace(go.Scatter(x=exchange_time_10S, y=resample_trading_10S_df['ddelta_vwap'],
                         name='ddelta_vwap', line=dict(color='rgb(171,99,250)')), row=4, col=1)

# Add traces for 1Min
exchange_time_1M = resample_trading_1M_df.index

fig.add_trace(go.Scatter(x=exchange_time_1M, y=resample_trading_1M_df['last_price'],
                         showlegend=False, line=dict(color='rgb(99,110,250)')), row=1, col=2)
fig.add_trace(go.Scatter(x=exchange_time_1M, y=resample_trading_1M_df['vwap'],
                         showlegend=False, line=dict(color='rgb(239,85,59)')), row=2, col=2)
fig.add_trace(go.Scatter(x=exchange_time_1M, y=resample_trading_1M_df['delta_vwap'],
                         showlegend=False, line=dict(color='rgb(0,204,150)')), row=3, col=2)
fig.add_trace(go.Scatter(x=exchange_time_1M, y=resample_trading_1M_df['ddelta_vwap'],
                         showlegend=False, line=dict(color='rgb(171,99,250)')), row=4, col=2)

# Add traces for 6Min
exchange_time_6M = resample_trading_6M_df.index

fig.add_trace(go.Scatter(x=exchange_time_6M, y=resample_trading_6M_df['last_price'],
                         showlegend=False, line=dict(color='rgb(99,110,250)')), row=1, col=3)
fig.add_trace(go.Scatter(x=exchange_time_6M, y=resample_trading_6M_df['vwap'],
                         showlegend=False, line=dict(color='rgb(239,85,59)')), row=2, col=3)
fig.add_trace(go.Scatter(x=exchange_time_6M, y=resample_trading_6M_df['delta_vwap'],
                         showlegend=False, line=dict(color='rgb(0,204,150)')), row=3, col=3)
fig.add_trace(go.Scatter(x=exchange_time_6M, y=resample_trading_6M_df['ddelta_vwap'],
                         showlegend=False, line=dict(color='rgb(171,99,250)')), row=4, col=3)

# Update xaxis properties
for row in range(1, 5):
    for col in range(1, 4):
        fig.update_xaxes(title_text='exchange_time', row=row, col=col)

# Update yaxis properties
for col in range(1, 4):
    fig.update_yaxes(title_text='last_price', row=1, col=col)
    fig.update_yaxes(title_text='vwap', row=2, col=col)
    fig.update_yaxes(title_text='delta_vwap', row=3, col=col)
    fig.update_yaxes(title_text='ddelta_vwap', row=4, col=col)

# Update height, weight and title
fig.update_layout(height=1000, width=1900,
                  title_text='Subplots_' + instrument_id + '__10seconds_vs_1minute_vs_6minutes')

fig.show()

