import logging
from typing import Union
from dash import Dash, html, dcc, callback, Output, Input, callback_context
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from scipy.interpolate import griddata
import numpy as np
from scipy.interpolate import Rbf
from dash.dependencies import State
import logging
from db import get_data_many

logging.basicConfig(level=logging.INFO)

PLACEMENTS_FILE_PATH = "/var/lib/mysql-files/placements.csv"
APP_HOST_ADDR = "0.0.0.0"
APP_PORT = 8888

PM_MAX = 10

placements_df = pd.read_csv(PLACEMENTS_FILE_PATH)
placements_df_front = placements_df.loc[placements_df['plot']==0]
placements_df_back = placements_df.loc[placements_df['plot']==1]
logging.info(f"Placements: {placements_df}")

MANNEQUIN_MASK_PATH = "assets/outline.png"

scatter_plot_front = go.Scatter(
    customdata=[f"{v} PM2.5" for v in placements_df_front['sensor']],
    x=placements_df_front['x'], y=placements_df_front['y'],
    text=placements_df_front['serial_number'],
    hovertemplate="%{customdata}<extra><br>%{text}</br><br>x=%{x}, y=%{y}</br></extra>",
    marker=dict(
        colorscale='Viridis',
        cmin=0,
        cmax=PM_MAX,
        cauto=False,
        size=14,
        color='black',
        showscale=True
    ),
    mode="markers"
)
scatter_plot_back = go.Scatter(
    customdata=[f"{v} PM2.5" for v in placements_df_back['sensor']],
    x=placements_df_back['x'], y=placements_df_back['y'],
    text=placements_df_back['serial_number'],
    hovertemplate="%{customdata}<extra><br>%{text}</br><br>x=%{x}, y=%{y}</br></extra>",
    marker=dict(
        colorscale='Viridis',
        cmin=0,
        cmax=PM_MAX,
        cauto=False,
        size=14,
        color='black',
        showscale=True
    ),
    mode="markers"
)

fig_front = go.Figure(
    layout=go.Layout
    (
        images=[dict(
            source=MANNEQUIN_MASK_PATH,
            xref='x', yref='y',
            x=0, y=1,
            sizex=1, sizey=1,
            sizing='stretch',
            opacity=1,
            layer='above'
        )],
        xaxis=dict(
            range=(0,1),
            constrain='domain'  # This option ensures that the aspect ratio is maintained
        ),
        yaxis=dict(
            range=(0,1),
            scaleanchor="x",  # This option forces the y-axis to scale with the x-axis
            scaleratio=1      # This option ensures a 1:1 aspect ratio
        ),
        width=800,
        height=650,
        title=dict(
            text="Front View",  # Title text
            x=0.5,  # Title x position (0.5 is centered)
            y=0.95,  # Title y position (adjust if needed)
            xanchor='center',  # Anchor the title at the center at x position
            yanchor='top',  # Anchor the title at the top at y position
            font=dict(
                family="Arial, sans-serif",
                size=20,
                color="black"
            )
        ),
    )
)
fig_front.add_trace(scatter_plot_front)

fig_back = go.Figure(
    layout=go.Layout
    (
        images=[dict(
            source=MANNEQUIN_MASK_PATH,
            xref='x', yref='y',
            x=0, y=1,
            sizex=1, sizey=1,
            sizing='stretch',
            opacity=1,
            layer='above'
        )],
        xaxis=dict(
            range=(0,1),
            constrain='domain'  # This option ensures that the aspect ratio is maintained
        ),
        yaxis=dict(
            range=(0,1),
            scaleanchor="x",  # This option forces the y-axis to scale with the x-axis
            scaleratio=1      # This option ensures a 1:1 aspect ratio
        ),
        width=800,
        height=650,
        title=dict(
            text="Back View",  # Title text
            x=0.5,  # Title x position (0.5 is centered)
            y=0.95,  # Title y position (adjust if needed)
            xanchor='center',  # Anchor the title at the center at x position
            yanchor='top',  # Anchor the title at the top at y position
            font=dict(
                family="Arial, sans-serif",
                size=20,
                color="black"
            )
        ),
    )
)
fig_back.add_trace(scatter_plot_back)

# app_layout = html.Div([
#     dcc.Interval(
#         id='interval-component',
#         interval = 5000, #ms
#         n_intervals=0
#     ),
#     dcc.Graph(
#         id='interactive-graph-front',
#         figure=fig_front
#     ),
#     dcc.Graph(
#         id='interactive-graph-back',
#         figure=fig_back
#     )
# ])
app_layout = html.Div([
    dcc.Interval(
        id='interval-component',
        interval=5000,  # milliseconds
        n_intervals=0
    ),
    html.Div([  # This div will act as a flex container
        dcc.Graph(
            id='interactive-graph-front',
            figure=fig_front,
            style={'flex': 1}  # This ensures the graph takes up equal space
        ),
        dcc.Graph(
            id='interactive-graph-back',
            figure=fig_back,
            style={'flex': 1}  # This ensures the graph takes up equal space
        )
    ], style={'display': 'flex', 'flex-direction': 'row'})  # This makes the container a row-type flexbox
])

app = Dash(name=__name__)
app.layout = app_layout

@app.callback(
    [Output('interactive-graph-front', 'figure'),
     Output('interactive-graph-back', 'figure')],
    Input('interval-component', 'n_intervals'),
    prevent_initial_call=True,
)
def update_graph(n_intervals):
    ctx = callback_context

    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'interval-component':
        if len(placements_df_front) != 0:
            new_z_data = get_data_many(placements_df_front['sensor'].values, placements_df_front['serial_number'].values, 3)
            if new_z_data is not None and len(new_z_data) > 0:
                for idx, v in enumerate(new_z_data):
                    if (v is None) or (np.isnan(v)):
                        new_z_data[idx] = np.NaN
                z = np.array(new_z_data).round(1)

                fig_front.data[0].marker.color = z  # Use the z values for coloring
                fig_front.data[0].marker.cmin = 0
                fig_front.data[0].marker.cmax = max([z.max(), PM_MAX])
                fig_front['data'][0]['customdata'] = [f"<br>{sensor} PM2.5</br><br><b>{val}</b></br>" for sensor, val in zip(placements_df_front['sensor'].values, z)]
            
        if len(placements_df_back) != 0:
            new_z_data = get_data_many(placements_df_back['sensor'].values, placements_df_back['serial_number'].values, 3)
            if new_z_data is not None and len(new_z_data) > 0:
                for idx, v in enumerate(new_z_data):
                    if (v is None) or (np.isnan(v)):
                        new_z_data[idx] = np.NaN
                z = np.array(new_z_data).round(1)

                fig_back.data[0].marker.color = z  # Use the z values for coloring
                fig_back.data[0].marker.cmin = 0
                fig_back.data[0].marker.cmax = max([z.max(), PM_MAX])
                fig_back['data'][0]['customdata'] = [f"<br>{sensor} PM2.5</br><br><b>{val}</b></br>" for sensor, val in zip(placements_df_back['sensor'].values, z)]
            
    return fig_front, fig_back

def main():
    app.run(debug=True, port=APP_PORT, host=APP_HOST_ADDR)

main()