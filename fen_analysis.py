import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import chess
from stockfish import Stockfish
import pandas as pd
import tqdm
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk 

def switch_side_to_move(fen):
    parts = fen.split()
    side_to_move = parts[1]
    if side_to_move == 'w':
        side_to_move = 'b'
    else:
        side_to_move = 'w'
    return parts[0] + ' ' + side_to_move

piece_scores = {
    "p": 1,
    "P": -1,
    "r": 5,
    "R": -5,
    "n": 3,
    "N": -3,
    "b": 3,
    "B": -3,
    "q": 9,
    "Q": -9
}

# Initialize Stockfish engine
stockfish_good = Stockfish("stockfish/stockfish-windows-x86-64-avx2.exe")
stockfish_good.set_depth(20)  # How deep the AI looks
stockfish_good.set_skill_level(20)  # Highest rank stockfish

# Define function to build stored game analysis
def build_stored_game_analysis(game, move_number):
    row = {}
    row['move_number'] = move_number
    row['taken'] = []
    board = chess.Board()
    for san in game[:move_number]:
        parsed_san = board.parse_san(san)
        taken = board.piece_at(parsed_san.to_square)
        if taken:
            row['taken'].append(taken.__str__())
        move = board.push_san(san)
    row['invalid'] = bool(board.promoted) or bool(board.outcome())
    stockfish_good.set_fen_position(board.fen())
    evaluation = stockfish_good.get_evaluation()
    row['evaluation'] = evaluation['value']
    row['taken_score'] = sum([piece_scores.get(p) for p in row['taken']]) * 100
    row['fen'] = board.fen()
    try:
        row['last_move'] = san
    except:
        print(game)
        row['invalid'] = True
    return row

# Read FEN strings from file starting from the second line
fens = []
with open('fen.txt', 'r') as file:
    next(file)  # Skip the first line
    for line in file:
        fens.append(line.strip())  # Strip whitespace and newline characters

# Switch side to move for alternating FEN strings
switched_fens = []
for i, fen in enumerate(fens):
    fen_without_suffix = fen.split()[0]  # Remove parts after the first space
    if i % 2 == 0:
        switched_fens.append(fen_without_suffix + ' w')  # Add 'w' for even-indexed FEN strings
    else:
        switched_fens.append(fen_without_suffix + ' b')  # Add 'b' for odd-indexed FEN strings

def recognize_move(current_fen, next_fen):
    current_board = chess.Board(current_fen)
    next_board = chess.Board(next_fen)

    for move in current_board.legal_moves:
        current_board.push(move)
        if current_board.board_fen() == next_board.board_fen():  # Use board_fen to compare only piece placements
            current_board.pop()
            return move.uci()  # UCI format for the move
        current_board.pop()

    return "No move recognized"

new_games = []
for i in range(len(switched_fens) - 1):
    current_fen = switched_fens[i]
    next_fen = switched_fens[i+1]
    move = recognize_move(current_fen, next_fen)
    new_games.append(move)        

# Recognize moves and store analysis results
rows = []
for move_number in tqdm.tqdm(range(1, len(new_games) + 1)):
    rows.append(build_stored_game_analysis(new_games, move_number))

# Create DataFrame containing analysis results
moves = pd.DataFrame(rows).set_index("move_number")

# Create Tkinter application window
root = tk.Tk()
root.title("Analysis Plot")

# Create a frame for the plot
plot_frame = ttk.Frame(root)
plot_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Create a Figure
fig = Figure(figsize=(12, 10), dpi=100)
ax1 = fig.add_subplot(211)  # Two rows, one column, first subplot
ax2 = fig.add_subplot(212)  # Two rows, one column, second subplot

# Plot the data
moves[['taken_score', 'evaluation']].plot(kind="bar", ax=ax1)
ax1.set_xlabel("Move Number")
ax1.set_ylabel("Scores")

# Define thresholds for major deflections
threshold_25 = 25
threshold_50 = 50

# Plot evaluation differences
evaluations_series = pd.Series(moves['evaluation'])
evaluation_diffs = [evaluations_series.iloc[i] - evaluations_series.iloc[i-1] for i in range(1, len(evaluations_series))]

ax2.plot(range(1, len(evaluations_series)), evaluation_diffs, color='purple')
ax2.set_title("Evaluation Score Difference After Each Move")
ax2.set_xlabel("Move Number")
ax2.set_ylabel("Evaluation Score Difference")
ax2.grid(True)

annotated_points = []
for i, diff in enumerate(evaluation_diffs):
    if i < len(new_games) - 1 and (abs(diff) > threshold_50 or abs(diff) > threshold_25):
        move_before = new_games[i]
        move_after = new_games[i + 1]
        annotated_points.append((move_before, move_after, diff))

# Display annotations outside the plot
for move_before, move_after, diff in annotated_points:
    # Find the peak index
    peak_index = np.argmax(evaluation_diffs[new_games.index(move_before):new_games.index(move_after)]) + new_games.index(move_before) + 1
    
    # Determine color based on depth
    if abs(diff) > threshold_50:
        color = 'red'
    elif abs(diff) > threshold_25:
        color = 'orange'
    else:
        color = 'black'
    
    # Plot dotted line connecting the dip to the annotation text
    ax2.plot([peak_index, len(evaluations_series)], [evaluation_diffs[peak_index-1], diff], linestyle='--', color=color)
    
    # Display annotation text outside the plot with adjusted color
    ax2.text(len(evaluations_series) + 1, diff, f"{move_before} to {move_after}", fontsize=8, ha='left', va='center', color=color)

ax2.set_xlim(1, len(evaluations_series) + 1)

# Add the plot to a Tkinter canvas
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.draw()

# Add the canvas to the Tkinter window
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Add a toolbar if needed
toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()

# Create a Tkinter button to close the window
close_button = ttk.Button(root, text="Close", command=root.destroy)
close_button.pack(pady=10)

# Run the Tkinter event loop
root.mainloop()
