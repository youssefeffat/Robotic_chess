from core.interfaces import IButtonModule
import time
from hardware.robotic_arm import RoboticArm
from pynput import keyboard


class Button(IButtonModule):
    def __init__(self, robotic_arm: RoboticArm):
        """
        Initialize the Button class.
        This is a placeholder implementation using the spacebar as a stand-in for a hardware button.
        """
        self.robotic_arm = robotic_arm
        self.is_initialized = False
        self._button_pressed = False
        self._listener = None

    def initialize_button(self) -> bool:
        """
        Initialize the button module.
        Sets up a keyboard listener that flips a flag when space is pressed.
        Returns:
            True if initialization succeeds, False otherwise.
        """
        try:
            # Start keyboard listener
            self._listener = keyboard.Listener(on_press=self._on_key_press)
            self._listener.start()
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize button module: {e}")
            return False

    def _on_key_press(self, key):
        try:
            if key == keyboard.Key.space:
                self._button_pressed = True
        except AttributeError:
            pass

    def human_turn_finished(self) -> bool:
        """
        Blocking call that waits until the 'button' (spacebar) is pressed,
        or until a hardware issue is detected (simulated as listener failure),
        or until a 5-minute timeout expires.

        Returns:
            True if the button was pressed before timeout; False otherwise.
        """
        if not self.is_initialized:
            raise RuntimeError("Button module not initialized. Call initialize_button() first.")

        print("Waiting for the button press (5-minute timeout)...")
        start_time = time.time()
        timeout = 5 * 60  # 5 minutes in seconds

        while True:
            # Check for timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                print("Timeout waiting for button press.")
                return False

            if not self._listener.is_alive():
                print("Hardware issue detected: listener stopped unexpectedly.")
                return False

            if self.button_pressed():
                print("Button pressed! Human turn finished.")
                self._button_pressed = False
                return True

            time.sleep(0.1)

    def button_pressed(self) -> bool:
        """
        Non-blocking check whether the button has been pressed.

        Returns:
            True if pressed since last check, False otherwise.
        """
        return self._button_pressed

    def shutdown(self) -> None:
        """
        Clean up resources and shut down the button module.
        """
        if self._listener:
            self._listener.stop()
            self._listener = None
        self.is_initialized = False
        print("Button module shut down.")
