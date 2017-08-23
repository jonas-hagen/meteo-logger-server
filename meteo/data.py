import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import glob


def read_csv(path):
    return pd.read_csv(path, index_col='time', parse_dates=['time'])


def read_data(path, since=None):
    """
    Read meteo data from csv files.
    :param path: Path to the csv files.
    :param since (datetime): Oldest data needed.
    :return: Dataframe.
    """
    pattern = os.path.join(path, 'meteo_????-??-??.csv')
    files = sorted(list(glob.glob(pattern)))

    df = read_csv(files.pop())
    while df.index.min() > since and files:
        df2 = read_csv(files.pop())
        df = pd.concat([df, df2])

    return df.sort_index()


def resample(df, freq='10min'):
    groups = df.groupby(pd.Grouper(freq=freq))
    return groups.apply(reduce)


def reduce(df, minmax=False):
    if df.empty:
        return pd.Series(index=df.columns)

    df_min = df.min()
    df_max = df.max()
    df_mean = df.mean()
    df_idxmin = df.idxmin()
    df_idxmax = df.idxmax()

    if minmax:
        index2 = list(df_mean.index).append([
            'air_temperature_min',
            'rel_humidity_min',
            'air_pressure_min',
            'air_temperature_max',
            'rel_humidity_max',
            'air_pressure_max',
        ])
    else:
        index2 = df_mean.index

    df2 = pd.Series(index=index2)

    df2['air_temperature'] = df_mean['air_temperature']
    df2['rel_humidity'] = df_mean['rel_humidity']
    df2['air_pressure'] = df_mean['air_pressure']
    df2['wind_speed_avg'] = df_mean['wind_speed_avg']
    df2['wind_speed_min'] = df_min['wind_speed_min']
    df2['wind_speed_max'] = df_max['wind_speed_max']
    df2['rain_accumulation'] = df_max['rain_accumulation']
    df2['rain_duration'] = df_max['rain_duration']
    df2['rain_intensity'] = df_mean['rain_intensity']
    df2['rain_peak_intensity'] = df_max['rain_peak_intensity']
    df2['heating_temperature'] = df_mean['heating_temperature']

    if minmax:
        df2['air_temperature_min'] = df_min['air_temperature']
        df2['rel_humidity_min'] = df_min['rel_humidity']
        df2['air_pressure_min'] = df_min['air_pressure']
        df2['air_temperature_max'] = df_max['air_temperature']
        df2['rel_humidity_max'] = df_max['rel_humidity']
        df2['air_pressure_max'] = df_max['air_pressure']

    # wind direction is special
    dir_avg = df['wind_dir_avg'].apply(np.deg2rad)
    dir_avg2 = np.arctan2(np.sum(np.sin(dir_avg)), np.sum(np.cos(dir_avg)))
    df2['wind_dir_avg'] = np.rad2deg(dir_avg2)
    df2['wind_dir_min'] = df['wind_dir_min'].loc[df_idxmax['wind_speed_min']]
    df2['wind_dir_max'] = df['wind_dir_max'].loc[df_idxmin['wind_speed_max']]

    return df2


def main():
    p = Path('data')
    stamp = datetime.utcnow()-timedelta(days=3)
    print(stamp)
    df = read_data(p, stamp)
    print('min: {}, max: {}, num: {}'.format(df.index.min(), df.index.max(), len(df)))

    print(reduce(df, minmax=True))
    print()
    print(reduce(df, minmax=True).index)


if __name__ == '__main__':
    main()
