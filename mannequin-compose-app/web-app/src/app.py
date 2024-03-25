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

MANNEQUIN_MASK_PATH = "assets/outline.png"

scatter_plot = go.Scatter(
    customdata=[f"{v} PM2.5" for v in placements_df['sensor']],
    x=placements_df['x'], y=placements_df['y'],
    text=placements_df['serial_number'],
    hovertemplate="%{customdata}<extra><br>%{text}</br><br>x=%{x}, y=%{y}</br></extra>",
    marker=dict(
        colorscale='Viridis',
        cmin=0,
        cmax=PM_MAX,
        cauto=False,
        size=10,
        color='black',
        showscale=True
    ),
    mode="markers"
)

fig = go.Figure(
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
        width=1000,
        height=870
    )
)
fig.add_trace(scatter_plot)

app_layout = html.Div([
    dcc.Interval(
        id='interval-component',
        interval = 5000, #ms
        n_intervals=0
    ),
    dcc.Graph(
        id='interactive-graph',
        figure=fig
    )
])

app = Dash(name=__name__)
app.layout = app_layout

@app.callback(
        Output('interactive-graph', 'figure'),
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
        new_z_data = get_data_many(placements_df['sensor'].values, placements_df['serial_number'].values, 3)
        for idx, v in enumerate(new_z_data):
            if (v is None) or (np.isnan(v)):
                new_z_data[idx] = np.NaN
        z = np.array(new_z_data).round(1)

        fig.data[0].marker.color = z  # Use the z values for coloring
        fig.data[0].marker.cmin = 0
        fig.data[0].marker.cmax = max([z.max(), PM_MAX])
        fig['data'][0]['customdata'] = [f"<br>{sensor} PM2.5</br><br><b>{val}</b></br>" for sensor, val in zip(placements_df['sensor'].values, z)]
    
    return fig

def main():
    app.run(debug=True, port=APP_PORT, host=APP_HOST_ADDR)

main()