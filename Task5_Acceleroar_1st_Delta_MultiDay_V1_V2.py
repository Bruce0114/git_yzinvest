import datetime
import pandas as pd
from yzutil import TaylorDB


# Retrieve tick data - for user-specified 'instrument_id' and 'date'
def load_tick_data(instrument_id, date):
    tl = TaylorDB('47.100.224.135')
    df = tl.query_ticks(instrument_id, date + ' 08:55:00', date + ' 15:05:00',
                        columns=['instrument_id', 'exchange_time', 'last_price', 'volume', 'turnover'])
    return df
  
  
# Initialize YzDataClient
from yzutil import YzDataClient

yz = YzDataClient("bruce@yangzeinvest.com", "bruce123")


# Calculate 'vwap', 'delta_vwap' and 'ddelta_vwap' (delta of delta_vwap)
def vwap_calculator(yz, df, freq):
    
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
    resample_df = df.set_index('exchange_time').resample(freq).pad()
    resample_df.iloc[0] = df.set_index('exchange_time').iloc[0] # initialize by setting the 1st row
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
    # firstly get the multiplier for the product
    multiplier = yz.products['multiplier'][yz.products['short_name'] == product_id]
    resample_trading_df['vwap'] = (resample_trading_df['turnover'] - resample_trading_df['turnover_shift']) / (resample_trading_df['volume'] - resample_trading_df['volume_shift'])
    resample_trading_df['vwap'] = resample_trading_df['vwap'].apply(lambda x: x / multiplier)
    resample_trading_df = resample_trading_df.fillna(method='ffill')   
    
    # calculate delta of 'vwap', i.e. change of vwap period by period
    resample_trading_df['delta_vwap'] = resample_trading_df['vwap'] - resample_trading_df['vwap'].shift(1)
    
    # calculate delta of delta of 'vwap', i.e. change of change of vwap period by period
    resample_trading_df['ddelta_vwap'] = resample_trading_df['delta_vwap'] - resample_trading_df['delta_vwap'].shift(1)
    
    return resample_trading_df.round(2)
    
    
import datetime
from datetime import date
from matplotlib.dates import drange

def return_date_list(start, end):
    delta = datetime.timedelta(days=1) # set increment as one day
    float_date_list = drange(start, end, delta)

    date_list = []
    for day in range(len(float_date_list)):
        # create a dates list with YYYY-MM-DD date format
        date_list.append(date.fromordinal(int(float_date_list[day])).strftime('%Y-%m-%d'))

    return date_list
    
 
# Get info of all the main contracts

all_main_contracts_df = yz.get_roll_feature('TEZA2', 'trade_code', shift=0)


# Multi-days signal generation

# Version 1: Calculation First, Concatenation Next

import numpy as np
import datetime
from datetime import date
from matplotlib.dates import drange
from tabulate import tabulate
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Select products
product_id_series = ['ni']
# product_id_series = yz.products[(yz.products['exchange'] == 'DCE') | (yz.products['exchange'] == 'SHFE')]['short_name']

for product_id in product_id_series:
    # Select main contracts corresponding to the product id 
    instrument_id = all_main_contracts_df[product_id][-1]
    
    # Create a multi-day data container (only Series and DataFrame objs are valid)
    predict_direction_10S_multidays_df = pd.DataFrame()
    
    # Set start and end date
    start = date(2019, 11, 4)  # set date(YYYY, M, D) as the start date for data retrival
    end = date(2019, 11, 7)  
#     end = datetime.date.today() + datetime.timedelta(days=1)
    
    # Create a date list
    date_list = return_date_list(start, end)
    
    for date in date_list:
        ticks_df = load_tick_data(instrument_id, date)
        resample_trading_10S_df = vwap_calculator(yz, ticks_df, '10S')
