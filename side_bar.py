#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
   side_bar.py

   Descp:

   Created on: 25-oct-2017

   Copyright 2017 Abel 'Akronix' Serrano Juste <akronix5@gmail.com>
"""

import json
import os
import itertools
from warnings import warn

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import grasia_dash_components as gdc
import dash_html_components as html
from lib.metrics.metric import MetricCategory

# GLOBAL VARIABLES

global app;

global debug;
debug = 'DEBUG' in os.environ

global metric_categories_order;
metric_categories_order = [MetricCategory.PAGES, MetricCategory.EDITIONS, MetricCategory.USERS, MetricCategory.RATIOS, MetricCategory.DISTRIBUTION]
category_names = ['PAGES', 'EDITIONS', 'USERS', 'RATIOS', 'DISTRIBUTION']

wikis_categories_order = ['LARGE', 'BIG', 'MEDIUM', 'SMALL']


# CODE

def fold_button():
    return html.Div(
        html.Div(
            id='fold-img-container',
            style={
                'cursor': 'pointer',
                'marginRight': '23px',
                'marginTop': '30px',
                'marginBottom': '30px'
            },
            #~ children=[html.Img(id='fold-img', src='assets/fold_arrow.svg')],
        ),
        id='fold-container',
        style={
            'display': 'flex',
            'flexDirection': 'row-reverse'
        }
    );


def generate_wikis_accordion_id(category_name):
    return '{}-wikis'.format(category_name);


def wikis_tab(wikis):

    def group_wikis_in_accordion(wikis, wikis_category):

        wikis_options = [{'label': wiki['name'], 'value': wiki['url']} for wiki in wikis]

        return gdc.Accordion(
                    id=generate_wikis_accordion_id(wikis_category) + '-accordion',
                    className='aside-category',
                    label=wikis_category,
                    itemClassName='metric-category-label',
                    childrenClassName='metric-category-list',
                    accordionFixedWidth='300',
                    defaultCollapsed=False if wikis else True,
                    children=[
                        dcc.Checklist(
                            id=generate_wikis_accordion_id(wikis_category),
                            className='aside-checklist-category',
                            options=wikis_options,
                            values=[],
                            labelClassName='aside-checklist-option',
                            labelStyle={'display': 'block'}
                        )
                    ],
                    style={'display': 'flex'}
                )

    # group metrics in a dict w/ key: category, value: [wikis]
    wikis_by_category = {wiki_category: [] for wiki_category in wikis_categories_order}
    for wiki in wikis:

        if wiki['pages'] > 100000:
            wikis_by_category['LARGE'].append(wiki)
        elif wiki['pages'] > 10000:
            wikis_by_category['BIG'].append(wiki)
        elif wiki['pages'] > 1000:
            wikis_by_category['MEDIUM'].append(wiki)
        else:
            wikis_by_category['SMALL'].append(wiki)

    # Generate accordions containing a checklist following the order
    #   defined by metric_categories_order list.
    wikis_checklist = []
    for category in wikis_categories_order:
        wikis_checklist.append(
                group_wikis_in_accordion(
                    wikis_by_category[category],
                    category
                )
            )

    intro_wikis_paragraph = html.Div(
                html.P(
                    html.Strong(('You can compare between {} wikis').format(len(wikis))),
                    className="sidebar-info-paragraph"
                ),
                className="container")

    return html.Div([
        html.Div(
            children = [intro_wikis_paragraph] + wikis_checklist,
            style={'color': 'white'},
            id='wikis-tab-container',
            ),
        ],
        id='wikis-tab'
    );


def select_time_axis_control():
    return (html.Div([
        html.Hr(),
        html.Div([
            html.Strong('Time axis:'),
            dcc.RadioItems(
                options=[
                    {'label': 'Months from birth', 'value': 'relative'},
                    {'label': 'Calendar dates', 'value': 'absolute'}
                ],
                value='relative',
                id='time-axis-selection'
            ),
            ],
            className="container"
        ),
        ])
    )


def generate_metrics_accordion_id(category_name):
    return '{}-metrics'.format(category_name);


def metrics_tab(metrics):

    def group_metrics_in_accordion(metrics, metric_category):

        metrics_options = [{'label': metric.text, 'value': metric.code} for metric in metrics]

        return gdc.Accordion(
                    id=generate_metrics_accordion_id(metric_category.name) + '-accordion',
                    className='aside-category',
                    label=metric_category.value,
                    itemClassName='metric-category-label',
                    childrenClassName='metric-category-list',
                    accordionFixedWidth='300',
                    defaultCollapsed=True,
                    children=[
                        dcc.Checklist(
                            id=generate_metrics_accordion_id(metric_category.name),
                            className='aside-checklist-category',
                            options=metrics_options,
                            values=[],
                            labelClassName='aside-checklist-option',
                            labelStyle={'display': 'block'}
                        )
                    ],
                    style={'display': 'flex'}
                )


    # group metrics in a dict w/ key: category, value: [metrics]
    metrics_by_category = {}
    for metric in metrics:
        if metric.category not in metrics_by_category:
            metrics_by_category[metric.category] = [metric]
        else:
            metrics_by_category[metric.category].append(metric)

    # Generate accordions containing a checklist following the order
    #   defined by metric_categories_order list.
    metrics_checklist = []
    for category in metric_categories_order:
        metrics_checklist.append(
                group_metrics_in_accordion(
                    metrics_by_category[category],
                    category
                )
            )

    intro_metrics_paragraph = html.Div(
                html.P(
                    html.Strong('Please, select the charts you wish to see and when you finish click on compare'),
                    className="sidebar-info-paragraph"
                ),
                className="container")

    return html.Div([
        html.Div(
            children = [intro_metrics_paragraph] + metrics_checklist,
            style={'color': 'white'},
            id='metrics-tab-container',
            ),
        select_time_axis_control(),
        #~ compare_button('metrics')
        ],
        id='metrics-tab'
    );


def compare_button():
    return (
        html.Div(
            html.Button('COMPARE',
                        id='compare-button',
                        className='action-button',
                        type='button',
                        n_clicks=0
            ),
            id='compare-button-container'
        )
    )


def selection_result_container():
    if debug:
        return html.Div(id='sidebar-selection', style={'display': 'block'})
    else:
        return html.Div(id='sidebar-selection', style={'display': 'none'})


def generate_side_bar(wikis, metrics):
    return html.Div(id='side-bar',
        children=[
            fold_button(),
            #~ html.Div(style={'backgroundColor': '#072146', 'height': '15px'}),
            gdc.Tabs(
                tabs=[
                    {'value': 'wikis', 'label': 'WIKIS'},
                    {'value': 'metrics', 'label': 'METRICS'}
                ],
                value='wikis',
                id='side-bar-tabs',
                vertical=False,
                selectedTabStyle={
                    'backgroundColor': '#004481',
                },
                style={
                    'width': '100%',
                    'textAlign': 'center',
                    'border': 'none',
                },
                tabsStyle={
                    'width': '50%',
                    'height': '70px',
                    'borderRadius': '3px',
                    'backgroundColor': '#072146',
                    'color': 'white',
                    'borderLeftStyle': 'none',
                    'borderRightStyle': 'none',
                    'fontSize': '18px',
                    'lineHeight': '21px',
                    'justifyContent': 'center',
                    'flexDirection': 'column'
                }),
            wikis_tab(wikis),
            metrics_tab(metrics),
            compare_button(),
            selection_result_container()
        ]
    );


def bind_callbacks(app):

    @app.callback(Output('wikis-tab', 'style'),
                   [Input('side-bar-tabs', 'value')])
    def update_wikis_tab_visible(tab_selection):
        if tab_selection == 'wikis':
            return {'display':'block'}
        else:
            return {'display':'none'}

    @app.callback(Output('metrics-tab', 'style'),
               [Input('side-bar-tabs', 'value')])
    def update_metrics_tab_visible(tab_selection):
        if tab_selection == 'metrics':
            return {'display':'block'}
        else:
            return {'display':'none'}

    # Note that we need one State parameter for each category metric that is created dynamically
    @app.callback(Output('sidebar-selection', 'children'),
               [Input('compare-button', 'n_clicks')],
                [State('time-axis-selection', 'value')] +
                [State(generate_wikis_accordion_id(name), 'values') for name in wikis_categories_order] +
                [State(generate_metrics_accordion_id(name), 'values') for name in category_names]
               )
    def compare_selection(btn_clicks,
                        time_axis_selection,
                        wikis_selection_large, wikis_selection_big, wikis_selection_medium, wikis_selection_small,
                        *metrics_selection_l):
        print('Number of clicks: ' + str(btn_clicks))
        if (btn_clicks > 0):
            metrics_selection = list(itertools.chain.from_iterable(metrics_selection_l)) # reduce a list of lists into one list.
            wikis_selection = wikis_selection_large + wikis_selection_big + wikis_selection_medium + wikis_selection_small
            selection = { 'wikis': wikis_selection, 'metrics': metrics_selection, 'time': time_axis_selection}
            return json.dumps(selection)


    # simple callbacks to enable / disable 'compare' button
    @app.callback(Output('compare-button', 'disabled'),
                [Input(generate_wikis_accordion_id(name), 'values') for name in wikis_categories_order] +
                [Input(generate_metrics_accordion_id(name), 'values') for name in category_names]
                )
    def enable_compare_button(wikis_selection_large, wikis_selection_big, wikis_selection_medium, wikis_selection_small,
                            *metrics_selection_l):
        metrics_selection = list(itertools.chain.from_iterable(metrics_selection_l)) # reduce a list of lists into one list.
        wikis_selection = wikis_selection_large + wikis_selection_big + wikis_selection_medium + wikis_selection_small
        print (wikis_selection, metrics_selection)
        if wikis_selection and metrics_selection:
            return None
        else:
            warn('You have to select at least one wiki and at least one metric')
            return 'disabled'
    return

if __name__ == '__main__':

    print('Using version ' + dcc.__version__ + ' of Dash Core Components.')
    print('Using version ' + gdc.__version__ + ' of Grasia Dash Components.')

    global app;

    app = dash.Dash()

    app.scripts.config.serve_locally = True

    def start_image_server():
        import flask
        import glob

        static_image_route = '/assets/'
        image_directory = os.path.dirname(os.path.realpath(__file__)) + static_image_route
        list_of_images = [os.path.basename(x) for x in glob.glob('{}*.svg'.format(image_directory))]

        # Add a static image route that serves images from desktop
        # Be *very* careful here - you don't want to serve arbitrary files
        # from your computer or server
        @app.server.route('{}<image_path>.svg'.format(static_image_route))
        def serve_image(image_path):
            image_name = '{}.svg'.format(image_path)
            if image_name not in list_of_images:
                raise Exception('"{}" is excluded from the allowed static files'.format(image_path))
            return flask.send_from_directory(image_directory, image_name)

    start_image_server()

#~ app.scripts.append_script({ "external_url": "app.js"})

    from lib.interface import get_available_metrics
    example_wikis = ['eslagunanegra_pages_full', 'cocktails', 'zelda']
    app.layout = html.Div(id='app-layout',
        style={'display': 'flex'},
        children=[
            generate_side_bar(example_wikis, get_available_metrics()),
        ]
    );
    bind_callbacks(app)

    app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
    app.css.append_css({"external_url": "https://codepen.io/akronix/pen/rpQgqQ.css"})

    app.run_server(port=8052, debug=True)

