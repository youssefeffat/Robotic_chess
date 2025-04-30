from core.interfaces import ICameraModule
import cv2 
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from core.interfaces import ICameraModule
import threading
# export PYTHONPATH=/home/anas/Documents/Python/Robotic_chess:$PYTHONPATH 

#Installation à faire :
#     pip install opencv-python

class Camera(ICameraModule):
    def __init__(self):
        """
        Initialize the Camera class.
        This is a placeholder implementation.
        The actual implementation will involve image processing and FEN generation.
        """
        self.chs = ChessboardDetector()
        
        self.camera = None #= cv2.VideoCapture(0)
        
        self.calibrate_camera = False
        
        self.fen_string = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
        self.buffer_fen_string = ["", ""]
        self.buffer_fen_string_index = 0
        
        
        self.thread = None
        self.running = False
        
    def _startThread(self):
        """
        Start the camera module in a separate thread.
        """
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
    
    def _loop(self):
        """
        Main loop for the camera module that is in a thread.
        This function captures images from the camera and processes them to generate FEN strings.
        """
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                print("Error: Could not read frame.")

            cv2.imshow("Chessboard Capture", frame)
            
            if self.calibrate_camera:
                self.chs.calibration_from_image(frame, False)# We calibrate the color of the pieces
                #Then with the same frame we detect the pieces
                # We should obtain the basic FEN string, if not it indicates that the camera is not well positioned
                self.chs.image = frame
                self.chs.preprocess_image(False)
                self.chs.detect_edges(False)
                approx = self.chs.find_chessboard_contour(False)
                if approx is not None:
                    warped_image = self.chs.apply_perspective_transform(approx, False)
                    self.chs.draw_grid(warped_image, True)
                    self.chs.detect_pieces(True)
                    fen_string = self.chs.generate_fen()
                    if(fen_string != "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"):
                        print("Calibration failed. Please adjust the camera position : ", fen_string)
                    elif fen_string == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR":
                        print("Calibration successful. Camera is well positioned.")
                        self.calibrate_camera = False
                    # self.fen_string = fen_string
                self.fen_string = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR" # Basic FEN for calibration
            else:
                # fen_string = chs.generate_fen_from_frame(frame)
                self.chs.image = frame
                self.chs.preprocess_image(True)
                self.chs.detect_edges()
                approx = self.chs.find_chessboard_contour(True)
                if approx is not None:
                    warped_image = self.chs.apply_perspective_transform(approx, False)
                    self.chs.draw_grid(warped_image, True)
                    self.chs.detect_pieces()
                    
                    self.buffer_fen_string[self.buffer_fen_string_index] = self.chs.generate_fen()
                    self.buffer_fen_string_index = (self.buffer_fen_string_index + 1) % 2
                    
                    if self.buffer_fen_string[0] == self.buffer_fen_string[1]:# filtre pour eviter les faux positifs
                        self.fen_string = self.buffer_fen_string[0]
                        self.buffer_fen_string_index = (self.buffer_fen_string_index + 1) % 2
                    elif self.buffer_fen_string_index == 0:
                        self.buffer_fen_string[0] = self.buffer_fen_string[1]
                        self.buffer_fen_string_index = (self.buffer_fen_string_index + 1) % 2
                    # print("Detected FEN:", fen_string)
                
            cv2.waitKey(1)

    def initialize_camera(self) -> None:
        """
        Initialize the camera module.
        This function sets up the camera hardware and prepares it for capturing images.
        """
        print("Camera module initialized.")
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print("Error: Could not open camera.")
            else:
                print("Camera opened successfully.")
        if self.thread is None:
            self._startThread()

    def get_fen(self) -> str:
        """
        Capture the current board state and return it as a FEN string.
        Expected Behavior:
            - Capture an image of the chessboard.
            - Process the image to detect piece positions.
            - Generate and return the FEN string.

        Outputs:
            - A valid FEN string representing the current chessboard state.
        """
        print("Capturing chessboard state...")

        # Placeholder: Simulate FEN generation
        # return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
        
        return self.fen_string

    def shutdown(self) -> None:
        """
        Close the camera connection.
        This function should be called during cleanup to release resources.
        """
        print("Camera closed.")
        self.running = False
        if self.thread is not None:
            self.thread.join()
        if self.camera is not None:
            self.camera.release()
        cv2.destroyAllWindows()
    
    def set_calibration_mode(self, mode: bool) -> None:
        """
        Set the camera module to calibration mode.
        In this mode, the camera captures images for calibration purposes.
        Must be activated then deactivated.
        Parameters:
            mode (bool): True to set calibration mode, False to set normal mode.
        """
        self.calibrate_camera = mode
        if mode:
            print("Camera module set to calibration mode.")
        else:
            print("Camera module set to normal mode.")