#         resample_trading_1M_df = vwap_calculator(yz, ticks_df, '1Min')
#         resample_trading_6M_df = vwap_calculator(yz, ticks_df, '6Min')
       
        # ****** Creating Simple Trading Signal ******  

        # Step1: calculate rolling standard deviation (std.)
        
        # Lookback period initially set up at n=100
        rolling_std_d_10S = resample_trading_10S_df['delta_vwap'].rolling(100).std()
        
        # Step2: use rolling std. calculated from (t0 to ti) to standardize/normalize the value of delta_vwap at ti

        standard_delta_vwap_10S =  resample_trading_10S_df['delta_vwap'] / rolling_std_d_10S
        
        # Step3: use standardized new points of delta_vwap at ti to label Pti+1 (P for last_price)

        # three label categories for price change: 'increase', 'unchanged', 'decrease'
        
        # a).Construct price changes
        price_change_10S = resample_trading_10S_df['last_price'] - resample_trading_10S_df['last_price'].shift(1)

        # b).Construct labels of price changes: '1'(increase), '-1'(decrease), '0'(unchanged)
        label_price_change_10S = price_change_10S.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else (0 if x == 0 else np.nan)))
        
        # c).Bin values of 'standard_delta_vwap_10S' into discrete intervals('bins') with equal range
        bin_labels = [
                        '(-)5to4', '(-)4to3', '(-)3to2', '(-)2to1', '(-)1to0',
                        '(+)0to1', '(+)1to2', '(+)2to3', '(+)3to4', '(+)4to5'
                     ]

        bin_stanrdard_delta_10S = pd.cut(standard_delta_vwap_10S, 
                                         bins=np.linspace(-5, 5, 11), 
                                         labels=bin_labels, 
                                         right=False)
        
#         # d).Construct predicting data frame
        predict_direction_10S_df = pd.DataFrame()
        predict_direction_10S_df['instrument_id'] = resample_trading_10S_df['instrument_id']
