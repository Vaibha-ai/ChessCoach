import sys
import time
import subprocess
import chess
import chess.svg
import pyautogui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt

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

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        layout = QVBoxLayout()

        self.fen_label = QLabel("Predicted FEN:", self)
        self.fen_label.setFont(QFont('Arial', 12))
        layout.addWidget(self.fen_label)

        self.board_image_label = QLabel(self)
        layout.addWidget(self.board_image_label)

        self.button = QPushButton('Capture Screen', self)
        self.button.clicked.connect(self.capture_screenshot)
        layout.addWidget(self.button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def capture_screenshot(self):
        if not self.screenshot_taken:
            self.screenshot_taken = True
            self.take_full_screenshot()
            self.timer.start(2000)  # Start the timer to capture screenshots every 2 seconds

    def take_full_screenshot(self):
        screen_width, screen_height = pyautogui.size()
        x1, y1, x2, y2 = 255, 190, 1010, 945
        screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
        screenshot_path = 'C:/Users/97155/Downloads/tensorflow_chessbot-chessfenbot/board.png'
        screenshot.save(screenshot_path)
        self.run_tensorflow_chessbot(screenshot_path)

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
        svg_image = chess.svg.board(board=board)
        self.display_board_image(svg_image)

    def display_board_image(self, svg_image):
        image = QImage.fromData(svg_image.encode('utf-8'))
        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(700, 500, aspectRatioMode=Qt.KeepAspectRatio)
        self.board_image_label.setPixmap(pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    
    sys.exit(app.exec_())
