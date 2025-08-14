import tkinter as tk
import random
import copy

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
            return

        original_grid = copy.deepcopy(self.grid)

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
            self.add_new_tile()
            self.save_state()
            if not self.can_move():
                self.game_over = True
    
    def can_move(self):
        if self.get_empty_cells(): return True
        for r in range(self.size):
            for c in range(self.size):
                if c < self.size - 1 and self.grid[r][c] == self.grid[r][c+1]: return True
                if r < self.size - 1 and self.grid[r][c] == self.grid[r+1][c]: return True
        return False

class GameGUI(tk.Tk):
    CELL_SIZE = 100
    CELL_PADDING = 10
    FONT = ("Helvetica", 32, "bold")
    
    COLORS = {
        0: "#cdc1b4", 2: "#eee4da", 4: "#ede0c8", 8: "#f2b179",
        16: "#f59563", 32: "#f67c5f", 64: "#f65e3b", 128: "#edcf72",
        256: "#edcc61", 512: "#edc850", 1024: "#edc53f", 2048: "#edc22e",
        4096: "#3c3a32"
    }

    def __init__(self):
        super().__init__()
        self.title("2048 game")
        self.game = Game2048()
        self.grid_size = self.game.size * self.CELL_SIZE + (self.game.size + 1) * self.CELL_PADDING
        
        top_frame = tk.Frame(self)
        top_frame.pack(pady=10)
        self.score_label = tk.Label(top_frame, text="Score: 0", font=("Helvetica", 16))
        self.score_label.pack()
        
        self.canvas = tk.Canvas(self, width=self.grid_size, height=self.grid_size, bg="#bbada0")
        self.canvas.pack(pady=(0, 10), padx=20)
        
        button_frame = tk.Frame(self)
        button_frame.pack(pady=(0, 20))
        
        self.undo_button = tk.Button(button_frame, text="⬅️ בטל", font=("Helvetica", 12), command=self.undo_action)
        self.undo_button.pack(side=tk.LEFT, padx=10)
        
        self.redo_button = tk.Button(button_frame, text="בצע שוב ➡️", font=("Helvetica", 12), command=self.redo_action)
        self.redo_button.pack(side=tk.RIGHT, padx=10)

        self.bind("<Key>", self.key_pressed)
        self.draw_grid()

    def get_color(self, value):
        return self.COLORS.get(value, self.COLORS[4096])

    def get_text_color(self, value):
        return "#776e65" if value in [2, 4] else "#f9f6f2"

    def draw_grid(self):
        self.canvas.delete("all")
        for r in range(self.game.size):
            for c in range(self.game.size):
                x1 = c * self.CELL_SIZE + (c + 1) * self.CELL_PADDING
                y1 = r * self.CELL_SIZE + (r + 1) * self.CELL_PADDING
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE
                
                value = self.game.grid[r][c]
                color = self.get_color(value)
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                
                if value != 0:
                    text_color = self.get_text_color(value)
                    self.canvas.create_text(x1 + self.CELL_SIZE/2, y1 + self.CELL_SIZE/2, 
                                            text=str(value), font=self.FONT, fill=text_color)
        
        self.score_label.config(text=f"Score: {self.game.score}")

        if self.game.game_over:
            self.canvas.create_rectangle(0, 0, self.grid_size, self.grid_size, fill="#eee4da", stipple="gray50")
            self.canvas.create_text(self.grid_size/2, self.grid_size/2, 
                                    text="Game Over!", font=("Helvetica", 48, "bold"), fill="#776e65")
        
        self.update_button_states()

    def key_pressed(self, event):
        if self.game.game_over: return

        key_map = {"Up": "up", "Down": "down", "Left": "left", "Right": "right",
                   "w": "up", "s": "down", "a": "left", "d": "right"}
        
        if event.keysym in key_map:
            self.game.move(key_map[event.keysym])
            self.draw_grid()
    
    def undo_action(self):
        if self.game.undo():
            self.draw_grid()

    def redo_action(self):
        if self.game.redo():
            self.draw_grid()

    def update_button_states(self):
        self.undo_button.config(state=tk.NORMAL if len(self.game.undo_stack) > 1 else tk.DISABLED)
        self.redo_button.config(state=tk.NORMAL if self.game.redo_stack else tk.DISABLED)

if __name__ == "__main__":
    app = GameGUI()
    app.mainloop()