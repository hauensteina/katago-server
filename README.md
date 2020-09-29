
A Back End API To Ask KataGo For Moves
===========================================
AHN, Sep 2020

Try it through a front end at https://katagui.herokuapp.com .
The repo for the fron end is at https://github.com/hauensteina/katago-gui .

The API is a Flask app, typically running on Ubuntu. Therefore, you probably want 
to be on a Ubuntu box where the default python is python version 3, which is pretty 
much standard these days.

WARNING: You need the katago weights. Get the weights with
```
$ cd katago-server
$ wget https://github.com/lightvector/KataGo/releases/download/v1.4.5/g170e-b20c256x2-s5303129600-d1228401921.bin.gz
```
The weights file must match the one used in `katago_server.py` in the line
```
katago_cmd = './katago gtp -model g170e-b20c256x2-s5303129600-d1228401921.bin.gz -config gtp_ahn.cfg '
```

To start the back end katago for testing, say
```
$ python katago_server.py 
```
This will start a Flask app listening on port 2718. Suppose the IP address
of your Ubuntu machine is `192.168.0.190`. To hit the API, from any machine 
on your network, try this:
```
curl -d '{"board_size":19, "moves":["R4", "D16"]}' -H "Content-Type: application/json" -X POST http://192.168.0.190:2718/select-move/katago_gtp_bot
```
It should return the ten best follow-up moves in descending quality, a score estimate, and a winning probability.

Production Deployment Process for katago-server
---------------------------------------------------------------
Log into your server, which probably has a strong GPU. Then:

```
$ cd /var/www/katago-server
$ systemctl stop katago-server
$ git pull origin master
$ git submodule update --init --recursive
$ systemctl start katago-server
```

The service configuration is in `/etc/systemd/system/katago-server.service` :

```
[Unit]
Description=katago-server
After=network.target

[Service]
User=ahauenst
Restart=on-failure
WorkingDirectory=/var/www/katago-server
ExecStart=/home/ahauenst/miniconda/envs/venv-dlgo/bin/gunicorn -c /var/www/katago-server/gunicorn.conf -b 0.0.0.0:2819 -w 1 katago_server:app

[Install]
WantedBy=multi-user.target
```

Enable the service with

```
$ sudo systemctl daemon-reload
$ sudo systemctl enable katago-server
```

=== The End ===
