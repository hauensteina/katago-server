
A Back End API To Ask KataGo For Moves
===========================================
AHN, Sep 2020

What is this
---------------

Katago-server is the back end for https://github.com/hauensteina/katagui .

Katago-server exposes a REST API implemented as a Python Flask app. This repo includes an executable for katago, running
on 64-bit Ubuntu. Therefore, you do not have to look for katago elsewhere, as long as 
you are on a 64-bit Ubuntu box. The default Python has to be Python 3, which is pretty 
much standard these days.

Installation
---------------

```
$ git clone https://github.com/hauensteina/katago-server.git
$ cd katago-server
```

To start the back end katago for testing, say
```
$ python katago_server.py 
```
This will start a Flask app listening on port 2718. 

If you get error messages about missing libraries, `sudo apt install <library-package>` is your friend.
Google will tell you which packages you need.

To hit the API, from a second terminal, 
try this:
```
$ curl -d '{"board_size":19, "moves":["R4", "D16"]}' -H "Content-Type: application/json" -X POST http://127.0.0.1:2718/select-move/katago_gtp_bot
```
It should return the ten best follow-up moves in descending quality, a score estimate, and a winning probability.

If you want a territory map, use this:
```
$ curl -d '{"board_size":19, "moves":["R4", "D16"]}' -H "Content-Type: application/json" -X POST http://127.0.0.1:2718/score/katago_gtp_bot
```

The API is used by a front end at https://katagui.herokuapp.com .

The repo for the front end is at https://github.com/hauensteina/katagui .


Running katago-server on Heroku, just for kicks
-------------------------------------------------------

Heroku is a platform which allows you to easily deploy an API for the general public to use,
among other things. And best of all, if you do not have a lot of traffic, it is totally free.

The drawback of Heroku is compute power. There is no GPU, and no hardware acceleration,
so KataGo will be quite slow. We will deploy to Heroku anyway, just because we can and
because this is cool. It will also be helpful if you want to play around with the front
end available at `https://github.com/hauensteina/katagui.git`.

Heroku runs Ubuntu, and therefore our katago_eigen binary should just work as is.
You also need to be on Ubuntu yourself to follow the steps given below. If you aren't, get yourself
a virtual Ubuntu like so:

https://brb.nci.nih.gov/seqtools/installUbuntu.html

Get a Heroku login at https://heroku.com .

Install the Heroku CLI. Instructions can be found at
https://devcenter.heroku.com/articles/heroku-cli .

Open a Ubuntu terminal and log into Heroku:

```
$ heroku login -i
```

Create a new Heroku project with

```
$ mkdir my-katago-server
$ cd my-katago-server
$ git init
$ heroku apps:create my-katago-server
```
You probably want to change the name `my-katago-server` to something less generic to
avoid name collisions.

We need to install the boost library on Heroku, which is possible using the apt buildpack:

```
$ heroku buildpacks:add --index 1 heroku-community/apt
```

Required Ubuntu packages are listed in `Aptfile`:

```
$ cat Aptfile
libboost-all-dev
```

To get the server code from github, let's add a second remote repo `github` to pull from:

`$ git remote add github https://github.com/hauensteina/katago-server.git`

The pull the code for the project to your local file system:

`$ git pull github master`

A ten block network is included. Things will be slow, and a small network will be faster. It is stronger than you think.
The weights are in `g170e-b10c128-s1141046784-d204142634.bin.gz`. We run the net with only one thread and 8 playouts, 
configured in `gtp_ahn_eigen.cfg`.

Make sure you are on python 3:

```
$ python --version
Python 3.7.1
```

Make a virtual environment to manage our package dependencies:

`$ python -m venv venv`

Activate the venv:

`$ source ./venv/bin/activate`

Install additional packages into the venv:

```
$ pip install flask
$ pip install gunicorn
```

The script `katago_server_eigen.py` uses a 10 block network and the binary katago_eigen, which runs on the CPU only,
with no GPU acceleration. The katago_eigen binary was rebuilt from source because the eigen binary contained in the official KataGo release
failed on heroku with 'illegal instruction' . Our build was done on a virtual Ubuntu 16 VMWare image running on a Mac. You don't have
to do this again, but just for reference:

```
$ git clone https://github.com/lightvector/KataGo.git
$ cd KataGo/cpp
$ cmake . -DUSE_BACKEND=EIGEN
$ make
$ mv katago katago_eigen
```

Run the server with

`$ python katago_server_eigen.py`

You should see a lot of output from katago, with the last line looking like

`kata resp: 2020-10-03 18:27:36+0000: GTP ready, beginning main protocol loop`

Make a requirements.txt to tell heroku what python packages to install:

`$ pip freeze > requirements.txt`