#         predict_direction_10S_df['exchange_time'] = resample_trading_10S_df.reset_index('exchange_time')['exchange_time']
        predict_direction_10S_df['price_change_10S'] = price_change_10S
        predict_direction_10S_df['label_price_change_10S'] = label_price_change_10S
        predict_direction_10S_df['bin_stanrdard_delta_shift1'] = bin_stanrdard_delta_10S.shift(1)
        predict_direction_10S_df.reset_index(inplace=True)
        
        # concatenate data of multiple days (key lines)
        predict_direction_10S_multidays_df = pd.concat([predict_direction_10S_multidays_df,
                                                        predict_direction_10S_df])
    
    predict_direction_10S_multidays_df.reset_index(inplace=True)
        
    # Step4: calculate the probability of price increase/decrease/unchanged

    # a).Extract price change data based on bin values of standard delta_vwap
    price_change_minus_5to4_10S = predict_direction_10S_multidays_df[predict_direction_10S_multidays_df['bin_stanrdard_delta_shift1'] == '(-)5to4']
    price_change_minus_4to3_10S = predict_direction_10S_multidays_df[predict_direction_10S_multidays_df['bin_stanrdard_delta_shift1'] == '(-)4to3']
    price_change_minus_3to2_10S = predict_direction_10S_multidays_df[predict_direction_10S_multidays_df['bin_stanrdard_delta_shift1'] == '(-)3to2']
    price_change_minus_2to1_10S = predict_direction_10S_multidays_df[predict_direction_10S_multidays_df['bin_stanrdard_delta_shift1'] == '(-)2to1']
    price_change_minus_1to0_10S = predict_direction_10S_multidays_df[predict_direction_10S_multidays_df['bin_stanrdard_delta_shift1'] == '(-)1to0']
    price_change_plus_0to1_10S = predict_direction_10S_multidays_df[predict_direction_10S_multidays_df['bin_stanrdard_delta_shift1'] == '(+)0to1']
    price_change_plus_1to2_10S = predict_direction_10S_multidays_df[predict_direction_10S_multidays_df['bin_stanrdard_delta_shift1'] == '(+)1to2']
    price_change_plus_2to3_10S = predict_direction_10S_multidays_df[predict_direction_10S_multidays_df['bin_stanrdard_delta_shift1'] == '(+)2to3']
    price_change_plus_3to4_10S = predict_direction_10S_multidays_df[predict_direction_10S_multidays_df['bin_stanrdard_delta_shift1'] == '(+)3to4']
    price_change_plus_4to5_10S = predict_direction_10S_multidays_df[predict_direction_10S_multidays_df['bin_stanrdard_delta_shift1'] == '(+)4to5']

    # b).Calculate the probability of price change & Present the results
    price_change_tuple = [
                          (price_change_minus_5to4_10S, '(-)5to4'), 
                          (price_change_minus_4to3_10S, '(-)4to3'), 
                          (price_change_minus_3to2_10S, '(-)3to2'),
                          (price_change_minus_2to1_10S, '(-)2to1'),
                          (price_change_minus_1to0_10S, '(-)1to0'),
                          (price_change_plus_0to1_10S, '(+)0to1'), 
                          (price_change_plus_1to2_10S, '(+)1to2'), 
                          (price_change_plus_2to3_10S, '(+)2to3'), 
                          (price_change_plus_3to4_10S, '(+)3to4'),
                          (price_change_plus_4to5_10S, '(+)4to5')
                         ]   
    
    # Figure 1, Stacked Bar Chart Subplot 3 by 3
    prob_up_list = []
    prob_down_list = []
    prob_zero_list = []

    prob_table = []
    prob_table.append(f"Main Contract '{instrument_id}'£º" + 'Probability(PriceChange) -- Signal(delta)-Bin(NoAbs)-10S')
    for price_change, bin_label in price_change_tuple:
        
        try:
            prob_up = round(len(price_change['label_price_change_10S'][price_change['label_price_change_10S'] == 1.0])/ \
                                len(price_change), 3)
            prob_down = round(len(price_change['label_price_change_10S'][price_change['label_price_change_10S'] == -1.0])/ \
                                len(price_change), 3)
            prob_zero = round(1 - prob_up - prob_down, 3)
        except ZeroDivisionError:
            prob_up = np.nan
            prob_down = np.nan
            prob_zero = np.nan
            
        prob_up_list.append(format(prob_up, '.3f'))
        prob_down_list.append(format(prob_down, '.3f'))
        prob_zero_list.append(format(prob_zero, '.3f'))

        prob_table.append(f"Bin '{bin_label}', Prob Up Down Zero:  " + f"{format(prob_up, '.3f')}  " + f"{format(prob_down, '.3f')}  " + f"{format(prob_zero, '.3f')}")

    prob_table_df = pd.DataFrame(prob_table)
#     prob_table_df.to_csv('D:/Yangze_Investment/Task5_Acceleroar/data/' + instrument_id + '_prob_table_df.csv')

    # Print results                 
    print(tabulate(prob_table_df, headers='firstrow'))
    print('\n')               
                          
    fig = go.Figure(go.Bar(x=bin_labels, y=prob_down_list, name='Prob Down',
                          showlegend=True,
                          text=prob_down_list, textposition='auto', textfont=dict(size=13.5),
                          width=[0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65],
                          marker_color='rgb(0,204,150)')) 

    fig.add_trace(go.Bar(x=bin_labels, y=prob_zero_list, name='Prob No_Change',
                          showlegend=True,
                          text=prob_zero_list, textposition='auto', textfont=dict(size=13.5),
                          width=[0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65],
                          marker_color='rgb(99,110,250)'))
                          
    fig.add_trace(go.Bar(x=bin_labels, y=prob_up_list, name='Prob Up',
                          showlegend=True,
                          text=prob_up_list, textposition='auto', textfont=dict(size=13.5),
                          width=[0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65],
                          marker_color='rgb(239,85,59)'))
    
    # Customize x and y axes
    fig.update_xaxes(title_text='bin (sigma)', title_font=dict(size=16), tickfont=dict(size=15))
    fig.update_yaxes(title_text='probability', title_font=dict(size=16), tickfont=dict(size=15))

    # Customize aspect
    fig.update_traces(opacity=0.8)
    fig.update_layout(barmode='stack', 
                      height=650, width=1300,
                      title_text=f'{instrument_id}:  ' + 'Probability of Price Change -- Signal(delta)-Bin(NoAbs)-<i>(10 Seconds Window)</i>',
                      title_x=0.5,  # choose 0.5 to make the title center-aligned
                      legend=dict(font_size=14))
                  
    # Save figure as .png
    fig.write_image('D:\\Yangze_Investment\\Task5_Acceleroar\\plots\\BarChart\\Delta(1st)_NoAbs_Multi_Days\\' + instrument_id + 'signal(delta)_bin(no_abs)_10S_Multi_Days_V1.png')
    
