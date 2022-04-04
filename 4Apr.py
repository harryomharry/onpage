import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

import dash
import dash_auth
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

import dash_cytoscape as cyto
from demos import dash_reusable_components as drc

# Load extra layouts
cyto.load_extra_layouts()


asset_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'assets'
)

VALID_USERNAME_PASSWORD_PAIRS = {
    'test': 'visual'
}

app = dash.Dash(
    external_stylesheets=[dbc.themes.SKETCHY],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
app.title = 'Strategic KPI on Page'
server = app.server


# ###################### DATA PREPROCESSING ######################
# Load data

df = pd.read_csv('data.csv', encoding="ISO-8859-1")
df1 = df[['KPI_NAME', 'KPI_DESC', 'NUMERIC_VALUE',
       'UOM', 'PERIOD', 'TARGET_VALUE',
       'TRENDING_DIRECTION', 'PRIORITY_OUTCOME',
       'PRIORITY_NAME', 'PRIORITY_AREA_NAME']]

pig = px.sunburst(df1, path=['PRIORITY_NAME', 'PRIORITY_AREA_NAME', 'PRIORITY_OUTCOME'],color = 'PRIORITY_AREA_NAME', color_continuous_scale='RdBu')#, values='total_bill')

df1[['PRIORITY_NAME','PRIORITY_AREA_NAME','PRIORITY_OUTCOME']].drop_duplicates().values
df2=df1[(~df1.PERIOD.isna()) | (~df1.NUMERIC_VALUE.isna())].copy()

df2.PERIOD = df2.PERIOD.astype(int).astype(str)
df2=df2.sort_values(['KPI_NAME', 'PERIOD'], ascending=[True, True]).copy()

start = [['Halifax','Council Priority'],
       ['Halifax','Admin Priority']]

first = df1[['PRIORITY_NAME','PRIORITY_AREA_NAME']].drop_duplicates().values

second = df1[['PRIORITY_AREA_NAME','PRIORITY_OUTCOME']].drop_duplicates().values

total = [start]+[first]+[second]

# We select the first 750 edges and associated nodes for an easier visualization

nodes = set()

following_node_di = {}  # user id -> list of users they are following
following_edges_di = {}  # user id -> list of cy edges starting from user id


cy_edges = []
cy_nodes = []

for t in total:
    
    for f in t:
        source, target = f[0],f[1]

        cy_edge = {'data': {'id': source+target, 'source': source, 'target': target}}
        cy_target = {"data": {"id": target, "label": target}}
        cy_source = {"data": {"id": source, "label": source}}

        if source not in nodes:
            nodes.add(source)
            cy_nodes.append(cy_source)
        if target not in nodes:
            nodes.add(target)
            cy_nodes.append(cy_target)

        # Process dictionary of following
        if not following_node_di.get(source):
            following_node_di[source] = []
        if not following_edges_di.get(source):
            following_edges_di[source] = []

        following_node_di[source].append(cy_target)
        following_edges_di[source].append(cy_edge)
        
        
genesis_node = cy_nodes[0]
genesis_node['classes'] = "genesis"
default_elements = [genesis_node]
default_stylesheet = [
    {
        "selector": 'node',
        'style': {
            "opacity": 0.65,
            'z-index': 9999
        }
    },
    {
        "selector": 'edge',
        'style': {
            "curve-style": "bezier",
            "opacity": 0.45,
            'z-index': 5000
        }
    },
    {
        'selector': '.followerNode',
        'style': {
            'background-color': '#0074D9'
        }
    },
    {
        'selector': '.followerEdge',
        "style": {
            "mid-target-arrow-color": "blue",
            "mid-target-arrow-shape": "vee",
            "line-color": "#0074D9"
        }
    },
    {
        'selector': '.followingNode',
        'style': {
            'background-color': '#FF4136',
            "label": "data(label)",
        }
    },
    {
        'selector': '.followingEdge',
        "style": {
            "mid-target-arrow-color": "green",
            "mid-target-arrow-shape": "vee",
            "line-color": "#6699ba",
            "label": "data(label)",
        }
    },
    {
        "selector": '.genesis',
        "style": {
            'background-color': '#1a6697',
            "border-width": 2,
            "border-color": "purple",
            "border-opacity": 1,
            "opacity": 1,

            "label": "data(label)",
            "color": "#1a6697",
            "text-opacity": 1,
            "font-size": 12,
            'z-index': 9999
        }
    },
    {
        'selector': ':selected',
        "style": {
            "border-width": 2,
            "border-color": "black",
            "border-opacity": 1,
            "opacity": 1,
            "label": "data(label)",
            "color": "black",
            "font-size": 12,
            'z-index': 9999
        }
    }
]

# ################################# APP LAYOUT ################################
styles = {
    'json-output': {
        'overflow-y': 'scroll',
        # 'height': 'calc(50% - 25px)',
        'border': 'thin lightgrey solid'
    },
}

app.layout = html.Div(
    [
        dbc.Row([
            dbc.Col([html.Br(),
                dbc.Row(html.P(id = 'title')),
                dbc.Row(dcc.Graph(figure=pig, id='sunburst')),
                dbc.Row(dbc.Col([drc.NamedDropdown(
                    name='Select Nodes Display',
                    id='dropdown-layout',
                    options=drc.DropdownOptionsList(
                        'random',
                        'grid',
                        'circle',
                        'concentric',
                        'breadthfirst',
                        'cose',
                        'cose-bilkent',
                        'dagre',
                        'cola',
                        'klay',
                        'spread',
                        'euler'),
                    value='cola',
                    clearable=False)], width = 2, align="center"),
            justify="center",
                        ),
                 dbc.Row([
                    cyto.Cytoscape(
                        id='cytoscape',
                        elements=default_elements,
                        stylesheet = default_stylesheet,
                    )],
            justify="center",)], width = 6),
            dbc.Col([html.Br(),
                dbc.Row([html.H4(id='outcometitle')]),
                dbc.Accordion(
                        [html.Div(id='accord')], 
                    )
            ], width = 6),

        ]),
    ]
)

# ############################## CALLBACKS ###################################


@app.callback(Output('cytoscape', 'layout'),
              [Input('dropdown-layout', 'value')])
def update_cytoscape_layout(layout):
    return {'name': layout}


@app.callback([Output('cytoscape', 'elements'),
               Output('accord', 'children'),
              Output('title','children'),
              Output('outcometitle','children')],
              [Input('cytoscape', 'tapNodeData'),
              Input("sunburst", "clickData")],
              [State('cytoscape', 'elements')])
def generate_elements(nodeData, clickData,elements):
    priority = df2['PRIORITY_NAME'].unique()
    area = df2['PRIORITY_AREA_NAME'].unique()
    outcome = df2['PRIORITY_OUTCOME'].unique()
    
    cardList =df2.head()
    kitems=[]
    title = 'Click on Sunburst chart or Tap a node underneath'
    accordlabel = str('Choose an Outcome - (Sunburst OR Tap any leaf node)')
    
    if clickData:
        click_path = clickData["points"][0]["id"].split("/")
        click_select = clickData["points"][0]["label"]
        title = f"Sunburst Selection: {' '.join(click_path)}" 
        if click_select in outcome:
            cardList=df2[df2['PRIORITY_OUTCOME']==click_select].copy()
            accordlabel = "Outcome KPI's for: "+  click_select
    
    if (not nodeData) & (not clickData):
    #if not nodeData:
        return default_elements, kitems, title, accordlabel

    if nodeData:
        if nodeData['id'] in outcome:
            cardList=df2[df2['PRIORITY_OUTCOME']==nodeData['id']].copy()
            accordlabel = "Outcome KPI's for: "+  nodeData['id']
        
           
    # elif nodeData['id'] in area:
    #     cardList=df2[df2['PRIORITY_AREA_NAME']==nodeData['id']].copy()
    # elif nodeData['id'] in priority:
    #     cardList=df2[df2['PRIORITY_NAME']==nodeData['id']].copy()
            
    
    for kpi in cardList.KPI_NAME.unique():
        focus = cardList[cardList.KPI_NAME == kpi]
        mini,maxi=focus.NUMERIC_VALUE.min(),focus.NUMERIC_VALUE.max()
        fig = px.area(focus,x='PERIOD', y='NUMERIC_VALUE', title = focus.KPI_NAME.unique()[0], line_shape ='spline', markers=True).update_layout(plot_bgcolor='rgba(241, 246, 249, 1)').update_yaxes(title='').update_xaxes(title='').update_layout(yaxis_range=[0.9*mini,1.3*maxi])
        fig.add_trace(go.Line(
            name='Target', x=focus.PERIOD,
            y=focus.TARGET_VALUE)),
        #kitems.append(dbc.AccordionItem([dcc.Graph(id=kpi,figure=fig)],title = kpi),)
        kitems.append(dcc.Graph(id=kpi,figure=fig, style={'border':'10px ridge','border':'10px groove','border-radius': '15px','border-color':'rgba(241, 246, 249, 1)'}))
     
    
    if nodeData:
        # If the node has already been expanded, we don't expand it again
        if nodeData['id'] != 'Halifax': 
            if nodeData.get('expanded'):
                for element in elements:
                    if nodeData['id'] == element.get('data').get('id'):
                        element['data'].pop('expanded')
                        nodeData.pop('expanded')
                return default_elements, kitems, title, accordlabel

        # This retrieves the currently selected element, and tag it as expanded
        for element in elements:
            if nodeData['id'] == element.get('data').get('id'):
                element['data']['expanded'] = True
                break

        following_nodes = following_node_di.get(nodeData['id'])
        following_edges = following_edges_di.get(nodeData['id'])

        if following_nodes:
            for node in following_nodes:
                if node['data']['id'] != genesis_node['data']['id']:
                    node['classes'] = 'followingNode' 
                    elements.append(node)

        if following_edges:
            for follower_edge in following_edges:
                follower_edge['classes'] = 'followingEdge'
            elements.extend(following_edges)
        nodeData = ''
    return elements, kitems, title, accordlabel

if __name__ == '__main__':
    app.run_server(debug=True)