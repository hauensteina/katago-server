#!/usr/bin/env python

# /********************************************************************
# Filename: agent_helpers.py
# Creation Date: Mar, 2019
# **********************************************************************/
#
# Check if a point is an eye.
# All four neighbors and three shoulders must be player color.
#

from pdb import set_trace as BP
from gotypes import Point

#--------------------------------------------
def is_point_an_eye(board, point, color):
    if point is None: return False
    if board.get(point) is not None: return False
    # All adjacent points must contain friendly stones.
    for neighbor in board.neighbors(point):
        neighbor_color = board.get(neighbor)
        if neighbor_color != color:
            return False
    # We must control 3 out of 4 corners if the point is in the middle
    # of the board; on the edge we must control all corners.
    friendly_corners = 0
    off_board_corners = 0
    corners = [
        Point(point.row - 1, point.col - 1),
        Point(point.row - 1, point.col + 1),
        Point(point.row + 1, point.col - 1),
        Point(point.row + 1, point.col + 1),
    ]
    for corner in corners:
        if board.is_on_grid(corner):
            corner_color = board.get(corner)
            if corner_color is None or corner_color == color:
                friendly_corners += 1
        else:
            off_board_corners += 1
    if off_board_corners > 0:
        # Point is on the edge or corner.
        return off_board_corners + friendly_corners == 4
    # Point is in the middle.
    return friendly_corners >= 3

#--------------------------------------------
def is_point_a_weak_eye(board, point, color):
    if point is None: return False
    if board.get(point) is not None: return False
    # All adjacent points must contain friendly stones.
    for neighbor in board.neighbors(point):
        neighbor_color = board.get(neighbor)
        if neighbor_color != color:
            return False
    return True
