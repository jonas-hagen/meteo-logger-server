#!/usr/bin/env python3
from datetime import datetime, timedelta
from io import StringIO
import os

import matplotlib
import yaml
from dicttoxml import dicttoxml
from flask import Flask, jsonify, request, Response, abort, render_template
from flask_caching import Cache

import meteo
from meteo import data as md

matplotlib.use('Agg')  # Force matplotlib to not use any Xwindows backend.
import matplotlib.pyplot as plt
import pandas as pd

home_folder = os.path.dirname(os.path.abspath(meteo.__file__))

app = Flask(__name__,
            template_folder=os.path.join(home_folder, 'templates'),
            static_folder=os.path.join(home_folder, 'static'))
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

app.logger.info(os.path.join(home_folder, 'templates'))

# Configure
with open('/etc/meteo.yml', 'r') as f:
    config = yaml.load(f)

units = {
    'air_temperature': '°C',
    'rel_humidity': '%',
    'air_pressure': 'hPa',
    'wind_speed_avg': 'm/s',
    'wind_speed_max': 'm/s',
    'wind_speed_min': 'm/s',
    'wind_dir_avg': 'deg',
    'wind_dir_min': 'deg',
    'wind_dir_max': 'deg',
    'rain_duration': 's',
    'rain_intensity': 'mm/h',
    'rain_accumulation': 'mm',
    'rain_peek_intensity': 'mm',
    'heating_temperature': '°C',

    'wind_speed': 'm/s',
    'wind_dir': 'deg'
}


def wordize(s):
    s = s.replace('_', ' ')
    s = s.title()
    return s


def api_response(data):
    accept = request.accept_mimetypes.best_match([
        'application/json',
        #'text/xml',
        #'application/xml',
    ])

    if accept == 'application/json':
        return jsonify(data)
    elif accept == 'text/xml' or accept == 'application/xml':
        return Response(dicttoxml(data), mimetype=accept)

    return jsonify(data)


@app.route('/plot/week/<column>')
@cache.memoize(60*60*3)
def plot_week(column):
    return plot_series('week', column)


@app.route('/plot/day/<column>')
@cache.memoize(60*10*3)
def plot_day(column):
    return plot_series('day', column)


@app.route('/plot/raw/<column>')
def plot_raw(column):
    return plot_series('raw', column)


def plot_series(period, column):
    now = datetime.utcnow()
    if period == 'week':
        timespan = timedelta(weeks=1)
        freq = '1H'
    elif period == 'day':
        timespan = timedelta(days=1)
        freq = '10min'
    elif period == 'raw':
        timespan = timedelta(days=1)
        freq = None
    else:
        abort(404)

    now = datetime.utcnow()
    first = now - timespan
    last = now

    df = md.read_data(config['target'], now - timespan)
    df = df[slice(first, last)]

    max_col = None
    min_col = None
    if column == 'wind_speed':
        max_col = 'wind_speed_max'
        min_col = 'wind_speed_min'
        column = 'wind_speed_avg'
    elif column == 'wind_dir':
        max_col = 'wind_dir_max'
        column = 'wind_dir_avg'

    if column not in df.columns:
        abort(404)

    interruption = df.index.to_series().diff() > pd.Timedelta(seconds=60*5)
    for c in df.columns:
        df[c][interruption] = pd.np.nan

    if freq is not None:
        df = md.resample(df, freq=freq)

    color = (31/255, 119/255, 180/255)
    fig, ax = plt.subplots()
    ax.plot(df.index, df[column], color=color)
    fig.autofmt_xdate()
    ax.set_xlim(now-timespan, now)

    if max_col and min_col:
        ax.fill_between(df.index, df[min_col], df[max_col], color=color, alpha=0.5)

    if max_col and not min_col:
        ax.plot(df.index, df[max_col], linestyle=':', color=color)

    ax.set_xlabel('Time (UTC)')
    ax.set_ylabel(wordize(column) + ' / ' + units[column])
    ax.grid()

    imgdata = StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)  # rewind the data

    return Response(imgdata, mimetype='image/svg+xml')


def meteo_latest(seconds=0, minmax=False):
    timespan = timedelta(seconds=max(seconds, config['interval']))

    now = datetime.utcnow()

    df = md.read_data(config['target'], now-timespan)
    if seconds > config['interval']:
        first = now - timespan
        last = now
        dfr = md.reduce(df[slice(first, last)], minmax=minmax)
        time = now
        debug = 'Average.'
    else:
        debug = 'Last row.'
        dfr = md.reduce(df.tail(1))
        time = df.index[-1]
        seconds = config['interval']

    data = {k: dfr[k] for k in dfr.index}
    data['timestamp'] = time.isoformat()
    data['date'] = str(time.date())
    data['time'] = time.time().strftime('%H:%M:%S')
    data['timespan'] = seconds
    data['debug'] = debug

    return data


@app.route('/latest/')
@app.route('/latest/<int:seconds>')
def api_meteo_latest(seconds=0):
    data = meteo_latest(seconds)
    return api_response(data)


@app.route('/')
@app.route('/<option>')
def page_root(option=''):
    latest = meteo_latest()
    context = {
        'name': config['name'],
        'latest': latest,
        'units': units,
        'last_day': meteo_latest(60*60*24, minmax=True),
        'last_week': meteo_latest(60*60*24*7, minmax=True),
        'show_plots': option == 'plots'
    }

    return render_template('overview.html', **context)


if __name__ == '__main__':
    app.run(host=config['server']['host'], port=config['server']['port'], debug=config['server']['debug'])
