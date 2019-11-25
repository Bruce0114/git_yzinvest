import json
import numpy as np
import pandas as pd


# Step One: Retrieve Data from Log and Data Formatting

def log_to_data_frame(filepath):
    # Read .log data first
    with open(filepath, 'r') as f:
        fund_log = []
        for line in f.readlines():
            # 1. Extract lines containing "FillField"
            if '"FillField"' in line:
                fund_log.append(line)

    # 2. Throw unuseful information & only keep json-format data
    fund_json = []
    for item in range(len(fund_log)):
        for index in range(len(fund_log[item])):
            if fund_log[item][index:index + 3] == '{"F':
                fund_json.append(fund_log[item][index:])

    # 3. Convert JSON to DataFrame format
    json_list = []
    for i in range(len(fund_json)):
        fund_dict = json.loads(fund_json[i])
        json_list.append(fund_dict['FillField'])

    fund_data_frame = pd.DataFrame(json_list)

    return fund_data_frame


if __name__ == '__main__':
    filepath =['D:\\Yangze_Investment\\broker_switch_log\\zefeng_1.log',
               'D:\\Yangze_Investment\\broker_switch_log\\zeyuan.log']

    zefeng_1_df = log_to_data_frame(filepath[0])
    zeyuan_df = log_to_data_frame(filepath[1])

# Append data from two funds/accounts together
fund_append_df = zefeng_1_df.append(zeyuan_df)
fund_append_reset_df = fund_append_df.reset_index(drop=True)


# Step Two: Volume Weighted Price Computation

# Compute volume weighted price by ('Price' * 'Volume')
volume_weighted_price_df = fund_append_reset_df
volume_weighted_price_df['VolWeightedPrice'] = fund_append_reset_df['Price'] * fund_append_reset_df['Volume']

# Group by 'StrategyName', 'InstrID', 'Direction'
volume_weighted_price_groupby_df = volume_weighted_price_df.groupby(['StrategyName', 'InstrID', 'Direction'])

# Compute volume weighted average price (vwp) for '0'(Buy) and '1' (Sell) seperately
vwp_series = volume_weighted_price_groupby_df['VolWeightedPrice'].agg(np.sum)

# Add minus('-') sign to '0' (Buy) direction
vwp_df = pd.DataFrame(vwp_series)
vwp_direction_df = vwp_df.reset_index()

# vwp_sign_df = vwp_direction_df.reset_index()
for i in range(len(vwp_direction_df)):
    if vwp_direction_df['Direction'][i] == 0:  # '0' for 'Buy'
        vwp_direction_df.loc[i, 'VolWeightedPrice'] = -vwp_direction_df['VolWeightedPrice'][i]

vwp_direction_df = vwp_direction_df.set_index(['StrategyName', 'InstrID'])

# vwp(Sell, 1) minus vwp (Buy, 0)
vwp_direction_groupby_df = vwp_direction_df.groupby(['StrategyName', 'InstrID'])
vwp_diff_df = vwp_direction_groupby_df['VolWeightedPrice'].agg(np.sum)


# Step Three: Get Final Value

# IntrumentID to ProductID
product_id = lambda instrument_id: instrument_id[0:-4] if instrument_id[-4].isdigit() else instrument_id[0:-3]
instrument_id = vwp_diff_df.reset_index('InstrID')['InstrID'].reset_index(drop=True)
instrument_id_df = pd.DataFrame(instrument_id)
product_id_df = instrument_id_df.applymap(product_id)


# ProductID to Multiplier
def get_multiply(product_id):
    multi  ={'a': 10, 'b': 10, 'c': 10, 'cs': 10, 'i': 100, 'j': 100, 'jd': 10, 'jm': 60, 'l': 5,
                      'm': 10, 'p': 10, 'pp': 5, 'v': 5, 'y': 10, 'ag': 15, 'al': 5, 'au': 1000, 'bu': 10,
                      'cu': 5, 'fu': 10, 'hc': 10, 'ni': 1, 'pb': 5, 'rb': 10, 'ru': 10, 'sn': 1, 'zn': 5, 'sc': 1000, 'AP': 10,
                      'CF': 5, 'FG': 20, 'MA': 10, 'OI': 10, 'PM': 50, 'RM': 10, 'RS': 10, 'SF': 5, 'SM': 5,
                      'SR': 10, 'TA': 5, 'WH': 20, 'ZC': 100, 'IC': 200, 'IF': 300, 'IH': 300, 'T': 10000, 'TF': 10000}
    return multi[product_id]


multiplier_df = product_id_df.applymap(get_multiply)

# Multiplier * VMP Number
vwp_diff_df = pd.DataFrame(vwp_diff_df).reset_index()
# vwp_diff_df
vwp_diff_df['FinalValue'] = vwp_diff_df['VolWeightedPrice'] * multiplier_df['InstrID']
print(vwp_diff_df)
