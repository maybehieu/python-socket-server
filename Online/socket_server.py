import socket
import multiprocessing
from threading import Thread, Lock
from game import chessGame, to_uci
import time

# set hostname (public IP can be found with 'what's my IP website')
HOST = ''           # server's local IP
PORT1 = 5555        
PORT0 = 5556
ACTIVE_CONN = 0

# declare variables
global BOARD_FEN
global GAME_STATE
global BOARD_FEN_MUTEX

global PLAYER1_MOVE
global PLAYER0_MOVE

# game properties
PLAYER1_MOVE =  [None, None, 'Played']      # (uci_move, time_taken, state - played, await)
PLAYER0_MOVE =  [None, None, 'Played']      # (uci_move, time_taken, state - played, await)
BOARD_FEN =     ['', 1, 'Updated']          # (fen_str, player_id, state - updated, await)
BOARD_FEN_MUTEX = Lock()
CURRENT_ID = 1
GAME_STATE = True


def connection_handler_thread(server_socket=socket.socket().bind((HOST, PORT0)), id=0):
    # get and set global variables
    global ACTIVE_CONN
    global BOARD_FEN
    global GAME_STATE
    global BOARD_FEN_MUTEX

    global PLAYER1_MOVE
    global PLAYER0_MOVE
    global CURRENT_ID
    
    # connect to client
    con, addr = server_socket.accept()  # accept a new connection
    print('Received connection from ' + str(addr))

    ACTIVE_CONN += 1

    # get average time delay between comms
    time_buffer = 0
    for ite in range(5):
        data = 'buffering'
        t_0 = time.time()
        con.send(data.encode())
        data = con.recv(2048).decode()
        time_buffer += time.time() - t_0
    time_buffer /= 5
    print(f'Setting {str(time_buffer)}ms as time buffer for client at address: {str(addr)}, playerId:{id}')

    # main process
    t0 = 0
    while True:
        try:
            # print(1)
            # kill client process if game have ended
            if not GAME_STATE:
                con.send('Quit'.encode())
                print('Shutting down client connection...')
                break

            # testing
            # print(BOARD_FEN[0])
            
            #  check for mutex usage
            BOARD_FEN_MUTEX.acquire()
            # print(f'Getting board_fen at id {id}: {BOARD_FEN}', end='\n')
            # game logic handler
            if id == 0:
                # print('2_0')
                if PLAYER0_MOVE[2] == 'Played' and BOARD_FEN[1] == 0 and BOARD_FEN[0] != '' and BOARD_FEN[2] == 'Await':
                    # print('sending data ' + BOARD_FEN[0])
                    t0 = time.time()
                    # push board-fen to client
                    con.send(BOARD_FEN[0].encode())         # sending board-fen to client
                    # print('sent!')
                    # get return result
                    data = con.recv(8192).decode()          # this is the uci move
                    print(f'Received move {data} from connected user ({str(addr)}): {str(data)}')
                    t1 = time.time() - t0 - time_buffer     # make up cost for delay between comms
                    # print('recv!')
                    # convert to Move object
                    PLAYER0_MOVE = [to_uci(data), t1, 'Await']
                    BOARD_FEN[2] = 'Updated'
                # print('3_0')

            elif id == 1:
                # print('2_1')
                if PLAYER1_MOVE[2] == 'Played' and BOARD_FEN[1] == 1 and BOARD_FEN[0] != '' and BOARD_FEN[2] == 'Await':
                    # print('sending data ' + BOARD_FEN[0])
                    t0 = time.time()
                    # push board-fen to client
                    con.send(BOARD_FEN[0].encode())         # sending board-fen to client
                    # print('sent')
                    # get return result
                    data = con.recv(8192).decode()          # this is the uci move
                    print(f'Received move {data} from connected user ({str(addr)}): {str(data)}')
                    t1 = time.time() - t0 - time_buffer     # make up cost for delay between comms
                    # print('recv')
                    # convert to Move object
                    PLAYER1_MOVE = [to_uci(data), t1, 'Await']
                    BOARD_FEN[2] = 'Updated'
                # print('3_1')
            
            # release the mutex
            BOARD_FEN_MUTEX.release()

            if not data:
                print('Closing connection...')
                break
        except:
            print('Unexpected connection closed! Closing connection...')
            break
    
    con.close()

