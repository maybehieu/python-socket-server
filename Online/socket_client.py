import socket, random, chess, time

# server connection properties
HOST = ''              # ask the host for their public IP
PORT1 = 5555           # socket server port number (must matched server's ports)
PORT0 = 5556

#############################

"""
SUMMARY: chess-player class

This section is only a DEMO player, change to your own implementation of Player

Require:    a function that receives a FEN str (represents current chess.Board)
            -> return (an uci move)
"""

class DemoPlayer:
    def __init__(self) -> None:
        self.board = chess.Board()
    def random_player(self, board_fen):
        self.board.set_fen(board_fen)
        move = random.choice(list(self.board.legal_moves))
        return move

# init chess player
player = DemoPlayer()

##############################

def client_program(host=HOST, port=PORT1):
    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server
    print('connected!')

    # time buffering calculation with socket server
    for ite in range(5):
        data = client_socket.recv(2048).decode()
        client_socket.send(data.encode())
        ite += 1
    print('Calculating time buffering completed! Main process starting...')

    # main process
    while True:
        try:
            t0 = time.time()
            board_fen = client_socket.recv(8192).decode()
            try:
                if board_fen == '' or board_fen == None:
                    continue
                print(f'Got fen {board_fen} from server')
            except:
                print('error at receiving data')
            if board_fen == 'Quit':
                break
            uci = player.random_player(board_fen)
            try:
                client_socket.send(str(uci).encode())
                print(f'Sent move {uci} to server, time taken: {str(time.time() - t0)} ms')
            except:
                print('error sending data to server')
        except:
            print('Got unexpected error, closing connection...')
            client_socket.close()
            break
    
    client_socket.close()  # close the connection
    print('Good bye!')

if __name__ == '__main__':
    client_program(HOST, PORT1)         # use this function if you are white player
    # client_program(HOST, PORT0)         # use this function if you are black player