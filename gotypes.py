#!/usr/bin/env python

# /********************************************************************
# Filename: gotypes.py
# Author: AHN
# Creation Date: Mar, 2019
# **********************************************************************/
#
# Types for implementing a go board
#

import enum
from collections import namedtuple

# Whose turn is it
#=============================
class Player( enum.Enum):
    black = 1
    white = 2

    @property
    def other( self):
        return Player.black if self == Player.white else Player.white

# Board intersection
#=================================================
class Point( namedtuple( 'Point', 'row col')):
    # Neighbors in tblr order
    #--------------------------
    def neighbors( self):
        return [
            Point( self.row - 1, self.col),
            Point( self.row + 1, self.col),
            Point( self.row, self.col - 1),
            Point( self.row, self.col + 1)
            ]

#------------
def main():
    p = Player( Player.white)
    print( p)
    print( p.other)
    print( Point(0,1).neighbors())
