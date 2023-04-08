from chessboard import display
import chess
import time

def to_uci(uci=''):
    return chess.Move.from_uci(uci).uci()

class chessGame:
    def __init__(self) -> None:
        self.board = chess.Board()
        self.game_board = display.start()
        self.max_move = 100
        self.Playing = False
        self.turn = True    # true: white, false: black
        self.time_buffer = 0.01   # seconds

    def startGame(self):
        self.Playing = True
        # init gameboard
        display.start(self.board.fen())

    def displayGame(self):
        display.update(self.board.fen(), self.game_board)
    
    def shutdown(self):
        display.terminate()
    
    # calculate score for game's result
    def staticAnalysis(self, color):
        score = 0
        for (piece, value) in [(chess.PAWN, 1), 
                            (chess.BISHOP, 4), 
                            (chess.KING, 0), 
                            (chess.QUEEN, 10), 
                            (chess.KNIGHT, 5),
                            (chess.ROOK, 3)]:
            score += len(self.board.pieces(piece, color)) * value
        return score

    def getFen(self):
        # print('getting board fen: ' + self.board.fen())
        return self.board.fen()
    
    def updateBoard(self, uci, time_taken):
        # handle move time-out
        t0 = time_taken - self.time_buffer if time_taken - self.time_buffer > 0 else 0    # minus the cost of networking delay
        if t0 > 3000:
            wEval = 9999 if self.turn else -9999
            bEval = -1 * wEval
            self.Playing = False
            return [not self.turn, len(self.board.move_stack),  wEval, bEval]
        
        # make move
        self.board.push_uci(uci)
        self.displayGame()

        # log move to console
        name = 'White' if self.turn == True else 'Black'
        print(f'Move {len(self.board.move_stack)}, {name} plays "{uci}", time taken: {str(t0)}ms')

        # check for checkmate
        if self.board.is_checkmate():
            wEval = 9999 if self.turn else -9999
            bEval = -1 * wEval
            self.Playing = False
            return [self.turn, len(self.board.move_stack), wEval, bEval]
        
        # check for number of moves
        if len(self.board.move_stack) >= self.max_move:
            wEval = self.staticAnalysis(True)
            bEval = self.staticAnalysis(False)
            self.Playing = False
            return [True if wEval > bEval else False, len(self.board.move_stack), wEval, bEval]
        
        # update game-state
        self.turn = not self.turn
        return [True]
        