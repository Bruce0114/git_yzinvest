from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Initialize figure with subplots
fig = make_subplots(rows=4, cols=1)

# Add traces for last_price
fig.add_trace(go.Scatter(y=resample_trading_price_fillna_df['last_price_10S'], 
                         name='10 Seconds Window', line=dict(width=1.8)), row=1, col=1)
fig.add_trace(go.Scatter(y=resample_trading_price_fillna_df['last_price_1M'], 
                         name='1 Minute Window', line=dict(width=1.8)), row=1, col=1)
fig.add_trace(go.Scatter(y=resample_trading_price_fillna_df['last_price_6M'], 
                         name='6 Minutes Window', line=dict(width=1.8)), row=1, col=1)

# Add traces for vwap
fig.add_trace(go.Scatter(y=resample_trading_vwap_fillna_df['vwap_10S'], 
                         showlegend=False, line=dict(width=1.8)), row=2, col=1)
fig.add_trace(go.Scatter(y=resample_trading_vwap_fillna_df['vwap_1M'], 
                         showlegend=False, line=dict(width=1.8)), row=2, col=1)
fig.add_trace(go.Scatter(y=resample_trading_vwap_fillna_df['vwap_6M'], 
                         showlegend=False, line=dict(width=1.8)), row=2, col=1)

# Add traces for delta_vwap
fig.add_trace(go.Scatter(y=resample_trading_delta_vwap_fillna_df['delta_vwap_10S'], 
                         showlegend=False, line=dict(width=1.6)), row=3, col=1)
fig.add_trace(go.Scatter(y=resample_trading_delta_vwap_fillna_df['delta_vwap_1M'], 
                         showlegend=False, line=dict(width=1.6)), row=3, col=1)
fig.add_trace(go.Scatter(y=resample_trading_delta_vwap_fillna_df['delta_vwap_6M'], 
                         showlegend=False, line=dict(width=1.6)), row=3, col=1)

# Add traces for ddelta_vwap
fig.add_trace(go.Scatter(y=resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_10S'], 
                         showlegend=False, line=dict(width=1.5)), row=4, col=1)
fig.add_trace(go.Scatter(y=resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_1M'], 
                         showlegend=False, line=dict(width=1.5)), row=4, col=1)
fig.add_trace(go.Scatter(y=resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_6M'], 
                         showlegend=False, line=dict(width=1.5)), row=4, col=1)

# Update xaxis properties
for row in range(1, 5):
    fig.update_xaxes(title_text='time lapse', row=row, col=1)

# Update yaxis properties
fig.update_yaxes(title_text='last_price', row=1, col=1)
fig.update_yaxes(title_text='vwap', row=2, col=1)
fig.update_yaxes(title_text='delta_vwap', row=3, col=1)
fig.update_yaxes(title_text='ddelta_vwap', row=4, col=1)

# Update height, weight and title
# Pinpoint and mark morning & lunch breaks
morning_position = break_position(resample_trading_price_fillna_df, 'morning')
lunch_position = break_position(resample_trading_price_fillna_df, 'lunch')

# Get min and max values for last_price
price_min = resample_trading_price_fillna_df['last_price_10S'] \
            .append(resample_trading_price_fillna_df['last_price_1M']) \
            .append(resample_trading_price_fillna_df['last_price_6M']).min()
price_max = resample_trading_price_fillna_df['last_price_10S'] \
            .append(resample_trading_price_fillna_df['last_price_1M']) \
            .append(resample_trading_price_fillna_df['last_price_6M']).max()

# Get min and max values for vwap
vwap_min = resample_trading_vwap_fillna_df['vwap_10S'] \
            .append(resample_trading_vwap_fillna_df['vwap_1M']) \
            .append(resample_trading_vwap_fillna_df['vwap_6M']).min()
vwap_max = resample_trading_vwap_fillna_df['vwap_10S'] \
            .append(resample_trading_vwap_fillna_df['vwap_1M']) \
            .append(resample_trading_vwap_fillna_df['vwap_6M']).max()

# Get min and max values for delta_vwap
delta_vwap_min = resample_trading_delta_vwap_fillna_df['delta_vwap_10S'] \
            .append(resample_trading_delta_vwap_fillna_df['delta_vwap_1M']) \
            .append(resample_trading_delta_vwap_fillna_df['delta_vwap_6M']).min()
delta_vwap_max = resample_trading_delta_vwap_fillna_df['delta_vwap_10S'] \
            .append(resample_trading_delta_vwap_fillna_df['delta_vwap_1M']) \
            .append(resample_trading_delta_vwap_fillna_df['delta_vwap_6M']).max()

