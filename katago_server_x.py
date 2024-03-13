#!/usr/bin/env python

# /********************************************************************
# Filename: katago_server_x.py
# Author: AHN
# Creation Date: Jan, 2020
# **********************************************************************/
#
# A back end API to run KataGo as a REST service
#

from katago_gtp_bot import KataGTPBot
from get_bot_app import get_bot_app

#katago_cmd = './katago gtp -model g170-b40c256x2-s5095420928-d1229425124.bin.gz -config gtp_ahn_x.cfg '
katago_cmd = './katago gtp -model  kata1-b18c384nbt-s9131461376-d4087399203.bin.gz -config gtp_ahn_x.cfg '
katago_gtp_bot = KataGTPBot( katago_cmd.split() )

# Get an app with 'select-move/<botname>' endpoints
app = get_bot_app( name='katago_gtp_bot', bot=katago_gtp_bot )

#----------------------------
if __name__ == '__main__':
    app.run( host='0.0.0.0', port=2718, debug=True)
