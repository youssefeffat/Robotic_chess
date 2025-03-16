import serial
import struct
import time


class SerialCommunication:
    SERIAL_BAUDRATE = 9600

    ID_CMD_MOUVEMENT = 0xA0  # Send a UCI move command
    ID_CMD_BOUTTON_STATE = 0xB0  # Request button state
    ID_ACK_GENERALE = 0xC0  # General acknowledgment

    HEADER = 0xFF
    FOOTER = 0xFF

    def __init__(self, port, baudrate=SERIAL_BAUDRATE, timeout=1):
        self.serial = serial.Serial(port, baudrate, timeout=timeout)
        self.running = True

    def send_message(self, message_id, data=[]):
        length = len(data)
        checksum = message_id ^ length
        for byte in data:
            checksum ^= byte

        packet = struct.pack(f'<B B B {length}s B B',
                             self.HEADER, message_id, length, bytes(data), checksum, self.FOOTER)

        self.serial.write(packet)
        print(f"Sent Message Packet {packet}, ID {hex(message_id)}, Data: {data}")

    def send_uci_move(self, move_str):
        move_bytes = move_str.encode('utf-8')
        self.send_message(self.ID_CMD_MOUVEMENT, list(move_bytes))

        response = self.wait_for_response(self.ID_ACK_GENERALE, expected_data=b"Done")
        if response:
            print("Move executed successfully.")
        else:
            print("Move execution failed or no response received.")

    def read_button_state(self):
        self.send_message(self.ID_CMD_BOUTTON_STATE, [0x00])

        response = self.wait_for_response(self.ID_CMD_BOUTTON_STATE)
        if response:
            button_state = response[0]
            is_pressed = bool(button_state)
            print(f"Button State: {'Pressed' if is_pressed else 'Not Pressed'}")
            return is_pressed
        else:
            print("No valid button state response.")
            return False

    def wait_for_response(self, expected_id, expected_data=None, timeout=3):
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.receive_message()
            if response and response["id"] == expected_id:
                if expected_data is None or response["data"] == expected_data:
                    return response["data"]
        return None

    def receive_message(self):
        response = self.serial.read(6)
        if len(response) < 6:
            return None

        if response[0] == self.HEADER and response[-1] == self.FOOTER:
            message_id = response[1]
            length = response[2]
            data = response[3:3 + length]
            checksum = response[3 + length]

            computed_checksum = message_id ^ length
            for byte in data:
                computed_checksum ^= byte

            if computed_checksum == checksum:
                return {"id": message_id, "data": data}
            else:
                print("Checksum mismatch in received message.")

        return None

    def close(self):
        self.running = False
        self.serial.close()


if __name__ == "__main__":
    serial_comm = SerialCommunication("COM13")
    serial_comm.send_uci_move("e2e4")
    time.sleep(1)
    button_pressed = serial_comm.read_button_state()
    print(f"Button Pressed: {button_pressed}")
    serial_comm.close()