# Get min and max values for ddelta_vwap
ddelta_vwap_min = resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_10S'] \
            .append(resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_1M']) \
            .append(resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_6M']).min()
ddelta_vwap_max = resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_10S'] \
            .append(resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_1M']) \
            .append(resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_6M']).max()

fig.update_layout(height=1200, width=1900, legend=dict(font_size=14), 
                  title_text='Main Contract Subplots: ' + instrument_id,
                  shapes=[
                      # Draw Lines Vertical
                      
                      # for last_price
                      go.layout.Shape(type='line', xref='x1', yref='y1', 
                                         x0=morning_position, y0=price_min,
                                         x1=morning_position, y1=price_max,
                                         line=dict(color='black', width=1.3)),
                      go.layout.Shape(type='line', xref='x1', yref='y1', 
                                         x0=lunch_position, y0=price_min,
                                         x1=lunch_position, y1=price_max,
                                         line=dict(color='black', width=1.3)),
                      
                      # for vwap
                      go.layout.Shape(type='line', xref='x2', yref='y2', 
                                     x0=morning_position, y0=vwap_min,
                                     x1=morning_position, y1=vwap_max,
                                     line=dict(color='black', width=1.3)),
                      go.layout.Shape(type='line', xref='x2', yref='y2', 
                                     x0=lunch_position, y0=vwap_min,
                                     x1=lunch_position, y1=vwap_max,
                                     line=dict(color='black', width=1.3)),
                      
                      # for delta_vwap
                      go.layout.Shape(type='line', xref='x3', yref='y3', 
                                     x0=morning_position, y0=delta_vwap_min,
                                     x1=morning_position, y1=delta_vwap_max,
                                     line=dict(color='black', width=1.3)),
                      go.layout.Shape(type='line', xref='x3', yref='y3', 
                                     x0=lunch_position, y0=delta_vwap_min,
                                     x1=lunch_position, y1=delta_vwap_max,
                                     line=dict(color='black', width=1.3)),
                      
                      # for ddelta_vwap
                      go.layout.Shape(type='line', xref='x4', yref='y4', 
                                     x0=morning_position, y0=ddelta_vwap_min,
                                     x1=morning_position, y1=ddelta_vwap_max,
                                     line=dict(color='black', width=1.3)),
                      go.layout.Shape(type='line', xref='x4', yref='y4', 
                                     x0=lunch_position, y0=ddelta_vwap_min,
                                     x1=lunch_position, y1=ddelta_vwap_max,
                                     line=dict(color='black', width=1.3))
                          ]
                     )

fig['layout'].update(annotations=[
                                 # annotation for last_price
                                 dict(x=morning_position, y=resample_trading_price_fillna_df['last_price_10S'][morning_position],
                                       xref='x1', yref='y1', ay=-80,
                                       text='Morning Break'),
                                 dict(x=lunch_position, y=resample_trading_price_fillna_df['last_price_10S'][lunch_position],
                                      xref='x1', yref='y1', ay=-90,
                                      text='Lunch Break'),
                     
                                 # annotation for vwap
                                 dict(x=morning_position, y=resample_trading_vwap_fillna_df['vwap_10S'][morning_position],
                                      xref='x2', yref='y2', ay=-80,
                                      text='Morning Break'),
                                 dict(x=lunch_position, y=resample_trading_vwap_fillna_df['vwap_10S'][lunch_position],
                                      xref='x2', yref='y2', ay=-90,
                                      text='Lunch Break'),
    
                                 # annotation for delta_vwap
                                 dict(x=morning_position, y=resample_trading_delta_vwap_fillna_df['delta_vwap_10S'][morning_position],
                                      xref='x3', yref='y3', ay=-80,
                                      text='Morning Break'),
                                 dict(x=lunch_position, y=resample_trading_delta_vwap_fillna_df['delta_vwap_10S'][lunch_position],
                                      xref='x3', yref='y3', ay=-80,
                                      text='Lunch Break'),
    
                                 # annotation for ddelta_vwap
                                 dict(x=morning_position, y=resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_10S'][morning_position],
                                      xref='x4', yref='y4', ay=-70,
                                      text='Morning Break'),
                                 dict(x=lunch_position, y=resample_trading_ddelta_vwap_fillna_df['ddelta_vwap_10S'][lunch_position],
                                      xref='x4', yref='y4', ay=-70,
                                      text='Lunch Break')
                        ]
                    )

fig.show()