# predict_direction_10S_multidays_df.to_csv('D:\\Yangze_Investment\\Task5_Acceleroar\\data\\Multi_Days\\predict_direction_10S_multidays_df.csv')    


# Multi-days signal generation

# Version 2: Concatenation First, Calculation Next

import numpy as np
import datetime
from datetime import date
from matplotlib.dates import drange
from tabulate import tabulate
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Select products
product_id_series = ['ni']
# product_id_series = yz.products[(yz.products['exchange'] == 'DCE') | (yz.products['exchange'] == 'SHFE')]['short_name']

# Set shift parameter for variable 'bin_stanrdard_delta'
shift_param = 1

for product_id in product_id_series:
    # Select main contracts corresponding to the product id 
    instrument_id = all_main_contracts_df[product_id][-1]
    
    # Create a multi-day data container (only Series and DataFrame objs are valid)
    resample_trading_10S_multidays_df = pd.DataFrame()
    
    # Set start and end date
    start_date = '2019-10-01'  # set date(YYYY, M, D) as the start date for data retrival
    end_date = '2019-11-07'    
#     end = datetime.date.today() + datetime.timedelta(days=1)

    # Create a date list
    date_list = yz.get_trade_day(start_date=start_date, end_date=end_date)
    
    for date in date_list:
        ticks_df = load_tick_data(instrument_id, date)
        resample_trading_10S_df = vwap_calculator(yz, ticks_df, '10S')
