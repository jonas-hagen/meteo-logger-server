#!/usr/bin/env bash

set -x

cp -n meteo.default.yml /etc/meteo.yml
cp meteologger.service /etc/systemd/system/
cp meteoserver.service /etc/systemd/system/

apt install libsystemd-dev
pip3 install . --upgrade

systemctl enable meteologger.service
systemctl start meteologger.service

systemctl enable meteoserver.service
systemctl start meteoserver.service

