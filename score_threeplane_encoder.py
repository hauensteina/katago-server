#!/usr/bin/env python

# /********************************************************************
# Filename: score_threeplane_encoder.py
# Author: AHN
# Creation Date: Apr, 2019
# **********************************************************************/
#
# Encode sgf files for later NN training to score a position.
# White and black stones live in separate input channels.
# A third channel indicates whose turn it is.

from pdb import set_trace as BP
import numpy as np

from encoder_base import Encoder
from goboard_fast import Point
from gotypes import Player

#=======================================
class ScoreThreeplaneEncoder(Encoder):

    #---------------------------------
    def __init__( self, board_size):
        self.board_width, self.board_height = board_size
        self.num_planes = 3

    #----------------
    def name( self):
        return 'score_threeplane_encoder'

    #------------------------------
    def encode( self, game_state):
        board_matrix = np.full( self.shape(), 0, dtype='int8')
        if game_state.next_player == Player.black:
            board_matrix[:,:,2] = np.zeros( (self.board_height, self.board_width) )
        elif game_state.next_player == Player.white:
            board_matrix[:,:,2] = np.ones( (self.board_height, self.board_width) )
        else:
            print( '>>>>> ERROR: unknown color')
            sys.exit(1)

        # Encode the stone planes
        for r in range( self.board_height):
            for c in range( self.board_width):
                p = Point( row = r + 1, col = c + 1)
                go_string = game_state.board.get_go_string( p)
                if go_string is None:
                    continue
                if go_string.color == Player.black:
                    board_matrix[r, c, 0] = 1
                else:
                    board_matrix[r, c, 1] = 1

        return board_matrix

    # Turn a board point into an integer index
    #--------------------------------------------
    def encode_point( self, point):
        return self.board_width * (point.row - 1) + (point.col - 1)

    # Turn an integer index into a board point
    #--------------------------------------------
    def decode_point_index( self, index):
        row = index // self.board_width
        col = index % self.board_width
        return Point(row=row + 1, col=col + 1)

    #-----------------------
    def num_points( self):
        return self.board_width * self.board_height

    #-------------------
    def shape( self):
        return self.board_height, self.board_width, self.num_planes

#-------------------------
def create( board_size):
    return ScoreThreeplaneEncoder( board_size)
