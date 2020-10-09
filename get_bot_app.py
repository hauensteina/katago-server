#!/usr/bin/env python

# /********************************************************************
# Filename: get_bot_app.py
# Author: AHN
# Creation Date: Mar, 2019
# **********************************************************************/
#
# Flask endpoint to get the next move from any bot
#

import os
from datetime import datetime

from flask import Flask
from flask import jsonify
from flask import request

# Return a flask app that will ask the specified bot for a move.
#-----------------------------------------------------------------
def get_bot_app( name,bot):

    here = os.path.dirname( __file__)
    static_path = os.path.join( here, 'static')
    app = Flask( __name__, static_folder=static_path, static_url_path='/static')

    @app.route('/select-move/' + name, methods=['POST'])
    # Ask the named bot for the next move
    #--------------------------------------
    def select_move():
        dtstr = datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')
        content = request.json
        print( '>>> %s select move %s %s' % (dtstr, name, str(content.get('config',{}))))
        board_size = content['board_size']
        config = content.get('config',{})
        bot_move = bot.select_move( content['moves'], config)
        diag =  bot.diagnostics()
        return jsonify({
            'bot_move': bot_move, # bot_move_str,
            'diagnostics': diag,
            'request_id': config.get('request_id','') # echo request_id
        })

    @app.route('/score/' + name, methods=['POST'])
    # Ask the named bot for the pointwise ownership info
    #------------------------------------------------------
    def score():
        dtstr = datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')
        content = request.json
        print( '>>> %s score %s %s' % (dtstr, name, str(content.get('config',{}))))
        board_size = content['board_size']
        config = content.get('config',{})
        ownership_arr = bot.score( content['moves'], config)
        diag =  bot.diagnostics()
        return jsonify({
            'probs': ownership_arr,
            'diagnostics': diag,
            'request_id': config.get('request_id','') # echo request_id
        })

    return app
