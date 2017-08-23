# WXT meteo station logger and server

Simple logger and web server for the Vaisala WXT 536 meteo station.

## Disclaimer

This has been written to be installed on a small platform (like RasberryPi)
which is more or less dedicated to logging and providing meteo data.
The install precedure is quite a hack and is not very user friendly.

## Components

* Python package ``meteo`` contains:
  * ``logger.py`` for logging meteo data.
    This script is meant to be started by systemd only.
  * ``data.py`` helper functions to read and average csv data.
  * ``server.py`` The server for API endpoints and webpage.
* Systemd service files, which will go to ``/etc/systemd/system/``:
  * ``meteologger.service`` and
  * ``meteoserver.service``.
* Config file ``meteo.yml``, used by the server and the logger,
   will go to ``/etc``.
* Python setup files for pip ``setup.py`` and ``MANIFEST.in``
* Install script ``install.sh`` (quick hack, use with care).

## Requirements

* System dependencies:
  * systemd
  * Python 3


* Most important python dependencies (install with pip):
  * pandas 0.20.3 or newer
  * matplotlib
  * flask
  * flask-caching

 Installation of numpy, matplotlib and pandas via pip can take a long
 time on a RasberryPi.

## Installation

Run the ``install.sh`` as super user. Or copy paste the commands one by one.

## Managing the services

* Start / stop / status:
  * ``sudo systemctl {start|stop|restart|status} meteologger.service``
  * ``sudo systemctl {start|stop|restart|status} meteoserver.service``
* View journal log:
  * ``sudo journalctl -p info -fu meteologger.service``
  * ``sudo journalctl -p info -fu meteoserver.service``

## License (2-Clause BSD)

Copyright (c) 2017, Jonas Hagen

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.