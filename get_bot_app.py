#!/usr/bin/env python

# /********************************************************************
# Filename: get_bot_app.py
# Author: AHN
# Creation Date: Mar, 2019
# **********************************************************************/
#
# Flask endpoint to get the next move from any bot
#

from pdb import set_trace as BP
import os
import numpy as np
from datetime import datetime

from flask import Flask
# A Flask extension for handling Cross Origin Resource Sharing (CORS), making cross-origin AJAX possible.
# Without this, javascript fetch can't use this API.
#from flask_cors import CORS
from flask import jsonify
from flask import request

from gotypes import Player, Point
from go_utils import print_board, print_move
import goboard_fast as goboard
from go_utils import coords_from_point, point_from_coords

# Return a flask app that will ask the specified bot for a move.
#-----------------------------------------------------------------
def get_bot_app( bot_map):

    here = os.path.dirname( __file__)
    static_path = os.path.join( here, 'static')
    app = Flask( __name__, static_folder=static_path, static_url_path='/static')

    @app.route('/select-move/<bot_name>', methods=['POST'])
    # Ask the named bot for the next move
    #--------------------------------------
    def select_move( bot_name):
        dtstr = datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')
        content = request.json
        print( '>>> %s select move %s %s' % (dtstr, bot_name, str(content.get('config',{}))))
        board_size = content['board_size']
        game_state = goboard.GameState.new_game( board_size)
        # Replay the game up to this point.
        for move in content['moves']:
            if move == 'pass':
                next_move = goboard.Move.pass_turn()
            elif move == 'resign':
                next_move = goboard.Move.resign()
            else:
                next_move = goboard.Move.play( point_from_coords(move))
            game_state = game_state.apply_move( next_move)
            #print_board( game_state.board)
        bot_agent = bot_map[bot_name]
        config = content.get('config',{})
        bot_move = bot_agent.select_move( game_state, content['moves'], config)
        if bot_move is None or bot_move.is_pass:
            bot_move_str = 'pass'
        elif bot_move.is_resign:
            bot_move_str = 'resign'
        else:
            bot_move_str = coords_from_point( bot_move.point)
        diag =  bot_agent.diagnostics()
        return jsonify({
            'bot_move': bot_move_str,
            'diagnostics': diag,
            'request_id': config.get('request_id','') # echo request_id
        })

    @app.route('/score/<bot_name>', methods=['POST'])
    # Ask the named bot for the pointwise ownership info
    #------------------------------------------------------
    def score( bot_name):
        dtstr = datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')
        content = request.json
        print( '>>> %s score %s %s' % (dtstr, bot_name, str(content.get('config',{}))))
        board_size = content['board_size']
        game_state = goboard.GameState.new_game( board_size)
        # Replay the game up to this point.
        for move in content['moves']:
            if move == 'pass':
                next_move = goboard.Move.pass_turn()
            elif move == 'resign':
                next_move = goboard.Move.resign()
            else:
                next_move = goboard.Move.play( point_from_coords(move))
            game_state = game_state.apply_move( next_move)
            #print_board( game_state.board)
        bot_agent = bot_map[bot_name]
        config = content.get('config',{})
        ownership_arr = bot_agent.score( game_state, content['moves'], config)
        diag =  bot_agent.diagnostics()
        return jsonify({
            'probs': ownership_arr,
            'diagnostics': diag,
            'request_id': config.get('request_id','') # echo request_id
        })

    return app
