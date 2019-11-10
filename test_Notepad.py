    predict_direction_10S_multidays_df
	
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
    prob_table.append(f"Main Contract '{instrument_id}'：" + 'Probability(PriceChange) -- Signal(delta)-Bin(NoAbs)-10S')
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
    fig.write_image('D:\\Yangze_Investment\\Task5_Acceleroar\\plots\\BarChart\\Delta(1st)_NoAbs\\' + instrument_id + 'signal(delta)_bin(no_abs)_10S.png')
      