from dash import Dash, html, dcc, callback, Output, Input, callback_context
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from scipy.interpolate import griddata
import numpy as np
from scipy.interpolate import Rbf
from dash.dependencies import State
import logging

MANNEQUIN_MASK_PATH = "assets/outline.png"

class ScatterPlot(go.Scatter):
    def __init__(self, placements_df: pd.DataFrame):
        super().__init__(
            customdata=placements_df['sensor'],
            x=placements_df['x'], y=placements_df['y'],
            # fillcolor=[np.NaN for i in range(len(placements_df))],
            text=placements_df['serial_number'],
            hovertemplate="<br><b>%{customdata} PM2.5</b></br><extra><br>%{text}</br><br>x=%{x}, y=%{y}</br></extra>",
            marker=dict(color='black', size=10),
            mode="markers"
        )

class AppPlot(go.Figure):
    def __init__(self, placements_df: pd.DataFrame):
        super().__init__(layout=go.Layout(
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
        ))
        scatter_plot = ScatterPlot(placements_df)
        self.add_trace(scatter_plot)
class AppLayout(html.Div):
    def __init__(self, placements_df: pd.DataFrame):
        self.app_figure = AppPlot(placements_df)
        super().__init__([
            dcc.Interval(
                id='interval-component',
                interval = 5000, #ms
                n_intervals=0
            ),

            # html.H1(
            #     children='Sensor Mannequin Plot',
            #     style={'textAlign':'center'}
            # ),
            # html.Button('Toggle Heatmap/Contour', id='toggle-button', n_clicks=0),
            dcc.Graph(
                id='interactive-graph',
                figure=self.app_figure
            )
        ])


class MannequinApp(Dash):
    def __init__(self, placements_df: pd.DataFrame):
        super().__init__(
            name=__name__,
        )
        self.layout = AppLayout(placements_df)

"""
x = placements_df['x'].values.copy()
y = placements_df['y'].values.copy()
serials = placements_df['serial_number'].values.copy()
sensors = placements_df['sensor'].values.copy()
z = np.linspace(0, 0, len(placements_df))

# RBF Interpolation
rbfi = Rbf(x, y, z, function='gaussian')
xi, yi = np.linspace(0, 1, 100), np.linspace(0, 1, 100)
xi, yi = np.meshgrid(xi, yi)
zi = rbfi(xi, yi)

# Layout for the plot
layout = go.Layout(
    images=[dict(
        source='assets/outline.png', # URL or path to your image
        xref='x', yref='y',
        x=0, y=1, # Coordinates where the image will be placed
        sizex=1, sizey=1, # Size of the image
        sizing='stretch',
        opacity=1, # Image opacity
        layer='above' # Display image above the plot
    )]
)

# Create a figure
fig = go.Figure(layout=layout)
# fig = go.Figure()

# Add heatmap
fig.add_trace(
    go.Heatmap(z=zi, x=xi[0], y=yi[:, 0], hoverinfo=None)
)

# Add original points as scatter plot
scatter = go.Scatter(
    x=x, y=y, mode='markers', 
    marker=dict(color='black', size=10),
    text=[f"{sn}: {val}" for sn, val in zip(serials, z)], # This will be displayed on hover
    hoverinfo='text'
)

# Add contour
fig.add_trace(
    go.Contour(x=xi[0], y=yi[:, 0], z=zi, visible=False)
)

fig.add_trace(scatter)

fig.update_layout(
    xaxis=dict(
        range=(0,1),
        constrain='domain'  # This option ensures that the aspect ratio is maintained
    ),
    yaxis=dict(
        range=(0,1),
        scaleanchor="x",  # This option forces the y-axis to scale with the x-axis
        scaleratio=1      # This option ensures a 1:1 aspect ratio
    ),
    width=900,
    height=800
)

app.layout = html.Div([
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds
        n_intervals=0
    ),
    html.H1(children='Mannequin', style={'textAlign':'center'}),
    html.Button('Toggle Heatmap/Contour', id='toggle-button', n_clicks=0),
    # dcc.Dropdown(df.country.unique(), 'Canada', id='dropdown-selection'),
    # dcc.Graph(id='graph-content')
    dcc.Graph(id='interactive-graph', figure=fig)
])

@app.callback(
    Output('interactive-graph', 'figure'),
    [Input('toggle-button', 'n_clicks'), Input('interval-component', 'n_intervals')],
    prevent_initial_call=True,
)
def update_graph(n_clicks, n_intervals):
    ctx = callback_context

    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'toggle-button':
        # Code for toggling heatmap/contour
        mode = n_clicks % 3
        # [Add the rest of your toggle logic here...]
        # Update visibility based on the current mode
        if mode == 0:
            # Show Heatmap, Hide Contour, Scatter black
            fig.data[0].visible = True   # Heatmap
            fig.data[1].visible = False  # Contour
            fig.data[2].visible = True   # Scatter
            fig.data[2].marker.color = 'black'
            fig.data[2].marker.showscale = False  # Hide color bar
        elif mode == 1:
            # Hide Heatmap, Show Contour, Scatter black
            fig.data[0].visible = False
            fig.data[1].visible = True
            fig.data[2].visible = True
            fig.data[2].marker.color = 'black'
            fig.data[2].marker.showscale = False  # Hide color bar
        elif mode == 2:
            # Hide both Heatmap and Contour, Scatter colored
            fig.data[0].visible = False
            fig.data[1].visible = False
            fig.data[2].visible = True
            fig.data[2].marker.color = z  # Use the z values for coloring
            fig.data[2].marker.showscale = True  # Hide color bar
            fig.update_layout(plot_bgcolor='lightgrey', paper_bgcolor='lightgrey')
        
    elif button_id == 'interval-component':
        # Code for updating the plot every 5 seconds
        # Fetch new data from your database
        # Update your z values
        # Recalculate your heatmap/contour
        # [Add the rest of your interval update logic here...]

        new_z_data = get_data_many(sensors, serials, 3)
        for idx, v in enumerate(new_z_data):
            if (v is None) or (np.isnan(v)):
                new_z_data[idx] = 0
        z = np.array(new_z_data)

        # logging.info(f"Z = {z}")

        # Update your existing data (x, y, z) with new_data
        # This involves updating z-values and possibly adding new x, y, z points

        # Update RBF Interpolation with new data
        rbfi = Rbf(x, y, z, function='gaussian')
        zi = rbfi(xi, yi)

        # logging.info(f"zi: {zi}")

        # Update existing figure object
        fig['data'][0]['z'] = zi  # Updating heatmap
        fig['data'][1]['z'] = zi  # Updating contour
        # existing_figure['data'][2]['z'] = z
        # existing_figure['data'][2]['x'] = x   # Updating scatter plot x
        # existing_figure['data'][2]['y'] = y   # Updating scatter plot y
        fig['data'][2]['text'] = [f"{sn}: {val}" for sn, val in zip(serials, z)]
    
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=8888, host="0.0.0.0")
"""