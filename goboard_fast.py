
from pdb import set_trace as BP

import copy
from gotypes import Player, Point
import scoring
import zobrist
from go_utils import MoveAge

#__all__ = [
#    'Board',
#    'GameState',
#    'Move',
#]

neighbor_tables = {}
corner_tables = {}

#------------------------------
def init_neighbor_table(dim):
    rows, cols = dim
    new_table = {}
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            p = Point(row=r, col=c)
            full_neighbors = p.neighbors()
            true_neighbors = [
                n for n in full_neighbors
                if 1 <= n.row <= rows and 1 <= n.col <= cols]
            new_table[p] = true_neighbors
    neighbor_tables[dim] = new_table

#----------------------------
def init_corner_table(dim):
    rows, cols = dim
    new_table = {}
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            p = Point(row=r, col=c)
            full_corners = [
                Point(row=p.row - 1, col=p.col - 1),
                Point(row=p.row - 1, col=p.col + 1),
                Point(row=p.row + 1, col=p.col - 1),
                Point(row=p.row + 1, col=p.col + 1),
            ]
            true_corners = [
                n for n in full_corners
                if 1 <= n.row <= rows and 1 <= n.col <= cols]
            new_table[p] = true_corners
    corner_tables[dim] = new_table

#====================================
class IllegalMoveError(Exception):
    pass

# The color of a string, the set of its points (r,c),
# and the set of its liberties.
#======================================================
class GoString():

    #----------------------------------------------
    def __init__( self, color, stones, liberties):
        self.color = color
        self.stones = frozenset(stones)
        self.liberties = frozenset(liberties)

    # Return a new GoString with given liberty removed
    #---------------------------------------------------
    def without_liberty( self, point):
        new_liberties = self.liberties - set([point])
        return GoString(self.color, self.stones, new_liberties)

    # Return a new GoString with given liberty added
    #---------------------------------------------------
    def with_liberty( self, point):
        new_liberties = self.liberties | set([point])
        return GoString(self.color, self.stones, new_liberties)

    # Return a new GoString after merging with another one
    #-------------------------------------------------------
    def merged_with( self, string):
        assert string.color == self.color
        combined_stones = self.stones | string.stones
        return GoString(
            self.color,
            combined_stones,
            (self.liberties | string.liberties) - combined_stones)

    @property
    #-------------------------
    def num_liberties( self):
        return len(self.liberties)

    # So GoString can be dict key or in set
    #----------------------------------------
    def __hash__( self):
        return hash((
            self.color,
            self.stones,
            self.liberties))

    #-------------------------
    def __eq__( self, other):
        return isinstance( other, GoString) and \
            self.color == other.color and \
            self.stones == other.stones and \
            self.liberties == other.liberties

    #--------------------------------------
    def __deepcopy__( self, memodict={}):
        return GoString( self.color, self.stones, copy.deepcopy(self.liberties))

