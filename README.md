
A back end API to ask KataGo for moves
===========================================
AHN, Jan 2020

Used by the heroku app katago-gui.herokuapp.com, which is a separate github repo.
It is connected to heroku. A push to the master branch will deploy there.

katago-gui (the GUI) is a git submodule of katago-server (this repo).

WARNING: You need the katago weights. Get them with
$ cd katago-server
$ wget https://github.com/lightvector/KataGo/releases/download/v1.1/g104-b20c256-s447913472-d241840887.zip

To start the back end katago for testing, say
gunicorn katago_server:app --bind 0.0.0.0:2818 -w 1

The production port is 2819.

For testing, use
KATAGO_SERVER = 'https://ahaux.com/katago_server_test/'
in heroku_app.py .

The katago-gui GUI expects the back end at https://ahaux.com/katago_server .
The apache2 config on ahaux.com (marfa) forwards katago_server to port 2819:

$ cat /etc/apache2/sites-available/ahaux.conf
<VirtualHost *:443>
    SSLEngine On
    SSLCertificateFile /etc/ssl/certs/ahaux.com.crt
    SSLCertificateKeyFile /etc/ssl/private/ahaux.com.key
    SSLCACertificateFile /etc/ssl/certs/ca-certificates.crt

    ServerAdmin admin@ahaux.com
    ServerName www.ahaux.com
    DocumentRoot /var/www/ahaux
    ErrorLog /var/www/ahaux/log/error.log
    CustomLog /var/www/ahaux/log/access.log combined

   <Proxy *>
        Order deny,allow
          Allow from all
    </Proxy>
    ProxyPreserveHost On
    <Location "/katago_server">
          ProxyPass "http://127.0.0.1:2819/"
          ProxyPassReverse "http://127.0.0.1:2819/"
    </Location>

</VirtualHost>

Point your browser at
https://katago-gui.herokuapp.com

Deployment Process for katago-server
-------------------------------------
Log into the server (marfa), then:

$ cd /var/www/katago-server
$ systemctl stop katago-server
$ git pull origin master
$ git submodule update --init --recursive
$ systemctl start katago-server

The service configuration is in

/etc/systemd/system/katago-server.service:

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

Enable the service with

$ sudo systemctl daemon-reload
$ sudo systemctl enable katago-server

Deployment Process for katago-gui (the Web front end)
--------------------------------------------------------------

The heroku push happens through github.
Log into the server (marfa), then:

$ cd /var/www/katago-server/katago-gui
$ git pull origin dev
$ git pull origin master
<< Change the server address to prod in static/main.js >>
$ git merge dev
$ git push origin master

Log out of the server.
On your desktop, do

$ heroku logs -t --app katago-gui

to see if things are OK.

Point your browser at
https://katago-gui.herokuapp.com

CURL testing
------------------

Prod:

$ curl -d '{"board_size":19, "moves":["R4", "D16"]}' -H "Content-Type: application/json" -X POST https://ahaux.com/katago_server/select-move/katago_gtp_bot

Dev on marfa:

$ curl -d '{"board_size":19, "moves":["R4", "D16"]}' -H "Content-Type: application/json" -X POST https://ahaux.com/katago_server_test/select-move/katago_gtp_bot

Dev local on marfa:

$ curl -d '{"board_size":19, "moves":["R4", "D16"]}' -H "Content-Type: application/json" -X POST http://127.0.0.1:2818/select-move/katago_gtp_bot



=== The End ===
