
import struct

SERIAL_BAUDRATE = 921600

# Listes de tous les id :
ID_ACK_GENERAL                 = 0xC0 # Ack pour tous le reste
ID_ACK_UNKNOW                  = 0xC1 # Ack pour les messages inconnus
ID_REPEAT_REQUEST              = 0xD0

ID_CMD_MOVE                    = 0xA0 # On envoit le mouvement x y z à faire en millimetres
ID_ACK_CMD_MOVE                = 0xA1 # On reçoit l'accusé de réception

ID_SERVO_GRAB                  = 0xA2 # On demande de serrer la pince
ID_ACK_SERVO_GRAB              = 0xA3 # On reçoit l'accusé de réception

ID_SERVO_RELEASE               = 0xA4 # On demande de desserrer la pince
ID_ACK_SERVO_RELEASE           = 0xA5 # On reçoit l'accusé de réception

ID_HOMING                      = 0xA6 # On demande de faire le homing
ID_ACK_HOMING                  = 0xA7 # On réçoit l'accusé de réception

ID_SEND_CURRENT_POSITION       = 0xA8 # On demande d'envoyer la position courante
ID_ACK_SEND_CURRENT_POSITION   = 0xA9 # On reçoit la position courante

ID_CMD_BOUTTON_STATE           = 0xB1  # Request button state
ID_ACK_CMD_BOUTTON_STATE       = 0xB2 # On reçoit l'accusé de réception de l'état du bouton

idComEnText = {
    0x00: "",
    0xA0: "ID_CMD_MOVE",
    0xA1: "ID_ACK_CMD_MOVE",
    0xA2: "ID_SERVO_GRAB",
    0xA3: "ID_ACK_SERVO_GRAB",
    0xA4: "ID_SERVO_RELEASE",
    0xA5: "ID_ACK_SERVO_RELEASE",
    0xA6: "ID_HOMING",
    0xA7: "ID_ACK_HOMING",
    0xA8: "ID_SEND_CURRENT_POSITION",
    0xA9: "ID_ACK_SEND_CURRENT_POSITION",
    0xC0: "ID_ACK_GENERAL",
    0xD0: "ID_REPEAT_REQUEST",
    0xB1: "ID_CMD_BOUTTON_STATE",
    0xB2: "ID_ACK_CMD_BOUTTON_STATE",
}

class Message():
    def __init__(self, id=0, length=0, data=None):
        self.id = id
        self.len = length
        self.data = data if data else []
        self.checksum = 0 #Le checksum est un XOR de tous les octect du message (de id, len et data[])
    
    def setData(self, id, length = 0, data = None):
        self.id = id
        self.len = length
        self.data = data if data else []

    def build_packet(self):
        # Calculate checksum
        self.checksum = (self.id ^ self.len) & 0xFF
        for i in range(self.len):
            self.checksum ^= self.data[i]
        length = self.len if(self.len) else 1 #Comme ça meme si on envoit un commande sans data, il faut forcément qu'il y est data0
        # Construct the packet with HEADEAR, ID, length, data, checksum, and FOOTER
        #For example : (FF A0 02 01 02 A1 FF)
        packet_format = f'<B B B {length}s B B'
        packet_data = bytes(self.data)
        return struct.pack(packet_format, 0xFF, self.id, self.len, packet_data, self.checksum, 0xFF)

    def __str__(self):
        return f"[FF][{self.id:02X}][{self.len:02X}]{''.join(f'[{byte:02X}]' for byte in self.data)}[{self.checksum:02X}][FF]"

SIZE_FIFO = 32 #Une FIFO est un buffer, la taille du buffer de reception est de 32

class Position():
    def __init__(self, x = 0, y = 0, z = 0):
        self.x = float(x) #Position en metres
        self.y = float(y) #Position en metres
        self.z = float(z) #Position en metres
    
    def __str__(self):
        return f"Position(x: {self.x}, y: {self.y}, z: {self.z})"

TAILLE_CARREAU = 0.036 #En metres
HAUTEUR_BRAS = 0.13 #En metres, hauteur du bras à laquelle descendre pour prendre une pièce, en z, à mesurer!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

class ChessboardMoves():
    def __init__(self):
        self.moves = ["" for _ in range(SIZE_FIFO)]
        self.cursor_move_write = 0
        self.cursor_move_read = 0
        
        self.posA1 = Position(0.03, 0.025, 0) #Position de A1, utilisé comme référence, à mesurer!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        self.move_finished = False #On va l'utiliser pour savoir

    def addMoves(self, move):
        self.moves[self.cursor_move_write] = move
        self.cursor_move_write = (self.cursor_move_write + 1) % SIZE_FIFO

    def thereIsNewMoveToDo(self):
        if (self.cursor_move_write - self.cursor_move_read):
            return True
        else:
            return False
    
    def waitForMoveToFinish(self):
        while(self.move_finished == False):
            pass
        self.move_finished = False

    def getNextMove(self):
        if(self.thereIsNewMoveToDo() == False):
            return ""
        move = self.moves[self.cursor_move_read]
        self.moves[self.cursor_move_read] = ""
        self.cursor_move_read = (self.cursor_move_read + 1) % SIZE_FIFO
        return move

    def convertMovesToPositions(self, move : str):#On reçoit par exemple "e2e4" et on renvoit la position de e2 et e4
        #On reçoit par exemple "e2e4" et on
        #On renvoit la position de e2 et e4        
        def chessNotationToPosition(notation):
            if len(notation) != 2:
                raise ValueError("Invalid chess notation. Expected format: 'e2'")
            column = notation[0].lower()
            row = notation[1]
            if column < 'a' :#or row < '1' or column > 'h' or row > '8':
                raise ValueError("Invalid chess notation. Out of bounds.")
            x = self.posA1.x + (ord(column) - ord('a')) * TAILLE_CARREAU
            y = self.posA1.y + (int(row) - 1) * TAILLE_CARREAU
            return Position(x, y, 0)
        
        start_pos = chessNotationToPosition(move[:2])
        end_pos = chessNotationToPosition(move[2:])
        return start_pos, end_pos

    def convertPosToChessNotation(self, position: Position):
        # Convert the position to chess notation
        column = chr(int((position.x - self.posA1.x + 0.01) / TAILLE_CARREAU) + ord('a'))
        row = str(int((position.y - self.posA1.y + 0.01) / TAILLE_CARREAU) + 1)
        return f"{column}{row}"

if __name__ == "__main__":
    # Test the ChessboardMoves class
    chessboard_moves = ChessboardMoves()
    chessboard_moves.addMoves("a1a2")
    chessboard_moves.addMoves("a2e2")
    chessboard_moves.addMoves("e2e4")
    chessboard_moves.addMoves("e4f3")
    chessboard_moves.addMoves("f3b8")
    chessboard_moves.addMoves("b8a1")
    
    while chessboard_moves.thereIsNewMoveToDo():
        move = chessboard_moves.getNextMove()
        start_pos, end_pos = chessboard_moves.convertMovesToPositions(move)
        print(f"Move: {move}, Start Position: {start_pos}, End Position: {end_pos}")
        print(f"Chess Notation: {chessboard_moves.convertPositionToChessNotation(start_pos)}, {chessboard_moves.convertPositionToChessNotation(end_pos)}")