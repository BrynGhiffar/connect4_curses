import curses
from curses import textpad

class Format:
    """
    This class is a context manager 
    for formatting text within the application
    """
    def __init__(self, stdscr, pair_number, fg_color, bg_color = -1):
        """
        Initializes the context manager, stores the pair number,
        stores the stdscr object
        """
        self.pair_number = pair_number
        curses.init_pair(pair_number, fg_color, bg_color)
        self.stdscr = stdscr

    def __enter__(self):
        self.stdscr.attron(curses.color_pair(self.pair_number))

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.stdscr.attroff(curses.color_pair(self.pair_number))

class FormatCollection:

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.next_pair_number = 1
        self.format_collection = dict()

    def get(self, fg: int, bg: int):
        if f"{fg} {bg}" in self.format_collection:
            return self.format_collection[f"{fg} {bg}"]
        else:
            self.format_collection[f"{fg} {bg}"] = \
                Format(self.stdscr, self.next_pair_number, fg, bg)
            self.next_pair_number += 1
            return self.format_collection[f"{fg} {bg}"]

class ConnectFourGame:

    def __init__(self, stdscr):
        self.stdscr = stdscr

        # board settins
        self.nrows = 7
        self.ncolumns = 7
        self.cell_size = 2 # the size of each cell
        self.cell_spacing = 1 # the spacing between each cell
        self.board_pos = (8, 1)
        self.title_pos = (1, 1)
        self.guide_pos = (8, 30)

        # game data
        self.board = [[0 for _ in range(self.ncolumns)]\
                      for _ in range(self.nrows)]
        self.next_row = [0 for _ in range(self.ncolumns)]
        self.selected_column = 0
        self.current_player = 1
        self.last_col = -1 # last column played
        self.title = [
        "░█████╗░░█████╗░███╗░░██╗███╗░░██╗███████╗░█████╗░████████╗░░██╗██╗",
        "██╔══██╗██╔══██╗████╗░██║████╗░██║██╔════╝██╔══██╗╚══██╔══╝░██╔╝██║",
        "██║░░╚═╝██║░░██║██╔██╗██║██╔██╗██║█████╗░░██║░░╚═╝░░░██║░░░██╔╝░██║",
        "██║░░██╗██║░░██║██║╚████║██║╚████║██╔══╝░░██║░░██╗░░░██║░░░███████║",
        "╚█████╔╝╚█████╔╝██║░╚███║██║░╚███║███████╗╚█████╔╝░░░██║░░░╚════██║",
        "░╚════╝░░╚════╝░╚═╝░░╚══╝╚═╝░░╚══╝╚══════╝░╚════╝░░░░╚═╝░░░░░░░░╚═╝"
        ]

        # chip constants
        self.EMPTY_CELL = 0
        self.PLAYER1 = 1 # These two are also game state constants
        self.PLAYER2 = 2 # 

        self.UNDECIDED = -1
        self.DRAW = 0

        self.game_state = self.UNDECIDED

        # Keys
        self.KEY_PLACE = ord('j')
        self.KEY_SCROLL_RIGHT = ord('l')
        self.KEY_SCROLL_LEFT = ord('h')

        self.formats = FormatCollection(self.stdscr)

    def draw_title(self):
        # draw title
        for yi, row in enumerate(self.title):
            y = self.title_pos[0] + yi
            x = self.title_pos[1]
            self.stdscr.addstr(y, x, row)

    def draw_board(self):
        # draw board
        start_y = self.board_pos[0]
        intrvl_y = self.cell_size + self.cell_spacing
        end_y = start_y + self.nrows * intrvl_y

        start_x = self.board_pos[1]
        intrvl_x = self.cell_size + self.cell_spacing
        end_x = start_x + self.ncolumns * intrvl_x

        for iy, y in enumerate(range(start_y, end_y, intrvl_y)):
            for ix, x in enumerate(range(start_x, end_x, intrvl_x)):
                fy = y + self.cell_size
                fx = x + self.cell_size
                textpad.rectangle(self.stdscr, y, x, fy, fx) # the board

                # drawing the chips
                val = self.board[self.nrows - iy - 1][ix]
                fy = y + self.cell_size // 2
                fx = x + self.cell_size // 2
                if val == self.EMPTY_CELL:
                    self.stdscr.addstr(fy, fx, ' ')
                elif val == self.PLAYER1:
                    with self.formats.get(-1, curses.COLOR_RED):
                        self.stdscr.addstr(fy, fx, ' ')
                elif val == self.PLAYER2:
                    with self.formats.get(-1, curses.COLOR_YELLOW):
                        self.stdscr.addstr(fy, fx, ' ')

    def draw_guide(self):
        y, x = self.guide_pos
        guide_text = ["█░█ █▀█ █░█░█   ▀█▀ █▀█   █▀█ █░░ ▄▀█ █▄█",
                      "█▀█ █▄█ ▀▄▀▄▀   ░█░ █▄█   █▀▀ █▄▄ █▀█ ░█░",
                      "",
                      "Press H to move left",
                      "Press L to move right",
                      "Press J to place chip",
                      "Press R to restart",
                      "Press Q to quit"]
        height, width = 10, 50
        textpad.rectangle(self.stdscr, y, x, y + height, x + width)
        for i, line in enumerate(guide_text):
            if i in [0, 1]:
                fy = y + i + 1
                fx = x + width // 2 - len(line) // 2
            else:
                fy = y + i + 1
                fx = x + 2
            self.stdscr.addstr(fy, fx, line)

    def draw_column_cursor(self):
        start_x = self.board_pos[1]
        intrvl_x = self.cell_size + self.cell_spacing
        end_x = start_x + self.ncolumns * intrvl_x

        shfty = 0
        shftx = 1
        # draw cursor row
        y = self.board_pos[0] + self.nrows * (self.cell_size + self.cell_spacing)
        for i, x in enumerate(range(start_x, end_x, intrvl_x)):
            if i == self.selected_column:
                with self.formats.get(curses.COLOR_BLACK, curses.COLOR_WHITE):
                    self.stdscr.addstr(y + shfty, x + shftx, str(i + 1))
            else:
                self.stdscr.addstr(y + shfty, x + shftx, str(i + 1))

    def draw_current_player_turn(self):
        # draw player turn text
        shfty = 3
        shftx = 0
        y = self.board_pos[0] + self.nrows * (self.cell_size + 1)
        x = self.board_pos[1]
        turn_txt = "TURN: "
        self.stdscr.addstr(y + shfty, x + shftx, turn_txt)
        if self.current_player == self.PLAYER1:
            with self.formats.get(curses.COLOR_BLACK, curses.COLOR_RED):
                self.stdscr.addstr(y + shfty, x + shftx + len(turn_txt), 
                                   f"PLAYER {self.current_player}")
        elif self.current_player == self.PLAYER2:
            with self.formats.get(curses.COLOR_BLACK, curses.COLOR_YELLOW):
                self.stdscr.addstr(y + shfty, x + shftx + len(turn_txt), 
                                   f"PLAYER {self.current_player}")

    def draw_game_over_text(self):
        # draw game over text
        shftx = 0
        shfty = 5
        game_over_txt = "PRESS Q TO EXIT OR PRESS R TO RESTART"
        y = self.board_pos[0] + self.nrows * (self.cell_size + 1)
        x = self.board_pos[1]
        if self.game_state == self.DRAW:
            self.stdscr.addstr(y + shfty, x + shftx,
                               f"THE GAME IS DRAW, {game_over_txt}")
        elif self.game_state in [self.PLAYER1, self.PLAYER2]:
            txt = f"PLAYER {self.game_state}"

            if self.game_state == self.PLAYER1:
                with self.formats.get(curses.COLOR_BLACK, curses.COLOR_RED):
                    self.stdscr.addstr(y + shfty, x + shftx, txt)
            elif self.game_state == self.PLAYER2:
                with self.formats.get(curses.COLOR_BLACK, curses.COLOR_YELLOW):
                    self.stdscr.addstr(y + shfty, x + shftx, txt)
            self.stdscr.addstr(y + shfty, x + shftx + len(txt),
                               f" WINS! {game_over_txt}")

    def draw(self):
        self.draw_title()
        self.draw_board()
        self.draw_guide()
        self.draw_column_cursor()
        self.draw_current_player_turn()
        self.draw_game_over_text()

    def place(self, col: int):
        if self.next_row[col] != self.nrows:
            self.board[self.next_row[col]][col] = self.current_player
            self.next_row[col] += 1
            self.current_player = (self.current_player % 2) + 1
            self.last_col = col

    def probe_game_state(self):
        if self.last_col != -1:
            col = self.last_col
            previous_player = (self.current_player % 2) + 1
            height_col = self.next_row[col] - 1
            is_undecided = False
            WIN_LENGTH = 4
            for i in range(self.ncolumns):
                if self.next_row[i] != self.nrows:
                    is_undecided = True
                    break
            # if there is a column that has not been filled up to row height   
            # then the game can still be played
            for dr in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), \
                       (-1, -1), (1, -1), (-1, 1)]:
                for j in range(WIN_LENGTH):
                    win = True
                    for k in range(WIN_LENGTH):
                        y = height_col - j * dr[0] + k * dr[0]
                        x = col - j * dr[1] + k * dr[1]
                        if (y >= self.nrows) or (y < 0) \
                            or (x >= self.ncolumns) or (x < 0):
                            win = False
                            break
                        if (self.board[y][x] != previous_player):
                            win = False
                            break
                    if win:
                        self.game_state = previous_player
                        return
                        # return previous_player
            if is_undecided:
                self.game_state = self.UNDECIDED
                return
                # return self.UNDECIDED # undecided
            else:
                self.game_state = self.DRAW
                return
                # return self.DRAW # draw
        self.game_state = self.UNDECIDED
        return
        # return self.UNDECIDED

    def on_key_press(self, key):
        if key == self.KEY_PLACE:
            self.place(self.selected_column)
        elif (key == self.KEY_SCROLL_LEFT) \
            and (self.selected_column > 0):
            self.selected_column -= 1
        elif (key == self.KEY_SCROLL_RIGHT) \
            and (self.selected_column < self.ncolumns - 1):
            self.selected_column += 1
        elif (key - ord('0')) in list(range(1, self.ncolumns + 1)):
            self.place(key - ord('0') - 1)

    def play(self):
        quit = False
        while not quit:
            self.stdscr.clear()
            self.probe_game_state()
            self.draw()
            key = self.stdscr.getch()
            if self.game_state == -1:
                self.on_key_press(key)
            if key in [ord('q'), ord('Q')]:
                quit = True
            elif key in [ord('r'), ord('R')]:
                self.__init__(self.stdscr)


def test_probe_game_state():
    g = ConnectFourGame(None)
    g.probe_game_state()
    for row in g.board:
        print(row)
    print(f"game state: {g.game_state}")
    g.place(0)
    g.place(0)
    g.place(1)
    g.place(1)
    g.place(2)
    g.place(2)
    g.place(3)
    g.place(3)
    for row in g.board:
        print(row)
    g.probe_game_state()
    print(f"game state: {g.game_state}")

if __name__ == '__main__':
    test_probe_game_state()
