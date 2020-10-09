#!/usr/bin/env python

# /********************************************************************
# Filename: katago_server.py
# Author: AHN
# Creation Date: Jan, 2020
# **********************************************************************/
#
# A back end API to run KataGo as a REST service
#

from katago_gtp_bot import KataGTPBot
from get_bot_app import get_bot_app

katago_cmd = './katago_eigen gtp -model g170e-b10c128-s1141046784-d204142634.bin.gz -config gtp_ahn_eigen.cfg '
katago_gtp_bot = KataGTPBot( katago_cmd.split() )

# Get an app with 'select-move/<botname>' endpoints
app = get_bot_app( name='katago_gtp_bot', bot=katago_gtp_bot )

#----------------------------
if __name__ == '__main__':
    app.run( host='0.0.0.0', port=2818, debug=True)