#         resample_trading_1M_df = vwap_calculator(yz, ticks_df, '1Min')
#         resample_trading_6M_df = vwap_calculator(yz, ticks_df, '6Min')        
        
        # key step for later manipulation: reset index
        resample_trading_10S_df.reset_index(inplace=True)
        
        # concatenate data of multiple days (key lines)
        resample_trading_10S_multidays_df = pd.concat([resample_trading_10S_multidays_df, 
                                             resample_trading_10S_df])
    
    resample_trading_10S_multidays_df.reset_index(inplace=True)

    # ****** Creating Simple Trading Signal ******  

    # Step1: calculate rolling standard deviation (std.)
    
    # key lines for multi-day rolling operations
    # drop the first few obs everyday to generate continuous rolling results
    # without these 2 lines of code, multi-day rolling will be conducted separately for every single day
    resample_trading_10S_multidays_df.drop(['ddelta_vwap', 'volume', 'turnover', 'volume_shift', 'turnover_shift'], axis=1, inplace=True)
    resample_trading_10S_multidays_df.dropna(inplace=True)  
    
    # Lookback period initially set up at n=100
    rolling_std_d_10S = resample_trading_10S_multidays_df['delta_vwap'].rolling(100).std()
        
    # Step2: use rolling std. calculated from (t0 to ti) to standardize/normalize the value of delta_vwap at ti

    standard_delta_vwap_10S =  resample_trading_10S_multidays_df['delta_vwap'] / rolling_std_d_10S
        
    # Step3: use standardized new points of delta_vwap at ti to label Pti+1 (P for last_price)

    # three label categories for price change: 'increase', 'unchanged', 'decrease'
        
    # a).Construct price changes
    price_change_10S = resample_trading_10S_multidays_df['last_price'] - resample_trading_10S_multidays_df['last_price'].shift(1)

    # b).Construct labels of price changes: '1'(increase), '-1'(decrease), '0'(unchanged)
    label_price_change_10S = price_change_10S.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else (0 if x == 0 else np.nan)))
        
    # c).Bin values of 'standard_delta_vwap_10S' into discrete intervals('bins') with equal range
    bin_labels = [
                        '(-)5to4', '(-)4to3', '(-)3to2', '(-)2to1', '(-)1to0',
                        '(+)0to1', '(+)1to2', '(+)2to3', '(+)3to4', '(+)4to5'
                     ]

    bin_stanrdard_delta_10S = pd.cut(standard_delta_vwap_10S, 
                                         bins=np.linspace(-5, 5, 11), 
                                         labels=bin_labels, 
                                         right=False)
        
    # d).Construct predicting data frame
    predict_direction_10S_df = pd.DataFrame()
    predict_direction_10S_df['index'] = resample_trading_10S_multidays_df['index']
    predict_direction_10S_df['exchange_time'] = resample_trading_10S_multidays_df['exchange_time']
    predict_direction_10S_df['instrument_id'] = resample_trading_10S_multidays_df['instrument_id']
    predict_direction_10S_df['price_change_10S'] = price_change_10S
    predict_direction_10S_df['label_price_change_10S'] = label_price_change_10S
    # the key prediction parameter 'shift_param' determines how many periods ahead we will predict at present time 
    predict_direction_10S_df['bin_stanrdard_delta_shift1'] = bin_stanrdard_delta_10S.shift(shift_param)
    predict_direction_10S_df[predict_direction_10S_df['index'] == 0]['bin_stanrdard_delta_shift1'] = np.nan
    
    # Step4: calculate the probability of price increase/decrease/unchanged

    # a).Extract price change data based on bin values of standard delta_vwap
    price_change_minus_5to4_10S = predict_direction_10S_df[predict_direction_10S_df['bin_stanrdard_delta_shift1'] == '(-)5to4']
    price_change_minus_4to3_10S = predict_direction_10S_df[predict_direction_10S_df['bin_stanrdard_delta_shift1'] == '(-)4to3']
    price_change_minus_3to2_10S = predict_direction_10S_df[predict_direction_10S_df['bin_stanrdard_delta_shift1'] == '(-)3to2']
    price_change_minus_2to1_10S = predict_direction_10S_df[predict_direction_10S_df['bin_stanrdard_delta_shift1'] == '(-)2to1']
    price_change_minus_1to0_10S = predict_direction_10S_df[predict_direction_10S_df['bin_stanrdard_delta_shift1'] == '(-)1to0']
    price_change_plus_0to1_10S = predict_direction_10S_df[predict_direction_10S_df['bin_stanrdard_delta_shift1'] == '(+)0to1']
    price_change_plus_1to2_10S = predict_direction_10S_df[predict_direction_10S_df['bin_stanrdard_delta_shift1'] == '(+)1to2']
    price_change_plus_2to3_10S = predict_direction_10S_df[predict_direction_10S_df['bin_stanrdard_delta_shift1'] == '(+)2to3']
    price_change_plus_3to4_10S = predict_direction_10S_df[predict_direction_10S_df['bin_stanrdard_delta_shift1'] == '(+)3to4']
    price_change_plus_4to5_10S = predict_direction_10S_df[predict_direction_10S_df['bin_stanrdard_delta_shift1'] == '(+)4to5']

    # b).Calculate the probability of price change & Present the results
    price_change_tuple = [
                          (price_change_minus_5to4_10S, '(-)5to4'), 
                          (price_change_minus_4to3_10S, '(-)4to3'), 
                          (price_change_minus_3to2_10S, '(-)3to2'),
                          (price_change_minus_2to1_10S, '(-)2to1'),
                          (price_change_minus_1to0_10S, '(-)1to0'),
                          (price_change_plus_0to1_10S, '(+)0to1'), 
                          (price_change_plus_1to2_10S, '(+)1to2'), 
                          (price_change_plus_2to3_10S, '(+)2to3'), 
                          (price_change_plus_3to4_10S, '(+)3to4'),
                          (price_change_plus_4to5_10S, '(+)4to5')
                         ]   
    
    # Figure 1, Stacked Bar Chart Subplot 3 by 3
    prob_up_list = []
    prob_down_list = []
    prob_zero_list = []

    prob_table = []
    prob_table.append(f"Main Contract '{instrument_id}'£º" + 'Probability(PriceChange) -- Signal(delta)-Bin(NoAbs)-10S')
    for price_change, bin_label in price_change_tuple:
        
        try:
            prob_up = round(len(price_change['label_price_change_10S'][price_change['label_price_change_10S'] == 1.0])/ \
                                len(price_change), 3)
            prob_down = round(len(price_change['label_price_change_10S'][price_change['label_price_change_10S'] == -1.0])/ \
                                len(price_change), 3)
            prob_zero = round(1 - prob_up - prob_down, 3)
        except ZeroDivisionError:
            prob_up = np.nan
            prob_down = np.nan
            prob_zero = np.nan
            
        prob_up_list.append(format(prob_up, '.3f'))
        prob_down_list.append(format(prob_down, '.3f'))
        prob_zero_list.append(format(prob_zero, '.3f'))

        prob_table.append(f"Bin '{bin_label}', Prob Up Down Zero:  " + f"{format(prob_up, '.3f')}  " + f"{format(prob_down, '.3f')}  " + f"{format(prob_zero, '.3f')}")

    prob_table_df = pd.DataFrame(prob_table)
