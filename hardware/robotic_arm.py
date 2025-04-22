# Ensure the parent directory of 'core' is in the PYTHONPATH
from core.interfaces import IRoboticArmModule #Si ça ne marche pas, il faut changer le chemin, par exemple
# export PYTHONPATH=/home/anas/Documents/Python/Robotic_chess:$PYTHONPATH 

import threading  # Import the threading module
from hardware.serial_communication import *

class RoboticArm(IRoboticArmModule):
    def __init__(self, selected_port = "COM5"):
        """
        Initialize the RoboticArm class.
        This is a placeholder implementation.
        The actual implementation will involve controlling the robotic arm hardware.
        """
        self.is_initialized = False 

        self.selected_port = selected_port
        self.com = SerialCommunication()

        self.loop_thread = None  # Thread for the loop function
        self.running = False     # Flag to control the loop execution
        
        self.current_pos = Position(0,0,0)
        
        self.chessboard_moves = ChessboardMoves()
        self.state_chessboard_manager = 0
        self.last_move = "" #le dernier move fait par exemple "e2e4"

    def _start_serial(self, selected_port):
        if selected_port:
            try:
                self.com = SerialCommunication(selected_port, SERIAL_BAUDRATE)
                self.com.start()
                print("Starting serial self.com ", selected_port)
            except serial.SerialException as e:
                print("Serial Error", f"Failed to open port {selected_port}: {e}")
                
    def _start_loop(self):
        """
        Start the loop function in a separate thread.
        """
        if self.loop_thread is None or not self.loop_thread.is_alive():
            self.running = True
            print("Loop thread started.")
            self.loop_thread = threading.Thread(target=self.loop, daemon=True)
            self.loop_thread.start()
            
    def _stop_loop(self):
        """
        Stop the loop function.
        """
        self.running = False
        if self.loop_thread is not None:
            self.loop_thread.join()
            print("Loop thread stopped.")
            
    def initialize_robot(self) -> None:
        """
        Initialize the robotic arm module.
        This function sets up the robotic arm hardware (e.g., motors, servos).
        """
        self._start_serial(self.selected_port) # Start the serial communication
        print("Robotic arm initialized.")
        self._start_loop()  # Start the loop thread
        self.is_initialized = True

    def execute_move(self, move: str) -> None:
        """
        Execute the given move on the physical chessboard.
        Expected Behavior:
            - Move the robotic arm to perform the specified move.
            - Ensure the move is executed accurately.

        Inputs:
            - `move`: A UCI move string (e.g., "e2e4").

        Outputs:
            - None (executes the move physically).
        """
        if not self.is_initialized:
            raise RuntimeError("Robotic arm is not initialized. Call initialize_robot() first.")

        self.chessboard_moves.addMoves(move)
        
        print(f"Executing move: {move}")

    def shutdown(self) -> None:
        """
        Shut down the robotic arm and clean up resources.
        """
        self._stop_loop()  # Stop the loop thread
        print("Robotic arm shut down.")
        self.is_initialized = False
        
    def _rxManage(self):
        # print("RxManage")
        self.com.FIFO_occupation = self.com.FIFO_Ecriture - self.com.FIFO_lecture
        if(self.com.FIFO_occupation<0):
            self.com.FIFO_occupation = self.com.FIFO_occupation + SIZE_FIFO
        if(self.com.FIFO_max_occupation < self.com.FIFO_occupation):
            self.com.FIFO_max_occupation = self.com.FIFO_occupation
        if(self.com.FIFO_occupation == 0):
            return
        
        id = self.com.rxMsg[self.com.FIFO_lecture].id
        print("\nReceived message from id: ", idComEnText.get(id, "ID inconnu"))
        
        match id:
            case id if id == ID_ACK_GENERAL:
                print("Ack reçu")
            case id if id == ID_REPEAT_REQUEST:
                print("Repeat request")
            case id if id == ID_ACK_CMD_MOVE:
                print("Move acknowledgment received")
            case id if id == ID_ACK_SERVO_GRAB:
                print("Servo grab acknowledgment received")
            case id if id == ID_ACK_SERVO_RELEASE:
                print("Servo release acknowledgment received")
            case id if id == ID_ACK_HOMING:
                print("Homing acknowledgment received")
            case id if id == ID_ACK_SEND_CURRENT_POSITION:
                print("Current position received")
                # On recoit en mm, donc on convertit en metres
                self.current_pos.x = float(self.com.rxMsg[self.com.FIFO_lecture].data[0] + (self.com.rxMsg[self.com.FIFO_lecture].data[1] << 8)) / 1000.0
                self.current_pos.y = float(self.com.rxMsg[self.com.FIFO_lecture].data[2] + (self.com.rxMsg[self.com.FIFO_lecture].data[3] << 8)) / 1000.0
                self.current_pos.z = float(self.com.rxMsg[self.com.FIFO_lecture].data[4] + (self.com.rxMsg[self.com.FIFO_lecture].data[5] << 8)) / 1000.0
                print(self.current_pos)
            case id if id == ID_CMD_BOUTTON_STATE:
                print("Button state command received")
            case _:
                print(f"Received message from an unknown ID")
        self.com.FIFO_lecture = (self.com.FIFO_lecture + 1) % SIZE_FIFO
    
    def chessBoardMoveManager(self):
        """
        Manage the moves on the chessboard.
        This function will handle the moves.
        """
        
        if(self.chessboard_moves.thereIsNewMoveToDo()):
            moves = self.chessboard_moves.getNextMove()
            if self.last_move == moves:
                print("Move already done")
                return
            self.last_move = moves
            
            start_pos, end_pos = self.chessboard_moves.convertMovesToPositions(moves)
            print(f"Move from {start_pos} to {end_pos}")
            
            self.com.sendMove(start_pos)#On va au dessus de la piece
            
            start_pos.z = HAUTEUR_BRAS
            self.com.sendMove(start_pos)#On descend à la piece
            
            self.com.sendGrabPiece(True)#On attrape la piece
            
            start_pos.z = 0
            self.com.sendMove(start_pos)#On remonte
            
            self.com.sendMove(end_pos)#On va à la case
            
            end_pos.z = HAUTEUR_BRAS
            self.com.sendMove(end_pos)#On descend à la case
            
            self.com.sendGrabPiece(False)#On relache la piece
            
            end_pos.z = 0
            self.com.sendMove(end_pos)#On remonte
            
            #Est ce qu'on fait autre chose aprés? Comme aller appuyer sur un bouton? A voir !!!!!!!!!!!!!!!!!!!!
    
    def loop(self):
        """
        Main loop for the robotic arm module.
        This function is called in a thread to continuously check for incoming messages and process them.
        """
        last_time_pos = 0
        print("Starting loop... self.running = ", self.running)
        while self.running:
            self._rxManage()
            
            self.chessBoardMoveManager()
            
            #On actualise la position courante toutes les secondes
            if time.time() - last_time_pos > 1:
                last_time_pos = time.time()
                # Send a request for the current position
                # self.com.sendEmpty(ID_SEND_CURRENT_POSITION)
                
        print("Exiting loop... self.running = ", self.running)

if __name__ == "__main__":    
    robotic_arm = RoboticArm(afficherPortDisponible())
    # robotic_arm.chessboard_moves.addMoves("a1b2")
    robotic_arm.initialize_robot()
    # Simulate some operations
    # robotic_arm.execute_movee from Position(x: 0.0, y: 0.0, z: 0.0) to Position(x: 0.05, y: 0.05, z: 0.0)("e2e4")
    
    # Shutdown the robotic arm
    # robotic_arm.shutdown()
    while 1:
        key = input("")
        if key == 'a':
            print("Key 'a' pressed")
            robotic_arm.execute_move("e2e4")
        elif key == 'b':
            print("Key 'a' pressed")
            robotic_arm.execute_move("e4a1")
        elif key == 'c':
            start_pos, end_pos = robotic_arm.chessboard_moves.convertMovesToPositions("e2e4")
            print(f"Move from {start_pos} to {end_pos}")
            
            robotic_arm.com.sendMove(start_pos)
        elif key == 'p':
            print("Key 'p' pressed")
            robotic_arm.com.sendEmpty(ID_SEND_CURRENT_POSITION)