# A go position represented as a dictionary with (r,c) as keys.
# A dict value is a GoString, or None if empty.
#================================================================
class Board():

    #----------------------------------------
    def __init__( self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = {}
        self._hash = zobrist.EMPTY_BOARD

        global neighbor_tables
        dim = (num_rows, num_cols)
        if dim not in neighbor_tables:
            init_neighbor_table(dim)
        if dim not in corner_tables:
            init_corner_table(dim)
        self.neighbor_table = neighbor_tables[dim]
        self.corner_table = corner_tables[dim]
        self.move_ages = MoveAge(self)

    #---------------------------
    def neighbors( self, point):
        return self.neighbor_table[point]

    #---------------------------
    def corners( self, point):
        return self.corner_table[point]

    #-------------------------------------
    def place_stone( self, player, point):
        assert self.is_on_grid( point)
        if self._grid.get( point) is not None:
            print( 'Illegal play on %s' % str(point))
        assert self._grid.get( point) is None
        # 0. Examine the adjacent points.
        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []
        self.move_ages.increment_all()
        self.move_ages.add( point)
        for neighbor in self.neighbor_table[point]:
            neighbor_string = self._grid.get( neighbor)
            if neighbor_string is None:
                liberties.append( neighbor)
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append( neighbor_string)
            else:
                if neighbor_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append( neighbor_string)
        new_string = GoString( player, [point], liberties)

        # 1. Merge any adjacent strings of the same color.
        for same_color_string in adjacent_same_color:
            new_string = new_string.merged_with( same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string
        # Remove empty-point hash code.
        self._hash ^= zobrist.HASH_CODE[point, None]
        # Add filled point hash code.
        self._hash ^= zobrist.HASH_CODE[point, player]

        # 2. Reduce liberties of any adjacent strings of the opposite
        #    color.
        # 3. If any opposite color strings now have zero liberties,
        #    remove them.
        for other_color_string in adjacent_opposite_color:
            replacement = other_color_string.without_liberty( point)
            if replacement.num_liberties:
                self._replace_string(other_color_string.without_liberty( point))
            else:
                self._remove_string( other_color_string)

    #---------------------------------------
    def _replace_string( self, new_string):
        for point in new_string.stones:
            self._grid[point] = new_string

    #-----------------------------------
    def _remove_string( self, string):
        for point in string.stones:
            self.move_ages.reset_age( point)
            # Removing a string can create liberties for other strings.
            for neighbor in self.neighbor_table[point]:
                neighbor_string = self._grid.get( neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    self._replace_string( neighbor_string.with_liberty( point))
            self._grid[point] = None
            # Remove filled point hash code.
            self._hash ^= zobrist.HASH_CODE[point, string.color]
            # Add empty point hash code.
            self._hash ^= zobrist.HASH_CODE[point, None]

    #-------------------------------------
    def strings_in_atari( self, player):
        return self.strings_with_liberties( player, 1)

    #---------------------------------------------
    def strings_with_liberties( self, player, n):
        strs = self._grid.values()
        strs = set(strs)
        res = { s for s in strs if s and s.color == player and s.num_liberties == n }
        return res

    #------------------------------------------
    def is_self_capture( self, player, point):
        friendly_strings = []
        for neighbor in self.neighbor_table[point]:
            neighbor_string = self._grid.get( neighbor)
            if neighbor_string is None:
                # This point has a liberty. Can't be self capture.
                return False
            elif neighbor_string.color == player:
                # Gather for later analysis.
                friendly_strings.append(neighbor_string)
            else:
                if neighbor_string.num_liberties == 1:
                    # This move is real capture, not a self capture.
                    return False
        if all( neighbor.num_liberties == 1 for neighbor in friendly_strings):
            return True
        return False

    #---------------------------------------
    def will_capture( self, player, point):
        for neighbor in self.neighbor_table[point]:
            neighbor_string = self._grid.get( neighbor)
            if neighbor_string is None:
                continue
            elif neighbor_string.color == player:
                continue
            else:
                if neighbor_string.num_liberties == 1:
                    # This move would capture.
                    return True
        return False

    #------------------------------
    def is_on_grid( self, point):
        return 1 <= point.row <= self.num_rows and \
            1 <= point.col <= self.num_cols

    #----------------------
    def get( self, point):
        """Return the content of a point on the board.

        Returns None if the point is empty, or a Player if there is a
        stone on that point.
        """
        string = self._grid.get( point)
        if string is None:
            return None
        return string.color

    #--------------------------------
    def get_go_string( self, point):
        """Return the entire string of stones at a point.

        Returns None if the point is empty, or a GoString if there is
        a stone on that point.
        """
        string = self._grid.get( point)
        if string is None:
            return None
        return string

    # Return the strings in an array
    #----------------------------------
    def get_go_strings(self):
        strings = list(set(self._grid.values()))
        strings = [s for s in strings if s]
        return strings

    #--------------------------
    def __eq__( self, other):
        return isinstance( other, Board) and \
            self.num_rows == other.num_rows and \
            self.num_cols == other.num_cols and \
            self._hash() == other._hash()

    #-------------------------------------
    def __deepcopy__( self, memodict={}):
        copied = Board( self.num_rows, self.num_cols)
        # Can do a shallow copy b/c the dictionary maps tuples
        # (immutable) to GoStrings (also immutable)
        copied._grid = copy.copy( self._grid)
        copied._hash = self._hash
        return copied

# tag::return_zobrist[]
    #--------------------------
    def zobrist_hash( self):
        return self._hash
# end::return_zobrist[]

# A play, a pass, or a resign. Color *not* included.
#=======================================================
class Move():

    #----------------------------------------------------------------
    def __init__( self, point=None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass
        self.is_resign = is_resign

    @classmethod
    #----------------------
    def play( cls, point):
        return Move( point=point)

    @classmethod
    #-------------------
    def pass_turn( cls):
        return Move( is_pass=True)

    @classmethod
    #----------------
    def resign( cls):
        return Move( is_resign=True)

    #-------------------
    def __str__( self):
        if self.is_pass:
            return 'pass'
        if self.is_resign:
            return 'resign'
        return '(r %d, c %d)' % (self.point.row, self.point.col)

    # So Move can be dict key or in set
    #------------------------------------
    def __hash__( self):
        return hash((
            self.is_play,
            self.is_pass,
            self.is_resign,
            self.point))

    #----------------------------
    def  __eq__( self, other):
        return (
            self.is_play,
            self.is_pass,
            self.is_resign,
            self.point) == (
            other.is_play,
            other.is_pass,
            other.is_resign,
            other.point)

# A board, whose turn, most recent move, and a pointer to zobrist hash of prev board.
#=====================================================================================
class GameState():

    #--------------------------------------------------------
    def __init__( self, board, next_player, previous, move):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous
        if previous is None:
            self.previous_states = frozenset()
        else:
            self.previous_states = frozenset(
                previous.previous_states |
                {(previous.next_player, previous.board.zobrist_hash())})
        self.last_move = move

    # Make a new game state by applying a move
    #---------------------------------------------
    def apply_move( self, move):
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_player.other, self, move)

    #-------------------------------------
    def __deepcopy__( self, memodict={}):
        print( 'Game state deepcopy()')
        copied = self.apply_move( Move.pass_turn())
        copied.next_player = self.next_player
        return copied

    @classmethod
    # Start a new game, no handicap
    #--------------------------------
    def new_game( cls, board_size):
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)

    # Suicide rule
    #----------------------------------------------
    def is_move_self_capture( self, player, move):
        if not move.is_play:
            return False
        return self.board.is_self_capture(player, move.point)

    @property
    #---------------------
    def situation( self):
        return (self.next_player, self.board)

    # Ko rule
    #-----------------------------------------------
    def does_move_violate_ko( self, player, move):
        if not move.is_play:
            return False
        if not self.board.will_capture(player, move.point):
            return False
        next_board = copy.deepcopy( self.board)
        next_board.place_stone( player, move.point)
        next_situation = (player.other, next_board.zobrist_hash())
        return next_situation in self.previous_states

    # Any move on an empty intersection which isn't suicide or violates ko
    #-----------------------------------------------------------------------
    def is_valid_move( self, move):
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return (
            self.board.get( move.point) is None and
            not self.is_move_self_capture( self.next_player, move) and
            not self.does_move_violate_ko( self.next_player, move))

    # Two passes end a game
    #------------------------
    def is_over( self):
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass

    # A bot chooses from one of these
    #----------------------------------
    def legal_moves( self):
        if self.is_over():
            return []
        moves = []
        for row in range( 1, self.board.num_rows + 1):
            for col in range( 1, self.board.num_cols + 1):
                move = Move.play( Point(row, col))
                if self.is_valid_move( move):
                    moves.append( move)
        # These two moves are always legal.
        moves.append( Move.pass_turn())
        moves.append( Move.resign())

        return moves

    #-------------------
    def winner( self):
        if not self.is_over():
            return None
        if self.last_move.is_resign:
            return self.next_player
        game_result = scoring.compute_game_result( self)
        return game_result.winner
