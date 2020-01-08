#!/usr/bin/env python

# /********************************************************************
# Filename: go_utils.py
# Author: AHN
# Creation Date: Mar, 2019
# **********************************************************************/
#
# Various Go utility funcs
#

from pdb import set_trace as BP
import numpy as np
import gotypes

COLS = 'ABCDEFGHJKLMNOPQRST'
STONE_TO_CHAR = {
    None: ' . ',
    gotypes.Player.black: ' x ',
    gotypes.Player.white: ' o '
}

#-------------------------------
def print_move( player, move):
    if move.is_pass:
        move_str = 'passes'
    elif move.is_resign:
        move_str = 'resigns'
    else:
        move_str = '%s%d' % (COLS[move.point.col - 1], move.point.row)
    print( '%s %s' % (player, move_str))

#-------------------------
def print_board( board):
    for row in range( board.num_rows, 0, -1):
        bump = ' ' if row <= 9 else ''
        line = []
        for col in range( 1, board.num_cols + 1):
            stone = board.get( gotypes.Point( row, col))
            line.append( STONE_TO_CHAR[stone])
        print( '%s%d %s' % (bump, row, ''.join(line)))
    print('    ' + '  '.join( COLS[:board.num_cols]))

# Convert to sgf coords
#--------------------------------
def point_from_coords(coords):
    col = COLS.index(coords[0]) + 1
    row = int(coords[1:])
    return gotypes.Point(row=row, col=col)

# Convert from sgf coords
#------------------------------
def coords_from_point(point):
    return '%s%d' % (
        COLS[point.col - 1],
        point.row
    )

# Convert a point to a linear index
#-----------------------------
def p2idx(point, boardsize):
    return (point.row-1)*boardsize + point.col - 1

#==================
class MoveAge():
    def __init__(self, board):
        self.move_ages = - np.ones((board.num_rows, board.num_cols))

    def get(self, row, col):
        return self.move_ages[row, col]

    def reset_age(self, point):
        self.move_ages[point.row - 1, point.col - 1] = -1

    def add(self, point):
        self.move_ages[point.row - 1, point.col - 1] = 0

    def increment_all(self):
        self.move_ages[self.move_ages > -1] += 1
