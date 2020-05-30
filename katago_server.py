#!/usr/bin/env python

# /********************************************************************
# Filename: katago_server.py
# Author: AHN
# Creation Date: Jan, 2020
# **********************************************************************/
#
# A back end API to run KataGo as a REST service
#

from pdb import set_trace as BP
import os, sys, re
import numpy as np
from datetime import datetime
import uuid
from io import BytesIO

import flask
from flask import jsonify,request,Response,send_file

#import keras.models as kmod
#from keras import backend as K
#import tensorflow as tf

from gotypes import Point, Player
from katago_gtp_bot import KataGTPBot
from get_bot_app import get_bot_app
from sgf import Sgf_game
from go_utils import coords_from_point, point_from_coords
import goboard_fast as goboard
from encoder_base import get_encoder_by_name
from scoring import compute_nn_game_result


katago_cmd = './katago gtp -model g170e-b20c256x2-s4384473088-d968438914.bin.gz -config gtp_ahn.cfg '
katago_gtp_bot = KataGTPBot( katago_cmd.split() )

# Get an app with 'select-move/<botname>' endpoints
app = get_bot_app( {'katago_gtp_bot':katago_gtp_bot} )


#----------------------------
if __name__ == '__main__':
    app.run( host='127.0.0.1', port=2818, debug=True)
