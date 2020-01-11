#!/usr/bin/env python

# /********************************************************************
# Filename: agent_base.py
# Author: AHN
# Creation Date: Mar, 2019
# **********************************************************************/
#
# Base class for Go Agents
#

#==============
class Agent:
    #---------------------
    def __init__(self):
        pass

    #-----------------------------------------------------------
    def select_move( self, game_state, moves=None, config={}):
        raise NotImplementedError()

    #-----------------------------------------------------------
    def score( self, game_state, moves=None, config={}):
        raise NotImplementedError()

    #---------------------------
    def diagnostics( self):
        return {}
