#!/usr/bin/env python

# /*********************************
# Filename: katago_gtp_bot.py
# Creation Date: Jan, 2020
# Author: AHN
# **********************************/
#
# A wrapper around a  KataGo process to use it in a REST service.
# For use from a website were people can play KataGo.
#

from pdb import set_trace as BP
import os, sys, re
import numpy as np
import signal
import time

import subprocess
from threading import Thread,Lock,Event
import atexit

import goboard_fast as goboard
from agent_base import Agent
from agent_helpers import is_point_an_eye
from goboard_fast import Move
from gotypes import Point, Player
from go_utils import point_from_coords

g_response = None
g_handler_lock = Lock()
g_response_event = Event()
g_win_prob = -1
g_score = 0
g_bot_move = ''
g_best_ten = []

MOVE_TIMEOUT = 20 # seconds
#===========================
class KataGTPBot( Agent):
    # Listen on a stream in a separate thread until
    # a line comes in. Process line in a callback.
    #=================================================
    class Listener:
        #------------------------------------------------------------
        def __init__( self, stream, result_handler, error_handler):
            self.stream = stream
            self.result_handler = result_handler

            #--------------------------------------
            def wait_for_line( stream, callback):
                while True:
                    line = stream.readline().decode()
                    if line:
                        result_handler( line)
                    else: # probably my process died
                        error_handler()
                        break

            self.thread = Thread( target = wait_for_line,
                                  args = (self.stream, self.result_handler))
            self.thread.daemon = True
            self.thread.start()

    #--------------------------------------
    def __init__( self, katago_cmdline):
        Agent.__init__( self)
        self.katago_cmdline = katago_cmdline
        self.last_move_color = ''

        self.katago_proc, self.katago_listener = self._start_katagoproc()
        atexit.register( self._kill_katago)

    #------------------------------
    def _start_katagoproc( self):
        proc = subprocess.Popen( self.katago_cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
        listener = KataGTPBot.Listener( proc.stdout,
                                         self._result_handler,
                                         self._error_handler)
        return proc, listener

    #-------------------------
    def _kill_katago( self):
        if self.katago_proc.pid: os.kill( self.katago_proc.pid, signal.SIGKILL)

    # Parse katago response and trigger event to
    # continue execution.
    #---------------------------------------------
    def _result_handler( self, katago_response):
        global g_response
        global g_response_event
        global g_win_prob
        global g_score
        global g_bot_move
        global g_best_ten

        line = katago_response
        print( 'kata resp: %s' % line)
        if g_win_prob < 0 and 'CHAT:' in line: # Winrate
            print( '<-- ' + line)
            g_best_ten = []
            rstr = re.findall( r'Winrate\s+[^\s]+\s+', line)[0] # 'Winrate 44.37% '
            rstr = rstr.split()[1] # '44.37%'
            rstr = rstr[:-1] # '44.37'
            g_win_prob = 0.01 * float(rstr)
            rstr = re.findall( r'ScoreLead\s+[^\s]+\s+', line)[0] # 'ScoreLead -7.85 '
            rstr = rstr.split()[1] # '-7.85'
            g_score = float(rstr)
        elif  '@@' in line: # Our own logs from KataGo
            print( line)
        elif line.startswith('='): # GTP response
            resp = line.split('=')[1].strip()
            if resp:
                print( '<## ' + resp)
                g_response = self._resp2Move( resp)
                if g_response:
                    g_response_event.set()
        elif ' PSV ' in line: # Move candidates in descending order of PSV
            rstr = re.findall( r'PSV\s+[^\s]+\s+', line)[0] # 'PSV 842 '
            psv = rstr.split()[1]
            rstr = re.findall( r'^[^\s]+\s+:', line)[0] # 'E6  :'
            move = rstr.split()[0]
            g_best_ten.append( { 'move':move, 'psv':int(psv) })
        elif line.startswith('info '): # kata-analyze response
            self._katagoCmd( 'stop')
            rstr = re.findall( r'winrate\s+[^\s]+\s+', line)[0] # 'winrate 44.37% '
            rstr = rstr.split()[1] # '44.37%'
            rstr = rstr[:-1] # '44.37'
            g_win_prob = float(rstr)
            rstr = re.findall( r'scoreLead\s+[^\s]+\s+', line)[0] # 'scoreLead -7.85 '
            rstr = rstr.split()[1] # '-7.85'
            g_score = float(rstr)
            rstr = re.findall( r'\s+move\s+[^\s]+\s+', line)[0] # ' move Q16 '
            rstr = rstr.split()[1] # 'Q16'
            g_bot_move = rstr
            g_response = line
            g_response_event.set()

    # Resurrect a dead Katago
    #---------------------------
    def _error_handler( self):
        #print( '>>>>>>>>> err handler')
        global g_handler_lock
        with g_handler_lock:
            print( 'Katago died. Resurrecting.')
            self._kill_katago()
            self.katago_proc, self.katago_listener = self._start_katagoproc()
            time.sleep(1)
            print( 'Katago resurrected')

    # Convert Katago response string to a Move we understand
    #---------------------------------------------------------
    def _resp2Move( self, resp):
        res = None
        if 'pass' in resp:
            res = Move.pass_turn()
        elif 'resign' in resp:
            res = Move.resign()
        elif len(resp.strip()) in (2,3):
            p = point_from_coords( resp)
            res = Move.play( p)
        return res

    # Send a command to katago
    #-----------------------------
    def _katagoCmd( self, cmdstr):
        print( 'sending ' + cmdstr)
        cmdstr += '\n'
        p = self.katago_proc
        p.stdin.write( cmdstr.encode('utf8'))
        p.stdin.flush()
        #print( '--> ' + cmdstr)

    # Override Agent.select_move()
    #--------------------------------------------------------
    def select_move( self, game_state, moves, config = {}):
        global g_win_prob
        global g_response
        global g_response_event
        res = None
        g_win_prob = -1
        p = self.katago_proc

        # Set komi
        komi = config.get( 'komi', 7.5)
        self.set_komi( komi)

        # Reset the game
        self._katagoCmd( 'clear_board')
        self._katagoCmd( 'clear_cache')

        self.set_rules(komi)

        # Make the moves
        color = 'b'
        for idx,move in enumerate(moves):
            if move != 'pass' or idx > 20: # Early passes mess up the chinese handicap komi
                self._katagoCmd( 'play %s %s' % (color, move))
            color = 'b' if color == 'w' else 'w'

        # Ask for new move
        self.last_move_color = color
        #cmd = 'genmove ' + color + ' ' + str(randomness) + ' ' + str(playouts)
        cmd = 'genmove ' + color
        self._katagoCmd( cmd)
        # Hang until the move comes back
        print( '>>>>>>>>> waiting')
        success = g_response_event.wait( MOVE_TIMEOUT)
        g_response_event.clear()
        if not success: # I guess katago died
            print( 'error: katago select response timeout')
            self._error_handler()
            return None
        #time.sleep(2)
        print( 'response: ' + str(g_response))
        if g_response:
            res = g_response
            #print( '>>>>>>>>> clearing event')
            #g_response_event.clear()
        g_response = None
        print( 'katago select res: %s' % str(res))
        return res

    # score endpoint implementation
    #---------------------------------------------------
    def score( self, game_state, moves, config = {}):
        global g_response
        global g_response_event
        res = None
        p = self.katago_proc

        # Do we want ownership probs per intersection
        ownership = config.get( 'ownership', 'true')

        # Set komi
        komi = config.get( 'komi', 7.5)
        self.set_komi( komi)

        # Reset the game
        self._katagoCmd( 'clear_board')
        self._katagoCmd( 'clear_cache')

        self.set_rules(komi)

        # Make the moves
        color = 'b'
        for idx,move in enumerate(moves):
            if move != 'pass' or idx > 20: # Early passes mess up the chinese handicap komi
                self._katagoCmd( 'play %s %s' % (color, move))
            color = 'b' if color == 'w' else 'w'

        # Ask for the ownership info
        self._katagoCmd( 'kata-analyze 100 ownership %s' % ownership)
        # Hang until the info comes back
        print( '>>>>>>>>> waiting for score')
        success = g_response_event.wait( MOVE_TIMEOUT)
        g_response_event.clear()
        if not success: # I guess katago died
            print( 'error: katago score response timeout')
            self._error_handler()
            return None
        print( 'score response:\n' + str(g_response))
        if g_response:
            probs = []
            if ownership == 'true':
                probs = g_response.split( 'ownership')[1]
                probs = probs.split()
            res = probs
            #print( '>>>>>>>>> clearing event')
            #g_response_event.clear()
        g_response = None
        print( 'katago says: %s' % str(res))
        return res

    #----------------------------
    def set_rules( self, komi):
        # Rules should be jap for integer komi or even komi,
        # chinese for odd komi
        if not komi: komi=0
        rules = 'japanese'
        if komi != int(komi): # komi == n.5
            if (komi - 0.5) % 2: # 7.5, not 6.5
                rules = 'chinese'
        self._katagoCmd( 'kata-set-rules ' + rules)

    #---------------------------
    def set_komi( self, komi):
        if not komi: komi=0
        print( '>>>>>>>>> komi:%f',komi)
        self._katagoCmd( 'komi %f' % komi)

    # Override Agent.diagnostics()
    #------------------------------
    def diagnostics( self):
        global g_win_prob
        global g_score
        global g_best_ten
        return { 'winprob': float(g_win_prob), 'score': float(g_score), 'bot_move': g_bot_move, 'best_ten': g_best_ten }

    # Turn an idx 0..360 into a move
    #---------------------------------
    def _idx2move( self, idx):
        point = self.encoder.decode_point_index( idx)
        return goboard.Move.play( point)