def server():
    # initialize variables
    global CURRENT_ID
    global PLAYER1_MOVE
    global PLAYER0_MOVE
    global GAME_STATE
    global BOARD_FEN
    CURRENT_ID = 1
    PLAYER1_MOVE = [None, None, 'Played']
    PLAYER0_MOVE = [None, None, 'Played']
    GAME_STATE = True
    BOARD_FEN = ['', 1, 'Await']


    # bind the socket to current 'server' with port
    server_socket1 = socket.socket()
    server_socket1.bind((HOST, PORT1))
    print('Bind socket for player 1 successful! Awaiting connection...')

    # set max number of clients can connect to server
    num_of_con = 1
    server_socket1.listen(num_of_con)

    # bind the socket to current 'server' with port
    server_socket0 = socket.socket()
    server_socket0.bind((HOST, PORT0))
    print('Bind socket for player 0 successful! Awaiting connection...')

    # set max number of clients can connect to server
    num_of_con = 1
    server_socket0.listen(num_of_con)
    
    # starting n-threads with connection_handler
    # thread1 = multiprocessing.Process(target=connection_handler_thread, args=(server_socket1, 1,))
    # thread2 = multiprocessing.Process(target=connection_handler_thread, args=(server_socket0, 0,))
    thread1 = Thread(target=connection_handler_thread, args=(server_socket1, 1,))
    thread2 = Thread(target=connection_handler_thread, args=(server_socket0, 0,))

    thread1.start()
    thread2.start()

    # await 2 players
    while True:
        if ACTIVE_CONN == 2:
            print('All players have connected! Initializing game...')
            break
    
    # init game
    game_handler = chessGame()

    # await keyboard signal to start game
    while True:
        inp = input('Press enter to start game...')
        break

    game_handler.startGame()
    result = []

    while GAME_STATE:
        # accquire board fen
        BOARD_FEN_MUTEX.acquire()
        BOARD_FEN = [game_handler.getFen(), CURRENT_ID, 'Await']
        # release board fen mutex
        BOARD_FEN_MUTEX.release()
        print(BOARD_FEN)

        while True:
            if BOARD_FEN[2] == 'Updated': break

            if CURRENT_ID == 1:     # white turn
                if PLAYER1_MOVE[2] == 'Await':
                    # print(PLAYER1_MOVE[0], PLAYER1_MOVE[1])
                    result = game_handler.updateBoard(PLAYER1_MOVE[0], PLAYER1_MOVE[1])
                    PLAYER1_MOVE[2] = 'Played'
                    CURRENT_ID = 0
                    BOARD_FEN[2] = 'Updated'
                    break

            elif CURRENT_ID == 0:   # black turn
                if PLAYER0_MOVE[2] == 'Await':
                    # print(PLAYER0_MOVE[0], PLAYER0_MOVE[1])
                    result = game_handler.updateBoard(PLAYER0_MOVE[0], PLAYER0_MOVE[1])
                    PLAYER0_MOVE[2] = 'Played'
                    CURRENT_ID = 1
                    BOARD_FEN[2] = 'Updated'
                    break

        # print('returned result: ' + str(result))
        # game ends
        if len(result) > 1:
            # FORMAT: [winner side, move_num, whitePoint, blackPoint]
            winner = 'White' if result[0] else 'Black'
            move_num = result[1]
            wPoint = result[2]
            bPoint = result[3]
            print(f'Game end! {winner} wins, {str(move_num)} moves taken, white\'s side point: {str(wPoint)}, black\'s side point: {str(bPoint)}')
            GAME_STATE = False
            break

    # wait for 5 seconds before shutting down everything
    time.sleep(5)
    game_handler.shutdown()

    # # force quit socket thread
    # thread1.terminate()
    # thread2.terminate()

    thread1.join()
    thread2.join()

    print('Finished! Ending program...')

# start socket
server()