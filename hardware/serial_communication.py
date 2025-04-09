from PySide6.QtCore import QThread, Signal, Slot, QTimer
import serial
import serial.tools.list_ports
import time
import struct
from donnees import *


class SerialCommunication(QThread):
    # message_received = Signal(bytes)
    def __init__(self, port = None, baudrate = None):
        super().__init__()
        
        self.rxMsg = [Message() for _ in range(SIZE_FIFO)]
        self.FIFO_Ecriture = 0
        self.ecritureEnCours = False #Flag pour faire savoir qu'on a lancé une ecriture
        self.problemeEnEcriture = False #Flag pour dire que le serial.write n'a pas fonctionné
        
        self.FIFO_lecture = 0
        self.FIFO_max_occupation = 0
        self.FIFO_occupation = 0
        
        if port is not None:
            self.port = port
            self.baudrate = baudrate
            self.serial = serial.Serial(port, baudrate)
            self.running = True
        else:
            self.port = None
            self.baudrate = None
            self.serial = None
            self.running = False

        self.stateRx = 0
        self.compteurData = 0

        self.lastTime = time.time()

        self.msgError = ""

        self.FIFO_lecture           = 0 #Pour le  buffer
        self.FIFO_occupation        = 0
        self.FIFO_max_occupation    = 0

    def run(self):#Thread qui gére la connexion
        while self.running:
            if self.serial.in_waiting > 0:
                byte = self.serial.read(1)
                # print(byte)
                # self.message_received.emit(byte)
                self.RxReceive(byte)
                # self.serial.write(b'\xFF')
                # sample_message = Message(id=1, length=3, data=[0x01, 0x02, 0x03])
                # packet = sample_message.build_packet()
                # self.serial.write(packet)
            if((time.time()-self.lastTime) > 3):#Pour annuler l'envoi du message toutes les 3 secondes si jamais il y a un probléme
                self.lastTime = time.time()
                if(self.ecritureEnCours):
                    self.ecritureEnCours = False
                    self.serial.cancel_write() 
                    self.problemeEnEcriture = True
            

    def close(self):
        if self.running:
            self.running = False
            self.serial.close()

    # @Slot(bytes)
    def RxReceive(self, message):#Fonction callback appellé a chaque arrivé d'un octet
        byte = int.from_bytes(message, byteorder='big')
        # print(f"Received byte: Ox{byte:02X})")
        # print(f"Received raw message: {message}")
        match self.stateRx:
            case 0:
                if byte == 0xff:
                    self.msgError = ""
                    self.msgError += " Header"
                    #print("Header")
                    self.stateRx = 1
                    self.rxMsg[self.FIFO_Ecriture].checksum = 0
            case 1:
                #print("ID")
                self.msgError += " ID" + str(byte.to_bytes(1, byteorder='big'))
                self.rxMsg[self.FIFO_Ecriture].id = int(byte)
                self.rxMsg[self.FIFO_Ecriture].checksum ^= byte
                self.stateRx = 2
            case 2:
                #print("len")
                self.msgError += " len" + str(byte.to_bytes(1, byteorder='big'))
                self.rxMsg[self.FIFO_Ecriture].len = int(byte)
                self.rxMsg[self.FIFO_Ecriture].checksum ^= byte
                self.rxMsg[self.FIFO_Ecriture].data = []
                self.compteurData = 0
                self.stateRx = 3
            case 3:
                #print("data n°", self.compteurData)
                self.msgError += " dt[" + str(self.compteurData) + "]= " + f"Ox{byte:02X}."
                self.rxMsg[self.FIFO_Ecriture].data.append(int(byte)) 
                self.rxMsg[self.FIFO_Ecriture].checksum ^= byte
                self.compteurData += 1
                if(self.compteurData >= self.rxMsg[self.FIFO_Ecriture].len):
                    self.compteurData = 0
                    self.stateRx = 4
            case 4:
                #print("checksum %d", byte)
                self.msgError += " checksum" + f"Ox{byte:02X}"
                if(self.rxMsg[self.FIFO_Ecriture].checksum == int(byte)):
                    self.stateRx = 5
                else :
                    self.stateRx = 0
                    print(self.msgError)
                    print(" ERROR Checksum mismatch msg n°"+ str(self.FIFO_Ecriture) +", "+ str(self.rxMsg[self.FIFO_Ecriture].checksum) + " != " + str(byte))
            case 5:
                #print("Header Fin")
                if byte == 0xFF:
                    self.msgError += " Header Fin"
                    print("Received new msg n°"+ str(self.FIFO_Ecriture) + f" from id : Ox{self.rxMsg[self.FIFO_Ecriture].id:02X}")
                    self.FIFO_Ecriture = (self.FIFO_Ecriture + 1)%SIZE_FIFO
                #print(self.msgError)
                self.stateRx = 0


    def RxManage(self):#Fonction à mettre à la suite de ton programme et à  compléter pour faire tes actions. Tu peux la mettre dans une autre classe stv
        # print("RxManage")
        self.FIFO_occupation = self.FIFO_Ecriture - self.FIFO_lecture
        if(self.FIFO_occupation<0):
            self.FIFO_occupation = self.FIFO_occupation + SIZE_FIFO
        if(self.FIFO_max_occupation < self.FIFO_occupation):
            self.FIFO_max_occupation = self.FIFO_occupation
        if(self.FIFO_occupation == 0):
            return

        match self.rxMsg[self.FIFO_lecture].id:
            case 0xA0:
                pass
            case 0xB0:
                print("Ack reçu")
            case _:
                print(f"Received message from an unknown ID")
        self.FIFO_lecture = (self.FIFO_lecture + 1) % SIZE_FIFO
    
    def sendMsg(self, msg = Message()):
        # sample_message = Message(id=1, length=3, data=[0x01, 0x02, 0x03])
        packet = msg.build_packet()
        print(msg)
        if self.running:
            try:
                self.ecritureEnCours = True
                self.serial.write(packet) #Fonction bloquante, qui se debloque toutes les 3 secondes si l'envoi à echouer
                self.ecritureEnCours = False
                if(self.problemeEnEcriture):
                    self.problemeEnEcriture = False
                    print(f"")
                    print(f"-----------Problème rencontré lors de l'envoi de données")
                    print(f"-----------Deconnexion du PORT COM...")
                    self.close()
                    print(f"-----------Essayer de vous reconnectez svp")
            except (serial.SerialException) as e:
                error_message = f"Failed to send data: {e.__class__.__name__}: {e}"
                print(error_message)
                print(f"")
                print(f"-----------{error_message}")
                self.close()
                print(f"-----------Essayer de vous reconnectez svp")
        else:
            print(f"")
            print(f"-----------Aucun PORT COM de connecté! Veuillez-vous connectez.")

    def sendEmpty(self, id):
        sample_message = Message(id, length=0, data=[0])
        self.sendMsg(sample_message)

    def sendByte(self, id, byte):
        sample_message = Message(id, length=1, data=[byte & 0xFF])
        self.sendMsg(sample_message)
    
    def sendTwoUint16(self, id, var1, var2):
        data = [
            var1 & 0xFF, (var1 >> 8) & 0xFF,
            var2 & 0xFF, (var2 >> 8) & 0xFF
        ]
        sample_message = Message(id, length=4, data=data)
        self.sendMsg(sample_message)

    def sendThreeUint16(self, id, var1, var2, var3):
        data = [
            var1 & 0xFF, (var1 >> 8) & 0xFF,
            var2 & 0xFF, (var2 >> 8) & 0xFF,
            var3 & 0xFF, (var3 >> 8) & 0xFF
        ]
        sample_message = Message(id, length=6, data=data)
        self.sendMsg(sample_message)
    
    def sendData(self, id, len = 0, dt = [0]):
        sample_message = Message(id, length=len, data=dt)
        self.sendMsg(sample_message)
    
    def sendUciMove(self, move_str):#Fonction non gérée coté hardware
        move_bytes = list(move_str.encode('utf-8'))
        print(f"Sending UCI move: {move_str} {move_bytes}")
        
        self.sendData(0xFF, move_bytes)

    def sendMove(self, pos : Position):
        # Convert the position to bytes
        x = int(pos.x * 1000) & 0xFFFF
        y = int(pos.y * 1000) & 0xFFFF
        z = int(pos.z * 1000) & 0xFFFF

        # Send the position data
        self.sendThreeUint16(ID_CMD_MOVE, x, y, z)
    
    def sendGrabPiece(self, grab: bool):
        # Convert the grab state to bytes
        if grab:
            self.sendEmpty(ID_SERVO_GRAB)
        else:  
            self.sendEmpty(ID_SERVO_RELEASE)
        

    def __str__(self):
        return f"FIFO_Ecriture: {self.FIFO_Ecriture}, ecritureEnCours: {self.ecritureEnCours}, problemeEnEcriture: {self.problemeEnEcriture}"

#end SerialThread

def afficherPortDisponible():
        print("Afficher Port Disponible")
        ports = serial.tools.list_ports.comports()
        last_port = None
        for port in ports:
            print(port.device)
            last_port = port.device
        return last_port

if __name__ == "__main__":
    port = afficherPortDisponible()
    serial_comm = SerialCommunication(port, SERIAL_BAUDRATE)
    serial_comm.start()
    
    # serial_comm.sendEmpty(ID_SEND_CURRENT_POSITION)
    
    while 1:
        key = input("Press a key: ")
        if key == 'a':
            print("Key 'a' pressed")
            serial_comm.sendEmpty(ID_SEND_CURRENT_POSITION)