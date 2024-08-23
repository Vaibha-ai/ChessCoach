import sys
import subprocess
import chess
import chess.svg
import pyautogui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QProgressBar, QTextEdit
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
import tkinter as tk
import stockfish
from chatgpt_api import run_chatgpt

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

        # Initialize the fens list with the starting FEN string
        self.fens = [
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        ]
        
        # Initialize an ordered dictionary to store unique FEN strings
        self.fens_set = set(self.fens)

        self.move_number = 1

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

        self.chatgpt_output_textedit = QTextEdit(self)
        layout.addWidget(self.chatgpt_output_textedit)

        self.button_capture = QPushButton('Capture Screen', self)
        self.button_capture.clicked.connect(self.capture_screenshot)
        layout.addWidget(self.button_capture)

        self.button_explanation = QPushButton('Explanation', self)
        self.button_explanation.clicked.connect(self.get_explanation)
        layout.addWidget(self.button_explanation)
        
        self.button_analyze = QPushButton('Analyze', self)
        self.button_analyze.clicked.connect(self.analyze)
        layout.addWidget(self.button_analyze)

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
            #self.timer.start(1000)
            self.screenshot_taken = False 
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
                    if fen not in self.fens_set:
                        # Ensure that the extracted FEN is the only one added to self.fens
                        self.fens.append(fen)
                        self.fens_set.add(fen)  # Add to the set for uniqueness
                    self.fen_label.setText(f"Predicted FEN: {fen}")
                    # Ensure the order of FENs matches the order of extraction
                    break

        if fen:
            try:
                board = chess.Board(fen)
                if board.is_valid():
                    self.process_valid_board(board)
                else:
                    print("The predicted FEN is invalid.")
            except ValueError:
                print("Error: Invalid FEN format.")
        else:
            print("Error: Failed to extract FEN from the output.")


    def process_valid_board(self, board):
        # Get the best move from Stockfish
        self.stockfish.set_fen_position(board.fen())
        best_move_str = self.stockfish.get_best_move_time(1000)  # Adjust the time to analyze the position

        if best_move_str is not None:  # Check if best_move_str is not None
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
        
    def analyze(self):
        with open("fen.txt", "w") as file:
            for fen in self.fens:
                file.write(fen + "\n")
                
        # Read the saved fen strings from the file
        with open("fen.txt", "r") as file:
            fens = file.readlines()[1:]  # Skip the first line
        
        # Replace the fens list with the array of fens read from the fen.txt file
        self.fens = [fen.strip() for fen in fens]
                
        # Get moves and save them in moves.txt
        with open("moves.txt", "w") as moves_file:
            for i in range(len(self.fens)-1):
                current_fen = self.fens[i]
                next_fen = self.fens[i+1]
                move = recognize_move(current_fen, next_fen)
                moves_file.write(f"Recognized move: {move}\n")
        subprocess.run(["python", "fen_analysis.py"])

    def display_board_image(self, svg_image):
        image = QImage.fromData(svg_image.encode('utf-8'))
        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(700, 500, aspectRatioMode=Qt.KeepAspectRatio)
        self.board_image_label.setPixmap(pixmap)

    def evaluate_board(self, board):
        self.stockfish.set_fen_position(board.fen())
        return int(self.stockfish.get_evaluation()["value"])  # Return the centipawn value directly

    def get_explanation(self):
        fen = self.fen_label.text().split(":")[-1].strip()
        best_move_str = self.stockfish.get_best_move_time(1000)  # Adjust the time to analyze the position
        response = run_chatgpt(fen, best_move_str)
        self.chatgpt_output_textedit.setText(response)

def recognize_move(current_fen, next_fen): 
    current_board = chess.Board(current_fen) 
    next_board = chess.Board(next_fen)

    for move in current_board.legal_moves:
        current_board.push(move) 
        if current_board.fen() == next_board.fen():
            current_board.pop() 
            return move.uci()  # UCI format for the move
        current_board.pop()

    return "No move recognized"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    recorder = MousePositionRecorder()
    recorder.run()
    
    ex = App()
    ex.show()
    
    sys.exit(app.exec_())
