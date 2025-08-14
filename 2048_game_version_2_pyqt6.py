import sys
import random
import copy
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from PyQt6.QtCore import Qt, QRect

class Game2048:
    def __init__(self, size=4):
        self.size = size
        self.score = 0
        self.game_over = False
        self.grid = [[0] * size for _ in range(size)]
        
        self.undo_stack = []
        self.redo_stack = []

        self.add_new_tile()
        self.add_new_tile()
        self.save_state()

    def get_state(self):
        return (copy.deepcopy(self.grid), self.score, self.game_over)

    def set_state(self, state):
        grid, score, game_over = state
        self.grid = grid
        self.score = score
        self.game_over = game_over

    def save_state(self):
        self.undo_stack.append(self.get_state())
        self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.get_state())
            self.undo_stack.pop()
            last_state = self.undo_stack[-1]
            self.set_state(last_state)
            return True
        return False

    def redo(self):
        if self.redo_stack:
            next_state = self.redo_stack.pop()
            self.set_state(next_state)
            self.undo_stack.append(self.get_state())
            return True
        return False

    def get_empty_cells(self):
        return [(r, c) for r in range(self.size) for c in range(self.size) if self.grid[r][c] == 0]

    def add_new_tile(self):
        empty_cells = self.get_empty_cells()
        if empty_cells:
            r, c = random.choice(empty_cells)
            self.grid[r][c] = 2 if random.random() < 0.9 else 4

    def _compress(self, row):
        new_row = [i for i in row if i != 0]
        return new_row + [0] * (self.size - len(new_row))

    def _merge(self, row):
        row = self._compress(row)
        for i in range(self.size - 1):
            if row[i] != 0 and row[i] == row[i+1]:
                row[i] *= 2
                self.score += row[i]
                row[i+1] = 0
        return self._compress(row)

    def _transpose(self):
        self.grid = [list(t) for t in zip(*self.grid)]

    def _reverse(self):
        self.grid = [row[::-1] for row in self.grid]

    def move(self, direction):
        if self.game_over:
            return False

        original_grid = copy.deepcopy(self.grid)
        moved = False

        if direction == 'left':
            self.grid = [self._merge(row) for row in self.grid]
        elif direction == 'right':
            self._reverse()
            self.grid = [self._merge(row) for row in self.grid]
            self._reverse()
        elif direction == 'up':
            self._transpose()
            self.grid = [self._merge(row) for row in self.grid]
            self._transpose()
        elif direction == 'down':
            self._transpose()
            self._reverse()
            self.grid = [self._merge(row) for row in self.grid]
            self._reverse()
            self._transpose()

        if self.grid != original_grid:
            moved = True
            self.add_new_tile()
            self.save_state()
            if not self.can_move():
                self.game_over = True
        return moved
    
    def can_move(self):
        if self.get_empty_cells(): return True
        for r in range(self.size):
            for c in range(self.size):
                if c < self.size - 1 and self.grid[r][c] == self.grid[r][c+1]: return True
                if r < self.size - 1 and self.grid[r][c] == self.grid[r+1][c]: return True
        return False

class GameBoardWidget(QWidget):
    CELL_SIZE = 100
    CELL_PADDING = 10
    FONT = QFont("Helvetica", 32, QFont.Weight.Bold)
    
    COLORS = {
        0: "#cdc1b4", 2: "#eee4da", 4: "#ede0c8", 8: "#f2b179",
        16: "#f59563", 32: "#f67c5f", 64: "#f65e3b", 128: "#edcf72",
        256: "#edcc61", 512: "#edc850", 1024: "#edc53f", 2048: "#edc22e",
        4096: "#3c3a32"
    }

    def __init__(self, game_instance):
        super().__init__()
        self.game = game_instance
        self.grid_pixel_size = self.game.size * self.CELL_SIZE + (self.game.size + 1) * self.CELL_PADDING
        self.setFixedSize(self.grid_pixel_size, self.grid_pixel_size)

    def get_color(self, value):
        return QColor(self.COLORS.get(value, self.COLORS[4096]))

    def get_text_color(self, value):
        return QColor("#776e65") if value in [2, 4] else QColor("#f9f6f2")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#bbada0"))
        
        for r in range(self.game.size):
            for c in range(self.game.size):
                x = c * self.CELL_SIZE + (c + 1) * self.CELL_PADDING
                y = r * self.CELL_SIZE + (r + 1) * self.CELL_PADDING
                
                value = self.game.grid[r][c]
                color = self.get_color(value)
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawRoundedRect(x, y, self.CELL_SIZE, self.CELL_SIZE, 5, 5)

                if value != 0:
                    text_color = self.get_text_color(value)
                    painter.setPen(QPen(text_color))
                    painter.setFont(self.FONT)
                    rect = QRect(x, y, self.CELL_SIZE, self.CELL_SIZE)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(value))
        
        if self.game.game_over:
            painter.setBrush(QColor(238, 228, 218, 180))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.rect())
            
            painter.setPen(QColor("#776e65"))
            painter.setFont(QFont("Helvetica", 48, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Game Over!")

class GameGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2048 game")
        self.game = Game2048()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.score_label = QLabel(f"Score: {self.game.score}")
        self.score_label.setFont(QFont("Helvetica", 16))
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.score_label)

        self.board_widget = GameBoardWidget(self.game)
        main_layout.addWidget(self.board_widget)

        button_layout = QHBoxLayout()
        self.undo_button = QPushButton("⬅️ בטל")
        self.undo_button.setFont(QFont("Helvetica", 12))
        self.undo_button.clicked.connect(self.undo_action)
        
        self.redo_button = QPushButton("בצע שוב ➡️")
        self.redo_button.setFont(QFont("Helvetica", 12))
        self.redo_button.clicked.connect(self.redo_action)

        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.redo_button)
        main_layout.addLayout(button_layout)
        
        self.update_ui()
        self.setFocus()

    def update_ui(self):
        self.score_label.setText(f"Score: {self.game.score}")
        self.undo_button.setEnabled(len(self.game.undo_stack) > 1)
        self.redo_button.setEnabled(bool(self.game.redo_stack))
        self.board_widget.update()

    def keyPressEvent(self, event):
        if self.game.game_over:
            return

        key_map = {
            Qt.Key.Key_Up: "up", Qt.Key.Key_W: "up",
            Qt.Key.Key_Down: "down", Qt.Key.Key_S: "down",
            Qt.Key.Key_Left: "left", Qt.Key.Key_A: "left",
            Qt.Key.Key_Right: "right", Qt.Key.Key_D: "right"
        }
        
        direction = key_map.get(event.key())
        if direction:
            if self.game.move(direction):
                self.update_ui()

    def undo_action(self):
        if self.game.undo():
            self.update_ui()

    def redo_action(self):
        if self.game.redo():
            self.update_ui()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameGUI()
    window.show()
    sys.exit(app.exec())