class ChessboardDetector():
    def __init__(self, image_path = None):
        self.image_path = image_path
        self.image = cv2.imread(image_path) if image_path else None
        self.board_size = 400
        self.square_size = self.board_size // 8
        self.countours_size = 0 # Taille du contour autour du carré 
        
        self.zoom_margin = 10
        
        self.piece_detected = [["." for _ in range(8)] for _ in range(8)]
        self.red_lower = np.array([0, 150, 50])
        self.red_upper = np.array([10, 255, 255])

        self.blue_lower = np.array([100, 150, 50])
        self.blue_upper = np.array([120, 255, 255])

        self.green_lower = np.array([40, 150, 50])
        self.green_upper = np.array([75, 255, 255])

        self.orange_lower = np.array([10, 150, 50])
        self.orange_upper = np.array([20, 255, 255])

        self.magenta_lower = np.array([140, 150, 50])
        self.cyan_upper = np.array([100, 255, 255])
        self.magenta_upper = np.array([170, 255, 255])

        self.cyan_lower = np.array([75, 150, 50])
        self.cyan_upper = np.array([100, 255, 255])
        
        self.hsv_ranges = None

    def order_points(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def preprocess_image(self, affiche=False):
        if self.image is None:
            raise ValueError("Error: Image not loaded. Please check the image path or input frame.")
        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
        if affiche:
            cv2.imshow("Step 1: Grayscale & Blurring", self.blurred_image)
            # cv2.waitKey(1)
        return self.blurred_image

    def detect_edges(self, affiche=False):
        self.edges = cv2.Canny(self.blurred_image, 50, 150)
        if affiche:
            cv2.imshow("Step 2: Edge Detection", self.edges)
            # cv2.waitKey(1)
        return self.edges

    def find_chessboard_contour(self, affiche=False):
        """
        Find the contour of the chessboard in the image, even if the shape is not perfectly square
        or if the edges are not continuous.

        Returns:
            approx (np.ndarray): Approximated polygon of the chessboard contour with 4 corners.
        """
        # Find all contours in the edge-detected image
        contours, _ = cv2.findContours(self.edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by area to ignore small or irrelevant ones
        min_area = 50000  # Lowered to account for imperfect shapes
        filtered_contours = [c for c in contours if cv2.contourArea(c) > min_area]

        if not filtered_contours:
            # print("No contours found with sufficient area.")
            return None

        # Select the largest contour by area
        largest_contour = max(filtered_contours, key=cv2.contourArea)

        # Approximate the contour to a polygon
        epsilon = 0.05 * cv2.arcLength(largest_contour, True)  # Increased epsilon for less strict approximation
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)

        # Visualize the detected contour
        contour_image = self.image.copy()
        cv2.drawContours(contour_image, [largest_contour], -1, (0, 255, 0), 3)
        if(affiche):
            cv2.imshow("Step 3: Chessboard Contour", contour_image)
            # cv2.waitKey(1)

        # Ensure the approximated polygon has exactly 4 corners
        if len(approx) == 4:
            # print("Chessboard contour detected successfully.")
            return approx
        else:
            # print(f"Detected contour does not have 4 corners (found {len(approx)} corners).")
            # print("Attempting to fit a quadrilateral...")

            # Fit a quadrilateral if the contour does not have exactly 4 corners
            rect = cv2.minAreaRect(largest_contour)
            box = cv2.boxPoints(rect)
            box = np.int0(box).reshape((4, 2))

            # Convert box to the format compatible with order_points
            approx = np.array([[point] for point in box], dtype="float32")

            # Visualize the fitted quadrilateral
            cv2.drawContours(contour_image, [box], -1, (0, 0, 255), 2)
            if affiche:
                cv2.imshow("Step 3: Fitted Quadrilateral", contour_image)
                # cv2.waitKey(1)

            return approx

    def apply_perspective_transform(self, approx, affiche=False):
        if approx is None or len(approx) != 4:
            raise ValueError("Error: Invalid contour approximation. Expected 4 points.")

        # Extract points and ensure they are in the correct format
    
        pts = np.array([p[0] for p in approx], dtype="float32")
        ordered_pts = self.order_points(pts)
        dst_pts = np.array([
            [0, 0],  # top-left (a8)
            [self.board_size, 0],  # top-right (h8)
            [self.board_size, self.board_size],  # bottom-right (h1)
            [0, self.board_size]  # bottom-left (a1)
        ], dtype="float32")
        matrix = cv2.getPerspectiveTransform(ordered_pts, dst_pts)
        self.warped_image = cv2.warpPerspective(self.image, matrix, (self.board_size, self.board_size))
        if affiche:
            cv2.imshow("Step 4: Perspective Transform", self.warped_image)
            # cv2.waitKey(1)
        self.draw_grid(self.warped_image, affiche)
        return self.warped_image

    def draw_grid(self, image, affiche=False):
        grid_image = image.copy()
        for row in range(8):
            for col in range(8):
                x, y = col * self.square_size + self.countours_size, row * self.square_size + self.countours_size
                cv2.rectangle(grid_image, (x, y), (x + self.square_size, y + self.square_size), (255, 0, 0), 1)
                square_name = f"{chr(97 + col)}{8 - row}"
                cv2.putText(grid_image, square_name, (x + 5, y + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        if affiche:
            cv2.imshow("Step 5: Chessboard Grid", grid_image)
            # cv2.waitKey(1)

    # def detect_pieces(self):
    #     threshold = 0
    #     for row in range(8):
    #         for col in range(8):
    #             x, y = col * self.square_size + self.countours_size, row * self.square_size + self.countours_size
    #             square = self.warped_image[y:y + self.square_size, x:x + self.square_size]
    #             hsv_square = cv2.cvtColor(square, cv2.COLOR_BGR2HSV)

    #             red_mask = cv2.inRange(hsv_square, self.red_lower, self.red_upper)
    #             blue_mask = cv2.inRange(hsv_square, self.blue_lower, self.blue_upper)
    #             green_mask = cv2.inRange(hsv_square, self.green_lower, self.green_upper)
    #             orange_mask = cv2.inRange(hsv_square, self.orange_lower, self.orange_upper)
    #             magenta_mask = cv2.inRange(hsv_square, self.magenta_lower, self.magenta_upper)
    #             cyan_mask = cv2.inRange(hsv_square, self.cyan_lower, self.cyan_upper)

    #             total_pixels = self.square_size * self.square_size
    #             red_coverage = np.sum(red_mask) / total_pixels
    #             blue_coverage = np.sum(blue_mask) / total_pixels
    #             green_coverage = np.sum(green_mask) / total_pixels
    #             orange_coverage = np.sum(orange_mask) / total_pixels
    #             magenta_coverage = np.sum(magenta_mask) / total_pixels
    #             cyan_coverage = np.sum(cyan_mask) / total_pixels

    #             flag_red = red_coverage > threshold
    #             flag_blue = blue_coverage > threshold
    #             flag_green = green_coverage > threshold
    #             flag_orange = orange_coverage > threshold
    #             flag_magenta = magenta_coverage > threshold
    #             flag_cyan = cyan_coverage > threshold

    #             if flag_blue and flag_magenta:
    #                 self.piece_detected[row][col] = "R"  # White R: Blue + Magenta
    #             elif flag_red and flag_orange:
    #                 self.piece_detected[row][col] = "Q"  # White Q: Red + Orange
    #             elif flag_red and flag_cyan:
    #                 self.piece_detected[row][col] = "K"  # White K: Red + Cyan
    #             elif flag_orange and flag_green:
    #                 self.piece_detected[row][col] = "N"  # White N: Orange + Green
    #             elif flag_blue:
    #                 self.piece_detected[row][col] = "P"  # White P: Blue only
    #             elif flag_green:
    #                 self.piece_detected[row][col] = "B"  # White B: Green only

    #             elif flag_blue and flag_red:
    #                 self.piece_detected[row][col] = "q"  # Black q: Blue + Red
    #             elif flag_green and flag_red:
    #                 self.piece_detected[row][col] = "n"  # Black n: Green + Red
    #             elif flag_green and flag_magenta:
    #                 self.piece_detected[row][col] = "b"  # Black b: Green + Magenta
    #             elif flag_orange and flag_magenta:
    #                 self.piece_detected[row][col] = "k"  # Black k: Orange + Magenta
    #             elif flag_red:
    #                 self.piece_detected[row][col] = "p"  # Black p: Red only
    #             # Otherwise, remains empty (".")
    #     return self.piece_detected
    def calibration(self, image_path):
        """
        Calibrate the HSV color ranges for each type of chess piece and empty squares (black and white)
        based on a reference image. The reference image must have the chess pieces in their initial positions.

        Parameters:
            image_path (str): Path to the calibration image.

        Returns:
            dict: A dictionary containing the HSV ranges for each piece type and empty squares.
        """
        # print("Calibrating HSV ranges...")
        # Load the image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Error: Image not loaded. Please check the image path.")
        hsv_ranges = self.calibration_from_image(image)
        return hsv_ranges
    
    def calibration_from_image(self, image, affiche=False):
        """
        Calibrate the HSV color ranges for each type of chess piece and empty squares (black and white)
        based on a reference image. The reference image must have the chess pieces in their initial positions.

        Parameters:
            image (str): image from cv2.imread.

        Returns:
            dict: A dictionary containing the HSV ranges for each piece type and empty squares.
        """
        # print("Calibrating HSV ranges...")
        # Load the image
        
        if image is None:
            raise ValueError("Error: Image not loaded. Please check the image path.")

        # Define the initial positions of the pieces on the chessboard
        initial_positions = {
            "r": [(0, 0), (7, 0)],  # Black Rooks
            "n": [(1, 0), (6, 0)],  # Black Knights
            "b": [(2, 0), (5, 0)],  # Black Bishops
            "q": [(3, 0)],          # Black Queen
            "k": [(4, 0)],          # Black King
            "p": [(i, 1) for i in range(8)],  # Black Pawns
            "R": [(0, 7), (7, 7)],  # White Rooks
            "N": [(1, 7), (6, 7)],  # White Knights
            "B": [(2, 7), (5, 7)],  # White Bishops
            "Q": [(3, 7)],          # White Queen
            "K": [(4, 7)],          # White King
            "P": [(i, 6) for i in range(8)],  # White Pawns
            "black_empty": [(i, j) for i in range(8) for j in range(2, 4) if (i + j) % 2 == 0],  # Empty black squares
            "white_empty": [(i, j) for i in range(8) for j in range(2, 4) if (i + j) % 2 == 1]   # Empty white squares
        }

        # Perspective transform to align the chessboard
        self.image = image
        self.preprocess_image(affiche)
        self.detect_edges(affiche)
        approx = self.find_chessboard_contour(affiche)
        if approx is None:
            # raise ValueError("Error: Chessboard contour not detected.")
            return None
        warped_image = self.apply_perspective_transform(approx, affiche)

        # Convert the warped image to HSV
        hsv_image = cv2.cvtColor(warped_image, cv2.COLOR_BGR2HSV)

        # Dictionary to store HSV ranges for each piece type and empty squares
        hsv_ranges = {}

        # Measure the HSV values for each piece type and empty squares
        for piece, positions in initial_positions.items():
            hsv_values = []
            for col, row in positions:
                x = col * self.square_size + self.countours_size
                y = row * self.square_size + self.countours_size
                center_x = x + self.square_size // 2
                center_y = y + self.square_size // 2
                zoom_margin = self.square_size // self.zoom_margin  # Adjust the zoom margin to focus more on the center
                center_square = hsv_image[center_y - zoom_margin:center_y + zoom_margin, center_x - zoom_margin:center_x + zoom_margin]
                
                # # Smooth the colors by applying a Gaussian blur
                # smoothed_square = cv2.GaussianBlur(center_square, (5, 5), 0)
                
                # # Find the most dominant color by creating a histogram
                # hist = cv2.calcHist([smoothed_square], [0, 1, 2], None, [180, 256, 256], [0, 180, 0, 256, 0, 256])
                # dominant_color = np.unravel_index(np.argmax(hist), hist.shape)
                
                # # Replace the square with the dominant color
                # smoothed_square[:, :] = dominant_color
                
                # cv2.imshow(f"Calibration Square {piece} at {chr(97 + col)}{8 - row}", smoothed_square)
                
                # hsv_mean = cv2.mean(smoothed_square)[:3]  # Get the mean HSV values
                hsv_mean = cv2.mean(center_square)[:3]  # Get the mean HSV values
                hsv_values.append(hsv_mean)
                # print(f"Calibrating {piece}... {positions} hsv_values : {hsv_values}")

            # Calculate the HSV range for the piece or empty square
            h_values = [hsv[0] for hsv in hsv_values]
            s_values = [hsv[1] for hsv in hsv_values]
            v_values = [hsv[2] for hsv in hsv_values]

            h_min, h_max = max(0, min(h_values) - 10), min(180, max(h_values) + 10)
            s_min, s_max = max(0, min(s_values) - 40), min(255, max(s_values) + 40)
            v_min, v_max = max(0, min(v_values) - 40), min(255, max(v_values) + 40)

            hsv_ranges[piece] = {
                "lower": np.array([h_min, s_min, v_min]),
                "upper": np.array([h_max, s_max, v_max])
            }

        # Print the calibrated HSV ranges
        # for piece, ranges in hsv_ranges.items():
        #     print(f"{piece}: Lower={ranges['lower']}, Upper={ranges['upper']}")

        self.hsv_ranges = hsv_ranges
        # print("Calibration complete.")
        self.draw_grid(warped_image, affiche)
        return hsv_ranges
    
    def detect_pieces(self, affiche=False):
        if not self.hsv_ranges:
            print("Error: HSV ranges not calibrated. Please run the calibration method first.")
            return None

        for row in range(8):
            for col in range(8):
                # x, y = col * self.square_size + self.countours_size, row * self.square_size + self.countours_size
                # square = self.warped_image[y:y + self.square_size, x:x + self.square_size]
                x = col * self.square_size + self.countours_size
                y = row * self.square_size + self.countours_size
                center_x = x + self.square_size // 2
                center_y = y + self.square_size // 2
                zoom_margin = self.square_size // self.zoom_margin  # Adjust the zoom margin to focus more on the center
                square = self.warped_image[center_y - zoom_margin:center_y + zoom_margin, center_x - zoom_margin:center_x + zoom_margin]
                hsv_square = cv2.cvtColor(square, cv2.COLOR_BGR2HSV)

                best_piece = None
                best_coverage = 0

                for piece, ranges in self.hsv_ranges.items():
                    mask = cv2.inRange(hsv_square, ranges["lower"], ranges["upper"])
                    coverage = np.sum(mask) / (self.square_size * self.square_size)
                    if coverage > best_coverage and coverage > 0.5:  # Adjust threshold as needed
                        best_piece = piece
                        best_coverage = coverage

                if best_piece:
                    self.piece_detected[row][col] = best_piece
                    if affiche:
                        # print(f"Detected {best_piece} at {chr(97 + col)}{8 - row} with coverage: {best_coverage:.2f}")
                        cv2.imshow(f"Square {chr(97 + col)}{8 - row}", hsv_square)
                        # cv2.waitKey(1)
        
        # if affiche:
        #     cv2.destroyAllWindows()
        return self.piece_detected

    def generate_fen(self):
        fen_rows = []
        for row in self.piece_detected:
            empty_count = 0
            fen_row = ""
            for cell in row:
                if cell == "white_empty" or cell == "black_empty" or cell == ".":
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    fen_row += cell
            if empty_count > 0:
                fen_row += str(empty_count)
            fen_rows.append(fen_row)
        return "/".join(fen_rows)

    def process_image(self, show_intermediate=True):
        self.preprocess_image()
        self.detect_edges()
        approx = self.find_chessboard_contour()
        if approx is None:
            # print("Error: Chessboard contour not detected. Cannot generate FEN.")
            return ""
        self.apply_perspective_transform(approx)
        self.detect_pieces()
        fen_string = self.generate_fen()
        if not show_intermediate:
            cv2.destroyAllWindows()
        return fen_string

    # @classmethod
    def generate_fen_from_frame(self, frame, show_intermediate=True):
        # detector = cls.__new__(cls)
        self.image = frame
        return self.process_image(show_intermediate)

def testCamera():
    class GetCharacter():
        def __init__(self):
            self.key = None
            self.flag = False
        
        def loop(self):
            while True:
                self.key = input("Press 'c' to capture a photo and process it, or 'q' to quit: ")
                self.flag = True

        def startThread(self):
            threading.Thread(target=self.loop).start()
        
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()

    # print("Press 'space' to capture a photo and process it, or 'q' to quit.")

    char = GetCharacter()
    char.startThread()

    chs = ChessboardDetector()

    from api.stockfish_api import StockfishEngine
    stockfish = StockfishEngine()
    stockfish.stockfish.set_fen_position(stockfish.stockfish.get_fen_position())
    print(stockfish.stockfish.get_board_visual())
    print(stockfish.stockfish.get_fen_position())
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        cv2.imshow("Chessboard Capture", frame)
        # cv2.waitKey(1)

        if char.flag:
            char.flag = False
            if char.key == ('q'):
                break
            elif char.key == ('m'):
                chs.calibration_from_image(frame, True)
            elif char.key == (' '):
                print("Capturing and processing frame...")
                # fen_string = chs.generate_fen_from_frame(frame)
                chs.image = frame
                chs.preprocess_image(True)
                chs.detect_edges(True)
                approx = chs.find_chessboard_contour(True)
                if approx is not None:
                    chs.apply_perspective_transform(approx, True)
                    chs.detect_pieces()
                    fen_string = chs.generate_fen()
                    print("Detected FEN:", fen_string)
                    # stockfish = StockfishEngine()
                    # stockfish.stockfish.set_fen_position(fen_string)
                    # print(stockfish.stockfish.get_fen_position())
                    # print(stockfish.stockfish.get_board_visual())
                    
            else:
                print(char.key)

    cap.release()
    cv2.destroyAllWindows()

def testImage(image_path, image_path2=None):
    if image_path2 is None:
        image_path2 = image_path
    detector = ChessboardDetector(image_path2)
    detector.countours_size = 0
    # cv2.imshow("Image 1", cv2.imread(image_path))
    # cv2.imshow("Image 2", cv2.imread(image_path2))
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    
    # hsv_image = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2HSV)
    # cv2.imshow("HSV Image", hsv_image)
    
    detector.calibration(image_path)
    
    detector.image = cv2.imread(image_path2)
    detector.preprocess_image(True)
    detector.detect_edges()
    approx = detector.find_chessboard_contour(True)
    if approx is not None:
        detector.apply_perspective_transform(approx, True)
        detector.detect_pieces(True)
        fen_string = detector.generate_fen()
        print("Detected FEN:", fen_string)
        from api.stockfish_api import StockfishEngine
        stockfish = StockfishEngine()
        stockfish.stockfish.set_fen_position(fen_string)
        print(stockfish.stockfish.get_board_visual())
        print(stockfish.stockfish.get_fen_position())
        
        cv2.imshow("Final Processed Chessboard", detector.warped_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Chessboard contour not detected.")

def testMainClass():
    class GetCharacter():
        def __init__(self):
            self.key = None
            self.flag = False
        
        def loop(self):
            while True:
                self.key = input("Press 'i' to initialize the camera, 'c' to set calibration mode, 'v' to set normal mode, 'f' to get FEN, or 'q' to quit: ")
                self.flag = True

        def startThread(self):
            threading.Thread(target=self.loop).start()
            
    camera = Camera()
    # camera.initialize_camera()
    # camera.set_calibration_mode(True)
    # camera.get_fen()
    # camera.set_calibration_mode(False)
    # camera.get_fen()
    # camera.shutdown()
    char = GetCharacter()
    char.startThread()
    
    while True:
        if char.flag:
            char.flag = False
            if char.key == ('i'):
                camera.initialize_camera()
            elif char.key == ('c'):
                print("Camera is now in calibration mode")
                camera.set_calibration_mode(True)
            elif char.key == ('v'):
                print("Camera is now in normal mode")
                camera.set_calibration_mode(False)
            # elif char.key == ('f'):
            #     fen_string = camera.get_fen()  
            #     print("Detected FEN:", fen_string)
            elif char.key == ('q'):
                camera.shutdown()
                break
            fen_string = camera.get_fen()  
            print("Detected FEN:", fen_string)


if __name__ == "__main__":
    # testImage("/home/anas/Documents/Python/Robotic_chess/hardware/images/image2.png", "/home/anas/Documents/Python/Robotic_chess/hardware/images/image3.png")
    # testCamera()
    testMainClass()
