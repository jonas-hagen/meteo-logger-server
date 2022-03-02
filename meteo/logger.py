#!/usr/bin/env python3
import argparse
import csv
import os
import pathlib
from collections import OrderedDict
from datetime import datetime, timedelta
from time import sleep
import yaml

import sqlalchemy as sqa

import serial
from serial.tools import list_ports

import logging

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

FIELDS = OrderedDict([
    ('time', 'time'),

    ('air_temperature', 'Ta'),
    ('rel_humidity', 'Ua'),
    ('air_pressure', 'Pa'),

    ('wind_speed_avg', 'Sm'),
    ('wind_speed_min', 'Sn'),
    ('wind_speed_max', 'Sx'),
    ('wind_dir_avg', 'Dm'),
    ('wind_dir_min', 'Dn'),
    ('wind_dir_max', 'Dx'),

    ('rain_accumulation', 'Rc'),
    ('rain_duration', 'Rd'),
    ('rain_intensity', 'Ri'),
    ('rain_peak_intensity', 'Rp'),

    # ('hail_accumulation', 'Hc'),
    # ('hail_duration', 'Hd'),
    # ('hail_intensity', 'Hi'),
    # ('hail_peak_intensity', 'Hp'),

    # ('heating_voltage', 'Vh'),
    # ('ref_voltage', 'Vr'),
    # ('supply_voltage', 'Vs'),
    ('heating_temperature', 'Th'),
    # ('internal_temperature', 'Tp'),

    # ('information', 'Id'),
])

reverse_FIELDS = {v: k for k, v in FIELDS.items()}


def append_csv_row(path, data, default='NaN'):
    """Append a row to a CSV file. If the file does not exist already, also write the header."""
    new_file = not path.exists()
    f = path.open(mode='a', newline='')
    writer = csv.DictWriter(f, FIELDS.keys(), restval=default)
    if new_file:
        logger.info('Created new file '+str(path))
        writer.writeheader()
    writer.writerow(data)


def delete_log_files_if_needed(log_dir, max_files):
    path = pathlib.Path(log_dir)
    files = sorted(list(path.glob('meteo_????-??-??.csv')))
    if len(files) > max_files:
        logger.info('Too many log files. Deleting oldest.')
        old = files[0:len(files)-max_files]
        for p in old:
            p.unlink()


def convert_unit(key, value, unit, default=None):
    """Convert units to hPa, degC, mm and mm/h."""
    def identity(v):
        return v

    dispatcher = dict()

    # Speed
    dispatcher['S'] = {
        'M': identity,  # m/s
        'K': lambda v: 1000/3600 * v,  # km/h
        'S': lambda v: 0.44704 * v,  # mph
        'N': lambda v: 0.514444 * v,  # knots
    }

    # Pressure
    dispatcher['P'] = {
        'H': identity,  # hPa
        'P': lambda v: v / 100,  # Pa
        'B': lambda v: v * 1000,  # bar
        'M': lambda v: v * 1.33322,  # mmHg
        'I': lambda v: v * 25.4 * 1.33322,  # inHg
    }

    # Temperature
    dispatcher['T'] = {
        'C': identity,  # Celsius
        'F': lambda v: (v - 32) * 5/9
    }

    # Rain
    dispatcher['R'] = {
        'M': identity,  # mm or mm/h
        's': identity,  # seconds
        'I': lambda v: 52.4 * v,  # in or in/h
    }

    if unit == '#':
        return default
    else:
        conversion_fuc = dispatcher.get(key[0], {unit: identity})[unit]
        return conversion_fuc(value)


def parse_line(line):
    """Parse a data message from the meteo station."""
    parts = line.split(',')
    msg_type = parts.pop(0)
    data = dict()
    for p in parts:
        key, payload = p.split('=')
        value = payload[:-1]
        unit = payload[-1]
        data[key] = convert_unit(key, value, unit, default='NaN')
    data_row = {reverse_FIELDS[k]: v for k, v in data.items() if k in reverse_FIELDS}
    return msg_type, data_row


def parse_settings(line):
    """Parse a data message from the meteo station."""
    parts = line.split(',')
    msg_type = parts.pop(0)
    data = dict()
    for p in parts:
        key, value = p.split('=')
        data[key] = value
    return msg_type, data