Create a Procfile to tell heroku how to start the app. It should look like this:

```
$ cat Procfile
web: gunicorn katago_server_eigen:app -w 1
```

Test locally:

```
$ heroku local
7:21:06 PM web.1 |  [2020-10-03 19:21:06 +0000] [24136] [INFO] Starting gunicorn 20.0.4
7:21:07 PM web.1 |  [2020-10-03 19:21:06 +0000] [24136] [INFO] Listening at: http://0.0.0.0:5000 (24136)
7:21:07 PM web.1 |  [2020-10-03 19:21:06 +0000] [24136] [INFO] Using worker: sync
7:21:07 PM web.1 |  [2020-10-03 19:21:06 +0000] [24139] [INFO] Booting worker with pid: 24139
```

And in a second terminal, see if you can get a move out of it:

```
$ curl -d '{"board_size":19, "moves":["R4", "D16"]}' -H "Content-Type: application/json" -X POST http://127.0.0.1:5000/select-move/katago_gtp_bot

```

This should come back with some json containing the ten best moves, a winning probability, and a score estimate.

To get the ownership probability for each intersection, say

```
$ curl -d '{"board_size":19, "moves":["R4", "D16"]}' -H "Content-Type: application/json" -X POST http://127.0.0.1:5000/score/katago_gtp_bot
```

To see how the endpoints `select-move` and `score` are implemented, look at `get_bot_app.py`.
Communication between Python and the KataGo binary is handled in `katago_gtp_bot.py`.

Now we're ready to push everything to Heroku for all the world to see:

```
$ git add requirements.txt
$ git add Procfile
$ git commit -m 'first commit to heroku'
$ git push heroku master
```

Look at the server logs to see what is going on:

```
heroku logs -t --app my-katago-server
```

If things went well, you should see something like
```
2020-10-04T18:17:52.366558+00:00 heroku[run.6466]: State changed from starting to up
2020-10-04T18:17:52.497652+00:00 heroku[run.6466]: Awaiting client
2020-10-04T18:17:52.522600+00:00 heroku[run.6466]: Starting process with command `bash`
2020-10-04T18:18:22.878654+00:00 heroku[run.6466]: Process exited with status 0
2020-10-04T18:18:22.917188+00:00 heroku[run.6466]: State changed from up to complete
2020-10-04T18:20:43.000000+00:00 app[api]: Build started by user hauensteina@gmail.com
2020-10-04T18:21:21.443524+00:00 app[api]: Release v8 created by user hauensteina@gmail.com
2020-10-04T18:21:21.443524+00:00 app[api]: Deploy d17dfa7c by user hauensteina@gmail.com
2020-10-04T18:21:32.000000+00:00 app[api]: Build succeeded
```


Test with a curl to our Heroku project URL, from anywhere on the internet at all:

```
$ curl -d '{"board_size":19, "moves":["R4", "D16"]}' -H "Content-Type: application/json" -X POST https://my-katago-server.herokuapp.com/select-move/katago_gtp_bot
$ curl -d '{"board_size":19, "moves":["R4", "D16"]}' -H "Content-Type: application/json" -X POST https://my-katago-server.herokuapp.com/score/katago_gtp_bot
```

After a second or two, you should get some json output with moves and probabilities.

If you got this far and it works, congratulations! Drop me a note at hauensteina@gmail.com .

You might want to look at https://github.com/hauensteina/katagui.git to see if you can get the front end to run
with katago-server.



Production Deployment Process for katago-server
---------------------------------------------------------------
Log into your Ubuntu server, which hopefully has a strong GPU. Then:
```
$ cd /var/www
$ git clone https://github.com/hauensteina/katago-server.git
```

Configure katago-server as a service in `/etc/systemd/system/katago-server.service` :

```
[Unit]
Description=katago-server
After=network.target

[Service]
User=<you-user-name>
Restart=on-failure
WorkingDirectory=/var/www/katago-server
ExecStart=<your-home-dir>/miniconda/envs/venv-dlgo/bin/gunicorn -c /var/www/katago-server/gunicorn.conf -b 0.0.0.0:2819 -w 1 katago_server:app

[Install]
WantedBy=multi-user.target
```

Enable the service with
```
$ sudo systemctl daemon-reload
$ sudo systemctl enable katago-server
```

Start the service:
```
$ sudo systemctl start katago-server
```

The http access and error logs are in `/tmp/kata_access.log` and `/tmp/kata_error.log`.
The location of the http logs is configured in `/var/www/katago-server/gunicorn.conf` .
The python logs from `katago_server.py` are accessible with 

`$ journalctl -f -u katago-server`

where the `-f` option gives live updates, like `tail -f` .


=== The End ===
