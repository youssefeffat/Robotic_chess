from core.interfaces import ICameraModule
import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from core.interfaces import ICameraModule

class Camera(ICameraModule):
    def __init__(self):
        """
        Initialize the Camera class.
        This is a placeholder implementation.
        The actual implementation will involve image processing and FEN generation.
        """
        self.test = None  

    def initialize_camera(self) -> None:
        """
        Initialize the camera module.
        This function sets up the camera hardware and prepares it for capturing images.
        """
        print("Camera module initialized.")

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
        return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def shutdown(self) -> None:
        """
        Close the camera connection.
        This function should be called during cleanup to release resources.
        """
        print("Camera closed.")

class ChessboardDetector:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(image_path)
        self.board_size = 400
        self.square_size = self.board_size // 8
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
        self.magenta_upper = np.array([170, 255, 255])

        self.cyan_lower = np.array([75, 150, 50])
        self.cyan_upper = np.array([100, 255, 255])

    def order_points(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def preprocess_image(self):
        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
        cv2.imshow("Step 1: Grayscale & Blurring", self.blurred_image)
        cv2.waitKey(1000)
        return self.blurred_image

    def detect_edges(self):
        self.edges = cv2.Canny(self.blurred_image, 50, 150)
        cv2.imshow("Step 2: Edge Detection", self.edges)
        cv2.waitKey(1000)
        return self.edges

    def find_chessboard_contour(self):
        contours, _ = cv2.findContours(self.edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if cv2.contourArea(c) > 70000]  # Ignore small contours.
        if not contours:
            print("No contours found.")
            return None
        largest_contour = max(contours, key=cv2.contourArea)
        epsilon = 0.02 * cv2.arcLength(largest_contour, True)
        approx = cv2.approxPolyDP(largest_contour, epsilon, True)
        contour_image = self.image.copy()
        cv2.drawContours(contour_image, [largest_contour], -1, (0, 255, 0), 3)
        cv2.imshow("Step 3: Chessboard Contour", contour_image)
        cv2.waitKey(1000)
        if len(approx) == 4:
            return approx
        else:
            print("Could not detect exactly 4 corners of the chessboard.")
            return None

    def apply_perspective_transform(self, approx):
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
        cv2.imshow("Step 4: Perspective Transform", self.warped_image)
        cv2.waitKey(1000)
        self.draw_grid()
        return self.warped_image

    def draw_grid(self):
        grid_image = self.warped_image.copy()
        for row in range(8):
            for col in range(8):
                x, y = col * self.square_size, row * self.square_size
                cv2.rectangle(grid_image, (x, y), (x + self.square_size, y + self.square_size), (255, 0, 0), 1)
                square_name = f"{chr(97 + col)}{8 - row}"
                cv2.putText(grid_image, square_name, (x + 5, y + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow("Step 5: Chessboard Grid", grid_image)
        cv2.waitKey(1000)

    def detect_pieces(self):
        threshold = 0
        for row in range(8):
            for col in range(8):
                x, y = col * self.square_size, row * self.square_size
                square = self.warped_image[y:y + self.square_size, x:x + self.square_size]
                hsv_square = cv2.cvtColor(square, cv2.COLOR_BGR2HSV)

                red_mask = cv2.inRange(hsv_square, self.red_lower, self.red_upper)
                blue_mask = cv2.inRange(hsv_square, self.blue_lower, self.blue_upper)
                green_mask = cv2.inRange(hsv_square, self.green_lower, self.green_upper)
                orange_mask = cv2.inRange(hsv_square, self.orange_lower, self.orange_upper)
                magenta_mask = cv2.inRange(hsv_square, self.magenta_lower, self.magenta_upper)
                cyan_mask = cv2.inRange(hsv_square, self.cyan_lower, self.cyan_upper)

                total_pixels = self.square_size * self.square_size
                red_coverage = np.sum(red_mask) / total_pixels
                blue_coverage = np.sum(blue_mask) / total_pixels
                green_coverage = np.sum(green_mask) / total_pixels
                orange_coverage = np.sum(orange_mask) / total_pixels
                magenta_coverage = np.sum(magenta_mask) / total_pixels
                cyan_coverage = np.sum(cyan_mask) / total_pixels

                flag_red = red_coverage > threshold
                flag_blue = blue_coverage > threshold
                flag_green = green_coverage > threshold
                flag_orange = orange_coverage > threshold
                flag_magenta = magenta_coverage > threshold
                flag_cyan = cyan_coverage > threshold

                if flag_blue and flag_magenta:
                    self.piece_detected[row][col] = "R"  # White R: Blue + Magenta
                elif flag_red and flag_orange:
                    self.piece_detected[row][col] = "Q"  # White Q: Red + Orange
                elif flag_red and flag_cyan:
                    self.piece_detected[row][col] = "K"  # White K: Red + Cyan
                elif flag_orange and flag_green:
                    self.piece_detected[row][col] = "N"  # White N: Orange + Green
                elif flag_blue:
                    self.piece_detected[row][col] = "P"  # White P: Blue only
                elif flag_green:
                    self.piece_detected[row][col] = "B"  # White B: Green only

                elif flag_blue and flag_red:
                    self.piece_detected[row][col] = "q"  # Black q: Blue + Red
                elif flag_green and flag_red:
                    self.piece_detected[row][col] = "n"  # Black n: Green + Red
                elif flag_green and flag_magenta:
                    self.piece_detected[row][col] = "b"  # Black b: Green + Magenta
                elif flag_orange and flag_magenta:
                    self.piece_detected[row][col] = "k"  # Black k: Orange + Magenta
                elif flag_red:
                    self.piece_detected[row][col] = "p"  # Black p: Red only
                # Otherwise, remains empty (".")
        return self.piece_detected

    def generate_fen(self):
        fen_rows = []
        for row in self.piece_detected:
            empty_count = 0
            fen_row = ""
            for cell in row:
                if cell == ".":
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
            print("Error: Chessboard contour not detected. Cannot generate FEN.")
            return ""
        self.apply_perspective_transform(approx)
        self.detect_pieces()
        fen_string = self.generate_fen()
        if not show_intermediate:
            cv2.destroyAllWindows()
        return fen_string

    @classmethod
    def generate_fen_from_frame(cls, frame, show_intermediate=True):

        detector = cls.__new__(cls)
        detector.image = frame
        detector.board_size = 400
        detector.square_size = detector.board_size // 8
        detector.piece_detected = [["." for _ in range(8)] for _ in range(8)]
        # Set HSV color ranges.
        detector.red_lower = np.array([0, 150, 50])
        detector.red_upper = np.array([10, 255, 255])
        detector.blue_lower = np.array([100, 150, 50])
        detector.blue_upper = np.array([120, 255, 255])
        detector.green_lower = np.array([40, 150, 50])
        detector.green_upper = np.array([75, 255, 255])
        detector.orange_lower = np.array([10, 150, 50])
        detector.orange_upper = np.array([20, 255, 255])
        detector.magenta_lower = np.array([140, 150, 50])
        detector.magenta_upper = np.array([170, 255, 255])
        detector.cyan_lower = np.array([75, 150, 50])
        detector.cyan_upper = np.array([100, 255, 255])
        return detector.process_image(show_intermediate)


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit()

    print("Press 'space' to capture a photo and process it, or 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        cv2.imshow("Chessboard Capture", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord(' '):
            print("Capturing and processing frame...")
            fen_string = ChessboardDetector.generate_fen_from_frame(frame, show_intermediate=False)
            print("Detected FEN:", fen_string)

    cap.release()
    cv2.destroyAllWindows()
