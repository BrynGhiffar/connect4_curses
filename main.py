import curses
from classes import ConnectFourGame

def main(stdscr):
    curses.use_default_colors()
    curses.curs_set(0)
    ConnectFourGame(stdscr).play()
    pass

curses.wrapper(main)