#     prob_table_df.to_csv('D:/Yangze_Investment/Task5_Acceleroar/data/' + instrument_id + '_prob_table_df.csv')

    # Print results                 
    print(tabulate(prob_table_df, headers='firstrow'))
    print('\n')               
                          
    fig = go.Figure(go.Bar(x=bin_labels, y=prob_down_list, name='Prob Down',
                          showlegend=True,
                          text=prob_down_list, textposition='auto', textfont=dict(size=13.5),
                          width=[0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65],
                          marker_color='rgb(0,204,150)')) 

    fig.add_trace(go.Bar(x=bin_labels, y=prob_zero_list, name='Prob No_Change',
                          showlegend=True,
                          text=prob_zero_list, textposition='auto', textfont=dict(size=13.5),
                          width=[0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65],
                          marker_color='rgb(99,110,250)'))
                          
    fig.add_trace(go.Bar(x=bin_labels, y=prob_up_list, name='Prob Up',
                          showlegend=True,
                          text=prob_up_list, textposition='auto', textfont=dict(size=13.5),
                          width=[0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65, 0.65],
                          marker_color='rgb(239,85,59)'))
    
    # Customize x and y axes
    fig.update_xaxes(title_text='bin (sigma)', title_font=dict(size=16), tickfont=dict(size=15))
    fig.update_yaxes(title_text='probability', title_font=dict(size=16), tickfont=dict(size=15))

    # Customize aspect
    fig.update_traces(opacity=0.8)
    fig.update_layout(barmode='stack', 
                      height=650, width=1300,
                      title_text=f'{instrument_id}:  ' + 'Probability of Price Change -- Signal(delta)-Bin(NoAbs)-<i>(10 Seconds Window)</i>',
                      title_x=0.5,  # choose 0.5 to make the title center-aligned
                      legend=dict(font_size=14))
                  
    # Save figure as .png
    fig.write_image('D:\\Yangze_Investment\\Task5_Acceleroar\\plots\\BarChart\\Delta(1st)_NoAbs_Multi_Days\\' + instrument_id + 'signal(delta)_bin(no_abs)_10S_Multi_Days_V2.png')
    
# predict_direction_10S_multidays_df.to_csv('D:\\Yangze_Investment\\Task5_Acceleroar\\data\\Multi_Days\\predict_direction_10S_multidays_df.csv')    


resample_trading_10S_multidays_drop_df = resample_trading_10S_multidays_df.drop(['volume', 'turnover', 'volume_shift', 'turnover_shift'], axis=1)


resample_trading_10S_multidays_drop_df.to_csv('D:\\Yangze_Investment\\Task5_Acceleroar\\data\\Multi_Days\\' + instrument_id + 'resample_trading_10S_multidays_drop_df_V2.2.csv')


 