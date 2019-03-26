#!/usr/bin/env bash

set -x

systemctl stop meteologger.service
systemctl stop meteoserver.service

cp -n meteo.default.yml /etc/meteo.yml
cp meteologger.service /etc/systemd/system/
cp meteoserver.service /etc/systemd/system/

pip3 install . --upgrade

systemctl enable meteologger.service
systemctl enable meteoserver.service


echo 'You can start the services with:'
echo 'systemctl start meteologger.service meteoserver.service'
