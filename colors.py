import curses

def main(stdscr):
    curses.start_color()
    curses.use_default_colors()
    for i in range(1, curses.COLOR_PAIRS):
        curses.init_pair(i, 7, i)
    try:
        for i in range(0, 255):
            stdscr.addstr(str(i), curses.color_pair(i))
    except curses.error:
        # End of screen reached
        pass
    stdscr.getch()

curses.wrapper(main)