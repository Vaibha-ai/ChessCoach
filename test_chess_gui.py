import sys
import subprocess
import chess
import chess.svg
import pyautogui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QProgressBar
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
import time
import keyboard
import tkinter as tk
import stockfish

class MousePositionRecorder:
    def __init__(self):
        self.positions = []
        self.root = tk.Tk()
        self.root.title("Mouse Position Recorder")
        
        self.label = tk.Label(self.root, text="Press 'd' and click on the screen to record mouse positions")
        self.label.pack(pady=10)
        
        self.root.bind("<KeyPress-d>", self.record_mouse_position)
        
    def record_mouse_position(self, event):
        x, y = pyautogui.position()
        self.positions.append((x, y))
        self.label.config(text=f"Recorded position: x={x}, y={y}")
        if len(self.positions) == 2:
            self.root.destroy()  # Close the recorder GUI
            return
            
    def run(self):
        self.root.mainloop()

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = 'Chess Screen Clipper'
        self.left = 100
        self.top = 100
        self.width = 800
        self.height = 800
        self.initUI()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.take_full_screenshot)

        self.screenshot_taken = False

        # Initialize Stockfish engine with correct executable path
        self.stockfish = stockfish.Stockfish('stockfish/stockfish-windows-x86-64-avx2.exe')

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        layout = QVBoxLayout()

        self.fen_label = QLabel("Predicted FEN:", self)
        self.fen_label.setFont(QFont('Arial', 12))
        layout.addWidget(self.fen_label)

        self.centipawn_label = QLabel("Centipawn Value: ", self)  # New label for centipawn value
        self.centipawn_label.setFont(QFont('Arial', 12))
        layout.addWidget(self.centipawn_label)

        self.board_image_label = QLabel(self)
        layout.addWidget(self.board_image_label)

        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 1000)  # Set the range of the progress bar to accommodate centipawn values
        layout.addWidget(self.progressBar)

        self.button = QPushButton('Capture Screen', self)
        self.button.clicked.connect(self.capture_screenshot)
        layout.addWidget(self.button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def capture_screenshot(self):
        print("Capturing screenshot...")
        if not self.screenshot_taken:
            self.screenshot_taken = True
            self.take_full_screenshot()

    def take_full_screenshot(self):
        if len(recorder.positions) == 2:
            x1, y1 = recorder.positions[0]
            x2, y2 = recorder.positions[1]
            screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
            screenshot_path = 'C:/Users/97155/Downloads/tensorflow_chessbot-chessfenbot/board.png'
            screenshot.save(screenshot_path)
            self.run_tensorflow_chessbot(screenshot_path)
            # Restart the timer to continue capturing screenshots
            self.timer.start(2000)
        else:
            print("Please record two positions first.")

    
    def run_tensorflow_chessbot(self, image_path):
        command = f"C:/Users/97155/Downloads/tensorflow_chessbot-chessfenbot/tensorflow_chessbot.py --filepath {image_path}"
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()

        fen = None
        output_text = stdout.decode('utf-8').split("\n")

        for i in range(len(output_text)):
            line = output_text[i]
            if line.startswith("Predicted FEN:"):
                fen_line = output_text[i + 1].strip() if i + 1 < len(output_text) else None
                if fen_line:
                    fen = fen_line.split(":")[-1].strip()
                    self.fen_label.setText(f"Predicted FEN: {fen}")
                    break

        board = chess.Board(fen)

        # Get the best move from Stockfish
        self.stockfish.set_fen_position(board.fen())
        best_move_str = self.stockfish.get_best_move_time(1000)  # Adjust the time to analyze the position

        # Parse the best move string into a Move object
        best_move = chess.Move.from_uci(best_move_str)

        # Apply the best move to the board
        if best_move:
            board.push(best_move)

        # Display the updated board
        svg_image = chess.svg.board(board=board)
        self.display_board_image(svg_image)

        # Update centipawn label and progress bar
        centipawn_value = self.evaluate_board(board)
        self.centipawn_label.setText(f"Centipawn Value: {centipawn_value}")

        # Map centipawn value to the range of the progress bar and set it
        progress_value = min(int(centipawn_value), 1000)  # Limit to 1000 as the maximum value
        self.progressBar.setValue(progress_value)

    def display_board_image(self, svg_image):
        image = QImage.fromData(svg_image.encode('utf-8'))
        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(700, 500, aspectRatioMode=Qt.KeepAspectRatio)
        self.board_image_label.setPixmap(pixmap)

    def evaluate_board(self, board):
        self.stockfish.set_fen_position(board.fen())
        return int(self.stockfish.get_evaluation()["value"])  # Return the centipawn value directly

if __name__ == '__main__':
    app = QApplication(sys.argv)
    recorder = MousePositionRecorder()
    recorder.run()
    
    ex = App()
    ex.show()
    
    sys.exit(app.exec_())
