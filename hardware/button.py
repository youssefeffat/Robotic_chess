from core.interfaces import IButtonModule
import time
from hardware.robotic_arm import *  # Adjusted the import path to match the project structure

class Button(IButtonModule):
    def __init__(self, robotic_arm : RoboticArm):
        """
        Initialize the Button class.
        This is a placeholder implementation.
        The actual implementation will involve hardware interaction.
        """
        self.is_initialized = False  
        self.robotic_arm = robotic_arm

    def initialize_button(self) -> bool:
        """
        Initialize the button module.
        This function sets up the button.
        The state of the button is transferred by the electronic board.
        Outputs:
            - Returns True if initialization succeeds, False otherwise.
        """
        print("Initializing button module...")
        try:
            self.robotic_arm.com.sendEmpty(ID_CMD_BOUTTON_STATE) # Request button state
            self.is_initialized = True
            print("Button module initialized successfully.")
            return True
        except Exception as e:
            print(f"Error initializing button module: {e}")
            self.is_initialized = False
            return False

    def human_turn_finished(self) -> bool:
        """
        Blocking function.
        Block until the human player's turn is finished or a hardware issue is detected.
        Expected Behavior:
            - Wait for the button to be pressed.
            - If the button is pressed, finish execution.
            - If a hardware issue is detected, inform the user and return False.

        Outputs:
            - Returns True if the button was pressed successfully, False if a hardware issue occurs.
        """
        print("Waiting for the button press...")
        
        timeout = 300  
        start_time = time.time()
        start_time_request = time.time()
        while not self.button_pressed():
            # Check for timeout
            if time.time() - start_time > timeout:
                print("Error: Button press not detected within the timeout period. Possible hardware issue.")
                return False
            elif (time.time() - start_time_request) > 1:
                start_time_request = time.time()
                self.robotic_arm.com.sendEmpty(ID_CMD_BOUTTON_STATE) # Request button state
        print("Button pressed! Human turn finished.")
        return True

    def button_pressed(self) -> bool:
        """
        Check if the button is pressed.
        This function should be implemented based on the hardware setup.

        Outputs:
            - Returns True if the button is pressed, False otherwise.
        """
        ## LOGIC
        ##
        ##                       CODE
        ##
        return self.robotic_arm.button_state

    def shutdown(self) -> None:
        """
        Clean up resources and shut down the button module.
        """
        if self.is_initialized:
            ## LOGIC
           ##
           ##                       CODE
           ##
            print("Shutting down button module...")
            self.is_initialized = False