class MeteoTerminal(serial.Serial):
    """Simple wraper around pyserial object to send and receive commands from meteo station."""

    def __init__(self, name, *args, **kwargs):
        default_kwargs = {'baudrate': 19200, 'timeout': 2}
        default_kwargs.update(kwargs)
        super().__init__(name, *args, **default_kwargs)
        self.clear()

    def ask(self, s):
        self.send(s)
        return self.receive()

    def clear(self, loud=False):
        """Clear any previous incomplete input"""
        line = self.receive()
        while line:
            if loud:
                logger.warning('Unexpected response: ' + line)
            line = self.receive()
        self.send('?')
        self.readline()

    def send(self, s):
        self.write((s + '\r\n').encode('utf-8'))
        self.flush()

    def receive(self):
        bs = self.readline()
        if bs:
            return bs.decode('utf-8').strip()
        else:
            return ''

    def setup(self, settings):
        for line in settings:
            cmd, expected = parse_settings(line)
            cmd, current = parse_settings(self.ask(cmd))
            current = {k: v for k, v in current.items() if k in expected}
            if current != expected:
                answer = self.ask(line)
                logger.info('Setup "{}", answer "{}".'.format(line, answer))
                self.clear(loud=True)
            else:
                logger.info('Setup "{}" already ok.'.format(line))

    @staticmethod
    def find_station():
        ports = list_ports.comports()
        found = None
        for name, desc, hw in ports:
            try:
                logger.debug('Try ' + name)
                with MeteoTerminal(name) as ser:
                    answer = ser.ask('0')
                    if answer == '0':
                        logger.debug('OK: '+name)
                        found = name
                        break
            except Exception:
                pass
        logger.info('Found meteo station: {}'.format(found))
        return found


def create_db_table(conn, table):
    logger.info('Create table {} if not exists.'.format(table))
    if conn.dialect.name == 'mysql':
        columns = [sqa.Column('time', sqa.dialects.mysql.DATETIME(fsp=6), primary_key=True), ]
    else:
        columns = [sqa.Column('time', sqa.types.DateTime(), primary_key=True), ]
    columns += [sqa.Column(name, sqa.types.Float()) for name in FIELDS if name != 'time']

    meta = sqa.MetaData()
    table = sqa.Table(table, meta, *columns)

    table.create(conn, checkfirst=True)
    return table


def meteo_logger(config):
    if config['serial'] == 'auto':
        port = MeteoTerminal.find_station()
    else:
        port = config['serial']
    if port is None:
        logger.error('No meteo station found. Specify port in config file.')
        exit(1)

    db_engine = None
    db_table = None
    if config['database']['use_database']:
        try:
            db_engine = sqa.create_engine(config['database']['url'])
            with db_engine.connect() as conn:
                db_table = create_db_table(conn, config['database']['table'])
        except Exception as e:
            logger.error('While setting up database: ' + str(e))
            exit(1)

    output_dir = config['target']
    interval = config['interval']

    with MeteoTerminal(port, baudrate=config['baudrate']) as term:
        term.setup(config['setup'])

        logger.info('Will now take action every {} s.'.format(interval))
        while True:
            try:
                now = datetime.utcnow()

                # Poll and store measurement
                msg = term.ask('0R0')
                msg_type, data = parse_line(msg)
                data['time'] = now.isoformat() + 'Z'

                # Write csv
                day = now.date()
                path = pathlib.Path(output_dir) / str(now.year) / ('meteo_' + str(day) + '.csv')
                path.parent.mkdir(parents=True, exist_ok=True)
                append_csv_row(path, data)

                # Store to database
                if db_engine is not None:
                   with db_engine.connect() as conn:
                        conn.execute(db_table.insert(), **data)

                if (now + timedelta(seconds=interval)).day > now.day:
                    # Reset counters
                    # next measurement will be in next day, so we reset now
                    logger.info('Reset precipitation counters.')
                    term.ask('0XZRU')  # Precipitation counter reset
                    term.ask('0XZRI')  # Precipitation intensity reset

                    # Housekeeping
                    delete_log_files_if_needed(output_dir, config['max_files'])

                # Time
                if datetime.utcnow() - now >= timedelta(seconds=interval):
                    logger.warning('Loop took longer than interval. Working as fast as possible.')
                while datetime.utcnow() - now < timedelta(seconds=min(interval-2, 0)):
                    sleep(1)
                while datetime.utcnow() - now < timedelta(seconds=interval):
                    pass  # busy loop
            except KeyboardInterrupt:
                logger.info('Terminated by user.')
                exit(0)
            except Exception as e:
                logger.warning('Exception in main loop: ' + str(e))


def main():
    with open('/etc/meteo.yml', 'r') as f:
        config = yaml.load(f)
    meteo_logger(config)


if __name__ == '__main__':
    main()
