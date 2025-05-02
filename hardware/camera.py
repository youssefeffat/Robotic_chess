from core.interfaces import ICameraModule
import cv2 
import numpy as np
from pynput import keyboard
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from core.interfaces import ICameraModule

class Camera:
    def __init__(self,
                 board_size: int = 550,
                 coverage_threshold: float = 0.02,
                 border_cm: float = 2,
                 board_physical_size_cm: float = 40.0,
                 red_threshold: float = None,
                 debug: bool = False):
        self.board_size = board_size
        self.coverage_threshold = coverage_threshold
        self.red_threshold = red_threshold if red_threshold is not None else coverage_threshold * 0.5
        self.debug = debug

        self.border_px = int(round(board_size * border_cm / board_physical_size_cm))
        interior = board_size - 2 * self.border_px
        self.square_size = interior // 8

        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

        self.hsv_ranges = {
            'red':    (np.array([0, 150, 50]),   np.array([10, 255, 255])),
            'red2':   (np.array([170,150,50]),   np.array([180,255,255])),
            'blue':   (np.array([100, 150, 50]), np.array([120, 255, 255])),
            'green':  (np.array([30,  80, 50]),  np.array([90, 255, 255])),
            'orange': (np.array([10, 150, 50]),  np.array([19, 255, 255])),
            'yellow': (np.array([20, 150, 50]),  np.array([30, 255, 255])),
            'violet': (np.array([115, 50, 50]),  np.array([160, 255, 255])),
            'pink':   (np.array([160,  50, 50]), np.array([179, 255, 255])),
        }

        self.base_map = {'violet':'K','pink':'R','yellow':'N','blue':'P','green':'B','orange':'Q'}
        self.dark_map =  {'violet':'k','pink':'r','yellow':'n','blue':'p','green':'b','orange':'q'}

    def _debug_show(self, win, img, wait=300):
        if self.debug:
            cv2.imshow(win, img)
            cv2.waitKey(wait)

    def preprocess(self, image: np.ndarray):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        self._debug_show("Preprocess", blur)
        return blur

    def detect_edges(self, img: np.ndarray):
        edges = cv2.Canny(img, 50, 150)
        self._debug_show("Edges", edges)
        return edges

    def find_board(self, edges: np.ndarray):
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        large = [c for c in contours if cv2.contourArea(c) > (self.board_size**2 * 0.5)]
        if not large:
            raise RuntimeError("No large contour found")
        c = max(large, key=cv2.contourArea)
        eps = 0.02 * cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, eps, True)
        if len(approx) != 4:
            raise RuntimeError("Board contour not quadrilateral")
        pts = np.float32([p[0] for p in approx])
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        rect = np.array([
            pts[np.argmin(s)], pts[np.argmin(diff)],
            pts[np.argmax(s)], pts[np.argmax(diff)]], dtype="float32")
        return rect

    def warp(self, img: np.ndarray, rect: np.ndarray):
        dst = np.array([[0,0],[self.board_size,0],[self.board_size,self.board_size],[0,self.board_size]], dtype="float32")
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (self.board_size, self.board_size))
        self._debug_show("Warped", warped)
        return warped

    def draw_grid(self, img: np.ndarray):
        out = img.copy()
        for r in range(8):
            for c in range(8):
                x = self.border_px + c*self.square_size
                y = self.border_px + r*self.square_size
                cv2.rectangle(out,(x,y),(x+self.square_size,y+self.square_size),(255,0,0),1)
                cv2.putText(out,f"{chr(97+c)}{8-r}",(x+5,y+20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
        self._debug_show("Grid", out)

    def _get_mask(self, square: np.ndarray, color: str):
        hsv = cv2.cvtColor(square, cv2.COLOR_BGR2HSV)
        if color == 'red':
            low1, high1 = self.hsv_ranges['red']
            low2, high2 = self.hsv_ranges['red2']
            m1 = cv2.inRange(hsv, low1, high1)
            m2 = cv2.inRange(hsv, low2, high2)
            mask = cv2.bitwise_or(m1, m2)
        else:
            low, high = self.hsv_ranges[color]
            mask = cv2.inRange(hsv, low, high)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.kernel)
        mask = cv2.dilate(mask, self.kernel, iterations=1)
        return mask

    def detect_pieces(self, img: np.ndarray):
        board = [['.' for _ in range(8)] for _ in range(8)]
        for r in range(8):
            for c in range(8):
                x = self.border_px + c*self.square_size
                y = self.border_px + r*self.square_size
                sq = img[y:y+self.square_size, x:x+self.square_size]
                total = float(self.square_size**2)

                red_mask = self._get_mask(sq, 'red')
                red_flag = (red_mask.sum() > self.red_threshold * total * 255)

                base_color = None
                for color in ['violet','pink','yellow','blue','green','orange']:
                    if self._get_mask(sq, color).sum() > self.coverage_threshold * total * 255:
                        base_color = color
                        break

                if base_color:
                    piece = self.dark_map[base_color] if red_flag else self.base_map[base_color]
                else:
                    piece = 'p' if red_flag else '.'

                board[r][c] = piece
        return board

    def generate_fen(self, board):
        rows = []
        for row in board:
            cnt, fen = 0, ''
            for c in row:
                if c == '.': cnt += 1
                else:
                    if cnt: fen += str(cnt); cnt = 0
                    fen += c
            if cnt: fen += str(cnt)
            rows.append(fen)
        return '/'.join(rows)

    def process(self, image_path=None, frame=None):
        img = cv2.imread(image_path) if image_path else frame.copy()
        pre = self.preprocess(img)
        edges = self.detect_edges(pre)
        rect  = self.find_board(edges)
        warp  = self.warp(img, rect)
        self.draw_grid(warp)
        pieces= self.detect_pieces(warp)
        return self.generate_fen(pieces)

    @classmethod
    def generate_fen_from_frame(cls, frame, show_intermediate=False):
        detector = cls(debug=show_intermediate)
        fen = detector.process(frame=frame)
        if not show_intermediate:
            cv2.destroyAllWindows()
        return fen

    def initialize_camera(self) -> None:
        """
        Initialize the camera module.
        This function sets up the camera hardware and prepares it for capturing images.
        """
        print("Camera module initialized.")

    @classmethod
    def get_fen(cls) -> str:
        """
        Capture the current board state and return it as a FEN string,
        allowing the user to start capture (press 'c'), recalc on error (press 'r'),
        accept (press 'v'), or enter manually (press 'o').
        Uses pynput to listen for keypresses.
        """
        while True:
            # wait for user to press 'c' to start capture
            print("Press 'c' to capture the chessboard state...")
            key_pressed = {"char": None}

            def on_start(key):
                try:
                    c = key.char.lower()
                except AttributeError:
                    return
                if c == 'c':
                    key_pressed["char"] = c
                    return False

            with keyboard.Listener(on_press=on_start) as listener:
                listener.join()

            # start capture
            print("Capturing chessboard state...")
            cap = cv2.VideoCapture(1)
            if not cap.isOpened():
                exit("Error: Could not open camera.")
            ret, frame = cap.read()
            cap.release()

            # run your detector
            detector = cls(debug=True)
            fen = detector.generate_fen_from_frame(frame, show_intermediate=False)

            # show result and prompt
            print(f"Generated FEN: {fen}")
            key_pressed = {"char": None}

            def on_press(key):
                try:
                    c = key.char.lower()
                except AttributeError:
                    return
                if c in ("r", "v", "o"):
                    key_pressed["char"] = c
                    return False

            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()
            choice = key_pressed["char"]

            if choice == "v":
                # User accepts the generated FEN
                cv2.destroyAllWindows()
                return fen

            elif choice == "o":
                # User opts to enter FEN manually
                cv2.destroyAllWindows()
                manual_fen = input("Please enter the FEN string manually: ").strip()
                return manual_fen

            elif choice == "r":
                # Retry capturing
                cv2.destroyAllWindows()
                continue
    def shutdown(self) -> None:
        """
        Close the camera connection.
        This function should be called during cleanup to release resources.
        """
        print("Camera closed.")
if __name__ == '__main__':
    #cap = cv2.VideoCapture(1)
    #if not cap.isOpened(): exit("Error: Could not open camera.")
    #print("Press 'space' to capture and process, 'q' to quit.")
    #while True:
        #ret, frame = cap.read()
        #if not ret: break
        #cv2.imshow("Chessboard Capture", frame)
        #key = cv2.waitKey(1) & 0xFF
        #if key == ord('q'): break
        #if key == ord(' '):
    camera = Camera(debug=True)
    print("Detected FEN:", camera.get_fen())
    #cap.release(); cv2.destroyAllWindows()


