# /********************************************************************
# Filename: katago-server/scripts/01_server_selfmatch/server_match.py
# Author: AHN
# Creation Date: Jun, 2021
# **********************************************************************/
#
# A server match between two katago-server instances.
#

from pdb import set_trace as BP
import os,sys,re,datetime
import glob,shutil
import requests
import argparse

GAME_OVER_PROB = 0.1
OUTFOLDER = 'server_match.out'

#-----------------------------
def usage( printmsg=False):
    name = os.path.basename( __file__)
    msg = '''

    Name:
      %s: Let two katago-server instances play a match
    Synopsis:
      %s --ngames <n> --server1 <url_server_1> --server2 <url_server_2>
    Description:
      Run an n game match between server1 and server2. Color alternates.
      Games are stored in the folder server_match.out .
      On production, port 2819 is 20b/256, port 2820 is 40b/1024, port 2821 is 10b/256 .
      The port 2718 is the manually started test server.
    Examples:
      %s --ngames 100 --server1 http://192.168.0.190:2821 --server2 http://192.168.0.190:2718

--
''' % (name,name,name)
    if printmsg:
        print(msg)
        exit(1)
    else:
        return msg


#-------------
def main():
    if len(sys.argv) == 1: usage( True)
    parser = argparse.ArgumentParser( usage=usage())
    parser.add_argument( "--ngames", required=True, type=int)
    parser.add_argument( "--server1", required=True)
    parser.add_argument( "--server2", required=True)
    args = parser.parse_args()

    if os.path.exists( OUTFOLDER):
        print( 'ERROR: %s exists. Please move it away.' % OUTFOLDER)
        exit(1)

    os.mkdir( OUTFOLDER)

    run_match( args.server1, args.server2, args.ngames)

#------------------------------------------
def run_match( server1, server2, ngames):
    gamecount = 0
    servers = [server1, server2]
    wins = [0,0]

    while gamecount < ngames:
        winprob = 0.5
        moves = []
        black_server_idx = gamecount % 2
        cur_server_idx = black_server_idx

        while winprob > GAME_OVER_PROB and 1.0 - winprob > GAME_OVER_PROB:
            bot_move, winprob = move( servers[cur_server_idx], moves)
            cur_server_idx = 1 - cur_server_idx
            moves.append( bot_move)
            print( '.', end='')
            sys.stdout.flush()

        gamecount += 1
        result = ''
        if winprob > GAME_OVER_PROB: # Black won
            wins[black_server_idx] += 1
            result = 'B+'
        else: # White won
            wins[1-black_server_idx] += 1
            result = 'W+'

        store_game( OUTFOLDER, gamecount, moves, servers[black_server_idx], servers[1-black_server_idx], result)

        print( '\nServer1:%d Server2:%d' % (wins[0], wins[1]))
        if gamecount == ngames:
            print( '========== match over ==========')
            break

#--------------------------
def move( server, moves):
    url = server + '/select-move/katago_gtp_bot'
    args = { "board_size":19, "moves":moves }
    resp = requests.post( url, json=args)
    try:
        res = resp.json()
    except Exception as e:
        print( 'Exception in move()')
        print( 'args %s' % str(args))
    return res['bot_move'], res['diagnostics']['winprob']

#----------------------------------------------------------
def store_game( folder, gnum, moves, bplayer, wplayer, result):
    sgf = moves2sgf( moves, bplayer, wplayer, result)
    fname = folder + '/game_%03d.sgf' % gnum
    with open( fname, 'w') as out:
        out.write( sgf)

# Convert a list of moves like ['Q16',...] to sgf
#---------------------------------------------------
def moves2sgf( moves, bplayer, wplayer, result):
    COLS = 'ABCDEFGHJKLMNOPQRST'
    sgf = '(;FF[4]SZ[19]\n'
    sgf += 'SO[server_match.py]\n'
    dtstr = str(datetime.date.today())
    km = 7.5

    sgf += 'PB[%s]\n' % bplayer
    sgf += 'PW[%s]\n' % wplayer
    sgf += 'RE[%s]\n' % result
    sgf += 'KM[%s]\n' % km
    sgf += 'DT[%s]\n' % dtstr

    movestr = ''
    result = ''
    color = 'B'
    for idx,move in enumerate(moves):
        othercol = 'W' if color == 'B' else 'B'
        if move == 'resign':
            result = 'RE[%s+R]' % othercol
        elif move == 'pass':
            movestr += ';%s[tt]' % color
        elif move == 'A0':
            movestr += ';%s[tt]' % color
        else:
            col = COLS.index( move[0]) + 1
            row = int( move[1:])
            col_s = 'abcdefghijklmnopqrstuvwxy'[col - 1]
            row_s = 'abcdefghijklmnopqrstuvwxy'[19 - row]
            movestr += ';%s[%s%s]' % (color,col_s,row_s)
        color = othercol

    sgf += result
    sgf += movestr
    sgf += ')'
    return sgf

if __name__ == '__main__':
    main()
