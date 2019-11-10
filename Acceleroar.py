import datetime
import pandas as pd
from yzutil import TaylorDB


def vwap_calculator(data_frame, freq_str):
    """This function calculates volume weighted average price ('vwap'), change/delta of vwap ('delta_vwap') and
    change of delta_vwap ('ddelta_vwap) based on different time frequencies.

    Args:
        data_frame (DataFrame): tick data retrieved from TaylorDB
        freq_str (str): time frequency string such as '10S' (10 seconds) or '1Min' (1 Minute)

    Returns:
        resample_trading_df (DataFrame): data frame that contains vwap, delta_vwap and ddelta_vwap with user-specified
                                        frequency window, excluding tea break and lunch break data
    """

    # Step1, resample data set into user-specified frequencies, e.g. 10 seconds ('10S'), 1 minute ('1Min')

    # 'pad' method: propagate last valid observation forward to next valid obs
    resample_df = data_frame.set_index('exchange_time').resample(freq_str).pad()
    resample_df.iloc[0] = data_frame.set_index('exchange_time').iloc[0]
    resample_df['volume_shift'] = resample_df['volume'].shift(1)
    resample_df['turnover_shift'] = resample_df['turnover'].shift(1)

    # Step2, EXCLUDE data occurs during tea break and lunch break
    date_time_list = str(resample_df.index[0]).split(' ')

    # tea break from 10:15:00 to 10:30:00
    tea_break_start = date_time_list[0] + ' 10:15:00'
    tea_break_start = datetime.datetime.strptime(tea_break_start, '%Y-%m-%d %H:%M:%S')
    tea_break_end = date_time_list[0] + ' 10:30:00'
    tea_break_end = datetime.datetime.strptime(tea_break_end, '%Y-%m-%d %H:%M:%S')

    # tea break from 11:30:00 to 13:30:00
    lunch_break_start = date_time_list[0] + ' 11:30:00'
    lunch_break_start = datetime.datetime.strptime(lunch_break_start, '%Y-%m-%d %H:%M:%S')
    lunch_break_end = date_time_list[0] + ' 13:30:00'
    lunch_break_end = datetime.datetime.strptime(lunch_break_end, '%Y-%m-%d %H:%M:%S')

    # select data by data index
    tea_break_index = (resample_df.index > tea_break_start) & (resample_df.index <= tea_break_end)
    lunch_break_index = (resample_df.index > lunch_break_start) & (resample_df.index <= lunch_break_end)
    resample_trading_df = resample_df[~tea_break_index & ~lunch_break_index]

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


# set up data api
instr_id = 'i1912'
tl = TaylorDB('47.100.224.135')
df = tl.query_ticks(instr_id, '2019-10-22 08:50:00', '2019-10-22 16:00:00',
                    columns=['instrument_id', 'exchange_time', 'last_price', 'volume', 'turnover'])

freq_list = ['10S', '1Min', '6Min']

for freq in freq_list:
    resample_trading_df = vwap_calculator(df, freq)
    resample_trading_df.to_csv('D:/Yangze_Investment/Task5_Acceleroar/' + instr_id + '_resample_new_' + freq + '.csv')
