import curses
import os
import platform
import subprocess
from trie import Trie
from functions import Function
from operators import Operator
from collections import deque
import json

system = platform.system()
calcSplash = "MaxCalc v3.6.0-beta by max_min_median"

DISPLAY_LINE_LIMIT = 150

# - copy from display

class UI:

    _instance = None

    keymap = {
        "Windows":
        {
            443: {"key": curses.KEY_LEFT, "modifiers": {"ctrl"}},
            444: {"key": curses.KEY_RIGHT, "modifiers": {"ctrl"}},
            451: {"key": curses.KEY_PPAGE, "modifiers": {}},
            457: {"key": curses.KEY_NPAGE, "modifiers": {}},
            480: {"key": curses.KEY_UP, "modifiers": {"ctrl"}},
            481: {"key": curses.KEY_DOWN, "modifiers": {"ctrl"}},
            391: {"key": curses.KEY_LEFT, "modifiers": {"shift"}},
            400: {"key": curses.KEY_RIGHT, "modifiers": {"shift"}},
            547: {"key": curses.KEY_UP, "modifiers": {"shift"}},
            548: {"key": curses.KEY_DOWN, "modifiers": {"shift"}},
            449: {"key": curses.KEY_HOME, "modifiers": {}},
            388: {"key": curses.KEY_HOME, "modifiers": {"shift"}},
            449: {"key": curses.KEY_HOME, "modifiers": {}},
            388: {"key": curses.KEY_HOME, "modifiers": {"shift"}},
            455: {"key": curses.KEY_END, "modifiers": {}},
            384: {"key": curses.KEY_END, "modifiers": {"shift"}},
           1001: {"key": curses.KEY_LEFT, "modifiers": {"ctrl", "shift"}},
        },

        "Linux":
        {
            554: {"key": curses.KEY_LEFT, "modifiers": {"ctrl"}},
            569: {"key": curses.KEY_RIGHT, "modifiers": {"ctrl"}},
            393: {"key": curses.KEY_LEFT, "modifiers": {"shift"}},
            402: {"key": curses.KEY_RIGHT, "modifiers": {"shift"}},
            555: {"key": curses.KEY_LEFT, "modifiers": {"ctrl", "shift"}},
            570: {"key": curses.KEY_RIGHT, "modifiers": {"ctrl", "shift"}},
        },

        "Darwin":
        {},
    }


    pairIdx = None
    @staticmethod
    def makeColorPair(fg, bg):
        UI.pairIdx += 1
        curses.init_pair(UI.pairIdx, fg, bg)
        newPair = curses.color_pair(UI.pairIdx)
        UI.pairCodeToIdx[newPair] = UI.pairIdx
        return newPair

    @staticmethod
    def isWordChar(char):
        ascii = ord(char)
        return 65 <= ascii <= 90 or 97 <= ascii <= 122 or char in "_'"  # or 48 <= ascii <= 57


    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        if args or kwargs:
            cls._instance.initialize(*args, **kwargs)
        return cls._instance


    def initialize(self, mem, historyPath):
        
        if hasattr(self, 'initialized'): return
        else: self.initialized = True
        self.setupKeyboard()
        self.mem = mem
        self.historyPath = historyPath
        self.activeWin = "input"
        self.displaySelection = None
        # Initialize curses
        self.stdscr = curses.initscr()
        curses.update_lines_cols()
        curses.raw()
        curses.noecho()
        self.stdscr.keypad(1)
        try: curses.start_color()
        except: pass
        curses.use_default_colors()

        if UI.pairIdx is None:
            UI.pairIdx = 0
            UI.pairCodeToIdx = {}
            UI.YELLOW_ON_BLACK = UI.makeColorPair(226, -1)
            UI.GREY_ON_BLACK = UI.makeColorPair(241, -1)
            UI.GREEN_ON_BLACK = UI.makeColorPair(10, -1)
            UI.LIGHTBLUE_ON_BLACK = UI.makeColorPair(69, -1)
            UI.BRIGHT_PURPLE_ON_BLACK = UI.makeColorPair(201, -1)
            UI.DARK_PURPLE_ON_BLACK = UI.makeColorPair(129, -1)
            UI.BRIGHT_ORANGE_ON_BLACK = UI.makeColorPair(202, -1)
            UI.DIM_ORANGE_ON_BLACK = UI.makeColorPair(208, -1)
            UI.BRIGHT_GREEN_ON_BLACK = UI.makeColorPair(46, -1)
            UI.BRIGHT_RED_ON_BLACK = UI.makeColorPair(196, -1)
            UI.WHITE_ON_BLUE = UI.makeColorPair(-1, 21)
            UI.YELLOW_ON_BLUE = UI.makeColorPair(226, 21)
            UI.GREY_ON_BLUE = UI.makeColorPair(241, 21)
            UI.BRIGHT_WHITE_ON_BLACK = UI.makeColorPair(15, -1)
            # (prompt := "♦> ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙
            UI.pairIdxToCode = {v: k for k, v in UI.pairCodeToIdx.items()}

        # self.mem = memory
        self.statusDuration = 0
        # (prompt := "♦> ")  # →⇨►▶▷<◇▶❯›♦»•∙▷◇❯➤❯♦>∙
        self.prompt = (("♦", UI.BRIGHT_ORANGE_ON_BLACK), (">", UI.DIM_ORANGE_ON_BLACK), (" ", ))
        self.text = {"display": [], "status": [[]], "input": []}
        self.loadHistory()
        self.selectionAnchor = None
        self.pos = 0
        self.setupWindows()
        if "status" in self.subwins:
            self.addText("status", ("Hello :) Type 'help' for a quick guide!", UI.GREEN_ON_BLACK))
            self.redraw("status")
            self.doupdate()

    def setupKeyboard(self):
        from settings import Settings
        st = Settings()
        try:
            if not st.get("keyboard"): raise ImportError
            # raise ImportError  # skips loading `keyboard` - for testing
            import keyboard
            self.keyboard = keyboard
            self.keyboard.is_pressed(29)  # start up `keyboard` listener
        except ImportError:
            self.keyboard = type('DummyKeyboard', (), {'is_pressed': lambda self, *args: None})()

    def copyToClipboard(self, s):
        if system == "Windows": subprocess.run("clip", input=s.encode("utf-8"), check=True)
        elif system == "Darwin": subprocess.run("pbcopy", input=s.encode("utf-8"), check=True)
        elif system == "Linux": 
            if subprocess.run(["which", "xclip"], capture_output=True).returncode == 0:
                subprocess.run(["xclip", "-selection", "clipboard"], input=s.encode("utf-8"), check=True)
            elif subprocess.run(["which", "xsel"], capture_output=True).returncode == 0:
                subprocess.run(["xsel", "--clipboard"], input=s.encode("utf-8"), check=True)
            else:
                self.text["status"] = [[("No clipboard utility found. Install xclip or xsel."[:self.stdscr.getmaxyx()[1] - 3], UI.BRIGHT_RED_ON_BLACK)]]
                self.statusDuration = 1
                self.redraw("status")
                self.subwins["status"].refresh()


    def setupWindows(self) -> dict[str, curses.window]:
        os.system("cls" if os.name == "nt" else "clear")
        curses.raw()
        self.stdscr.erase()
        self.subwins = {}
        self.borderWins = {}
        prevWd = None if not hasattr(self, "wd") else self.wd
        self.ht, self.wd = self.stdscr.getmaxyx()
        while self.ht < 17 or self.wd < 44:
            self.stdscr.erase()
            if self.ht > 3 and self.wd > 15:
                self.stdscr.addstr(self.ht // 2, self.wd // 2 - 6, "Too small :(")
            self.stdscr.refresh()
            key = self.stdscr.getch()
            if key in (17, 27, 433): raise KeyboardInterrupt("Esc")
            curses.update_lines_cols()
            self.ht, self.wd = self.stdscr.getmaxyx()

        if prevWd != self.wd:
            self.displayLineLength = deque((sum(len(x[0]) for x in line) for line in self.text["display"]), DISPLAY_LINE_LIMIT)

        self.stdscr.addstr(0, (self.wd - len(calcSplash)) // 2, calcSplash, UI.LIGHTBLUE_ON_BLACK)
        self.borderWins["display"] = self.stdscr.subwin(self.ht * 3 // 4, self.wd, 1, 0)  # rows, cols, startrow, startcol
        self.borderWins["input"] = self.stdscr.subwin(self.ht - self.ht * 3 // 4 - 2, self.wd, self.ht * 3 // 4 + 2, 0)
        self.drawBorders()
        self.stdscr.noutrefresh()
        self.subwins["display"] = self.stdscr.subwin(self.ht * 3 // 4 - 2, self.wd - 2, 2, 1)
        self.subwins["display"].leaveok(True)
        self.subwins["display"].scrollok(True)
        self.subwins["status"] = self.stdscr.subwin(1, self.wd - 1, self.ht * 3 // 4 + 1, 1)
        self.subwins["status"].leaveok(True)
        self.subwins["status"].scrollok(True)
        self.subwins["input"] = self.stdscr.subwin(self.ht - self.ht * 3 // 4 - 4, self.wd - 2, self.ht * 3 // 4 + 3, 1)
        self.subwins["input"].leaveok(True)
        self.subwins["input"].scrollok(True)
        self.redraw("display", lastLine = len(self.text["display"]) - 1)
        self.redraw("input")
        self.redraw("status")
        return self.subwins


    def getWordAtPos(self, text, pos):  # returns (currWord, wordL, wordR)
        if not (pos > 0 and UI.isWordChar(text[pos - 1])) and not (pos < len(text) and UI.isWordChar(text[pos])):
            return None, len(text), 0
        else:
            wordL = wordR = pos
            while wordL > 0 and UI.isWordChar(text[wordL - 1]): wordL -= 1
            while wordR < len(text) and UI.isWordChar(text[wordR]): wordR += 1
            return ''.join(text[wordL:wordR]), wordL, wordR


    def getInput(self, trie: Trie=None):
        if not hasattr(self, 'st'):
            from settings import Settings
            self.st = Settings()
        if trie is not None: self.trie = trie
        text = []
        keys = []
        nearestWords = []
        self.pos = 0
        historyIndex = 0
        self.currWord = self.prevWord = None
        self.wordL, self.wordR = len(text), 0
        tabbed = False
        self.drawInput(text)

        while True:
            if keys == []:  # if there are no more keys left in the buffer, get more keys
                key = self.stdscr.getch()
                self.stdscr.nodelay(True)
                while (k := self.stdscr.getch()) != -1: keys.append(k)  # get all the keys at a go. Allows for e.g. simulating Ctrl-X as a sequence of Ctrl-C + Backspace
                keys.reverse()
                self.stdscr.nodelay(False)
            else:
                key = keys.pop()

            if (keyCombo := UI.keymap[system].get(key, None)): key = keyCombo["key"]
            shiftPressed = keyCombo is not None and "shift" in keyCombo["modifiers"] or self.keyboard.is_pressed(42) or self.keyboard.is_pressed(54)
            ctrlPressed = keyCombo is not None and "ctrl" in keyCombo["modifiers"] or self.keyboard.is_pressed(29)

            if key == 55 and (shiftPressed or self.keyboard.is_pressed(71)): key = curses.KEY_HOME
            elif key == 49 and (shiftPressed or self.keyboard.is_pressed(79)): key = curses.KEY_END

            # Handle window resizing
            if key == curses.KEY_RESIZE:
                self.setupWindows()
                self.drawInput(text, tabbed, nearestWords)
                continue

            if self.statusDuration > 0:
                self.statusDuration -= 1
                if self.statusDuration == 0: self.redraw("status")

            # Resolve tabbed state if the current key is not a tab or resize
            if tabbed is not False and key not in (9, 351, curses.KEY_RESIZE):
                text[self.wordL:self.wordR] = [*self.currWord + nearestWords[tabbed][len(self.currWord):]]
                self.pos = self.wordL + len(nearestWords[tabbed])
                tabbed = False

            # Register history as current input if a key is pressed which is not KEY_UP or KEY_DOWN.
            if historyIndex != 0 and key not in (curses.KEY_UP, curses.KEY_DOWN):
                if key in (curses.KEY_ENTER, 10, 13, 459):
                    self.inputHistory.pop(historyIndex)
                historyIndex = 0

            if key == 21:  # Ctrl-U = Ctrl-A then Backspace
                curses.ungetch(curses.KEY_BACKSPACE)
                curses.ungetch(1)  # Ctrl-A
                continue
            elif key == 24:  # Ctrl-X = Ctrl-C then Backspace
                if self.selectionAnchor is not None:
                    curses.ungetch(curses.KEY_BACKSPACE)
                    curses.ungetch(3)  # Ctrl-C
                continue

            if key == 1:  # Ctrl-A
                self.selectionAnchor = 0
                self.pos = len(text)
            elif key in (curses.KEY_BACKSPACE, 8, 127, curses.KEY_DC) and self.selectionAnchor is not None:
                selectL, selectR = sorted([self.selectionAnchor, self.pos])
                text[selectL:selectR] = []
                self.pos = selectL
                self.selectionAnchor = None
            elif key == 96:  # Backtick: switch window
                self.activeWin = "input" if self.activeWin == "display" else "display"
                if self.displaySelection is None:
                    curses.ungetch(curses.KEY_UP)
                self.drawBorders()
                self.redraw("display", lastLine=self.lastLine)
            elif key == 127:  # Ctrl-Backspace = Ctrl-Shift-Left + Backspace
                curses.ungetch(curses.KEY_BACKSPACE)
                curses.ungetch(1001)
                continue
            elif key in (curses.KEY_BACKSPACE, 8) and self.pos > 0:
                self.pos -= 1
                text[self.pos:self.pos+1] = []
            elif key == curses.KEY_DC and self.pos < len(text):
                text[self.pos:self.pos+1] = []
            elif key in (curses.KEY_UP, curses.KEY_DOWN):
                if self.activeWin == "input":
                    if key == curses.KEY_UP:
                        if -historyIndex == len(self.inputHistory): continue
                        if historyIndex == 0:
                            currentText = text
                        historyIndex -= 1
                        text = [*self.inputHistory[historyIndex]]
                        self.pos = len(text)
                    else:  # curses.KEY_DOWN
                        if historyIndex == 0: continue
                        historyIndex += 1
                        if historyIndex == 0:
                            text = currentText
                        else:
                            text = [*self.inputHistory[historyIndex]]
                        self.pos = len(text)
                else:  # self.activeWin == "display"
                    line = self.moveDisplaySelection(-1 if key == curses.KEY_UP else 1)
                    while True:
                        rng = self.getRangeEndingAtIndex(self.lastLine if self.lastLine is not None else len(self.text["display"]) - 1)[0]
                        if line < rng[0] + 2 and rng[0] != 0: self.lastLine -= 1
                        elif line > rng[-1] - 2 and rng[-1] != len(self.text["display"]) - 1: self.lastLine += 1
                        else: break
                    self.redraw("display", lastLine=self.lastLine)
            elif key in (curses.KEY_PPAGE, curses.KEY_NPAGE):
                if self.scrollDisplay(-1 if key == curses.KEY_PPAGE else 1):
                    self.redraw("display", lastLine=self.lastLine)
                    self.doupdate()
                continue
            elif key in (curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_HOME, curses.KEY_END):
                if shiftPressed:
                    if self.selectionAnchor is None: self.selectionAnchor = self.pos
                else:
                    self.selectionAnchor = None
                if key == curses.KEY_LEFT:
                    self.pos -= 1
                    if ctrlPressed:
                        while self.pos > 0 and (not UI.isWordChar(text[self.pos]) or UI.isWordChar(text[self.pos-1])): self.pos -= 1
                elif key == curses.KEY_RIGHT:
                    self.pos += 1
                    if ctrlPressed:
                        while self.pos < len(text) and (not UI.isWordChar(text[self.pos-1]) or self.pos < len(text) and UI.isWordChar(text[self.pos])): self.pos += 1
                elif key == curses.KEY_HOME: self.pos = 0
                elif key == curses.KEY_END: self.pos = len(text)
                self.pos = min(len(text), max(self.pos, 0))
                if self.selectionAnchor == self.pos: self.selectionAnchor = None
            elif key in (9, 351):  # TAB
                self.selectionAnchor = None
                if not nearestWords: continue
                if tabbed is False: tabbed = ((nearestWords[0] == self.currWord) if key == 9 else -1) % len(nearestWords)
                else: tabbed = (tabbed + (1 if key == 9 else -1)) % len(nearestWords)
            elif chr(key) in '([{' and self.selectionAnchor is not None:
                selectL, selectR = sorted([self.selectionAnchor, self.pos])
                text[selectL:selectL] = chr(key)
                text[selectR + 1:selectR + 1] = {'(': ')', '[': ']', '{': '}'}[chr(key)]
                self.selectionAnchor += 1
                self.pos += 1
            elif 32 <= key <= 126:  # usual alphanumeric + symbols
                # quickExponents
                if 48 <= key <= 57 and self.st.get("quick_exponents") and self.pos > 0 and (text[self.pos - 1] in ')]}' or self.wordR == self.pos and not isinstance(self.mem.get(self.currWord), (Operator)) and text[self.pos - 1] not in 'PC' and (text[self.pos - 1] not in 'Ee' or self.pos > 1 and not text[self.pos - 2].isdigit())):
                    typed = ['^', chr(key)]
                else:
                    typed = [chr(key)]
                
                if self.selectionAnchor is not None:
                    selectL, selectR = sorted([self.selectionAnchor, self.pos])
                    text[selectL:selectR] = typed
                    self.pos = selectL + len(typed)
                    self.selectionAnchor = None
                else:
                    text[self.pos:self.pos] = typed
                    self.pos += len(typed)
            elif key in (curses.KEY_ENTER, 10, 13, 459):  # Enter
                if self.activeWin == "input":
                    result = ''.join(text).strip()
                    if result:
                        self.subwins["status"].erase()
                        self.subwins["status"].refresh()
                        if len(self.text["display"]) > 0: self.addText("display")
                        self.addText("display", *self.prompt, (result, ))
                        if len(self.inputHistory) == 150: self.inputHistory.pop(0)
                        self.displaySelection = None
                        self.inputHistory.append(result)
                        return result
                    # ignore empty input
                    text = []
                    self.pos = 0
                else:
                    if self.displaySelection is None: continue
                    toCopy = self.text["display"][self.displaySelection]
                    hasPrompt = tuple(toCopy[:len(self.prompt)]) == self.prompt
                    toCopy = ''.join(x[0] for x in (toCopy[len(self.prompt):] if hasPrompt else toCopy))
                    curses.ungetch(96)  # switch back to input window
                    for ch in toCopy[::-1]:
                        curses.ungetch(ord(ch))
            elif key == 3:  # Ctrl-C
                if self.activeWin == "input":
                    if self.selectionAnchor is not None:
                        selectL, selectR = sorted([self.selectionAnchor, self.pos])
                        self.copyToClipboard(''.join(text[selectL:selectR]))
                elif self.displaySelection is not None:  # copy from display
                    toCopy = self.text["display"][self.displaySelection]
                    hasPrompt = tuple(toCopy[:len(self.prompt)]) == self.prompt
                    toCopy = ''.join(x[0] for x in (toCopy[len(self.prompt):] if hasPrompt else toCopy))
                    self.copyToClipboard(toCopy)
            elif key in (17, 27, 433):
                raise KeyboardInterrupt("Esc")
            
            self.currWord, self.wordL, self.wordR = self.getWordAtPos(text, self.pos)
            if self.prevWord != self.currWord:
                self.text["status"] = [[]]
                self.prevWord = self.currWord
                if self.currWord:
                    nearestWords = self.trie.nearestAutocomplete(self.currWord)
                    tabbed = False
                    # update text of status/autocomplete bar
                    spaces = ''
                    for word in nearestWords:
                        self.addText("status", (spaces, ), (word[:len(self.currWord)], UI.GREEN_ON_BLACK), (word[len(self.currWord):], UI.GREY_ON_BLACK), startNewLine=False)
                        spaces = '   '
                else:
                    nearestWords = []
                if self.statusDuration == 0: self.redraw("status")

            if keys: continue

            self.drawInput(text, tabbed, nearestWords)


    def drawInput(self, text, tabbed=False, nearestWords=[]):
        # redraws the input window and relocates the cursor
        if not self.subwins: return

        selectL, selectR = sorted([self.selectionAnchor, self.pos]) if self.selectionAnchor is not None else (len(text), 0)
        self.text["input"].clear()
        self.addText("input", *self.prompt)

        # 1. print left part
        self.addText("input", (''.join(text[:min(self.wordL, selectL)]), ), startNewLine=False)
        # 2. print from left end of selection to left end of autocomplete
        self.addText("input", (''.join(text[selectL:min(self.wordL, selectR)]), UI.WHITE_ON_BLUE), startNewLine=False)
        # 3. print from left end of autocomplete to left end of selection
        self.addText("input", (''.join(text[self.wordL:min(selectL, self.wordR)]), UI.YELLOW_ON_BLACK), startNewLine=False)
        # 4. print overlap of selection and autocomplete
        self.addText("input", (''.join(text[max(selectL, self.wordL):min(selectR, self.wordR)]), UI.YELLOW_ON_BLUE), startNewLine=False)
        # 5. print from right end of selection to right end of autocomplete
        self.addText("input", (''.join(text[max(selectL, selectR):self.wordR]), UI.YELLOW_ON_BLACK), startNewLine=False)

        if nearestWords:
            if tabbed is False: self.addText("input", (nearestWords[0][len(self.currWord):], UI.GREY_ON_BLUE if selectL <= self.wordR < selectR else UI.GREY_ON_BLACK), startNewLine=False)
            else: self.addText("input", (nearestWords[tabbed][len(self.currWord):], UI.YELLOW_ON_BLACK), startNewLine=False)

        # 6. print from right end of autocomplete to right end of selection
        self.addText("input", (''.join(text[max(self.wordR, self.wordL):selectR]), UI.WHITE_ON_BLUE), startNewLine=False)
        # 7. print right part
        self.addText("input", (''.join(text[max(self.wordR, selectR, min(self.wordL, selectL)):]), ), startNewLine=False)

        self.subwins["input"].move(*divmod(len(self.prompt) + (self.pos if tabbed is False else self.wordL + len(nearestWords[tabbed])), self.wd - 2))
        self.subwins["input"].cursyncup()
        self.redraw("input")
        self.doupdate()


    def addText(self, windowName, *strAndAttrTuples, startNewLine=True):  # adds text to self.text. Does not redraw window.
        if startNewLine:
            self.text[windowName].append([])
            if windowName == "display":
                self.displayHistory.append([])
                self.displayLineLength.append(None)
        self.text[windowName][-1] += strAndAttrTuples
        if windowName == "display":
            self.displayHistory[-1] += [tup if len(tup) == 1 else (tup[0], UI.pairCodeToIdx[tup[1]]) for tup in strAndAttrTuples]
            self.displayLineLength[-1] = sum(len(x[0]) for x in self.text[windowName][-1])
        return self

    def redraw(self, windowName, lastLine=None):  # does not call doupdate
        window, text = self.subwins[windowName], self.text[windowName]
        ht, wd = window.getmaxyx()
        window.erase()
        if windowName == "display":
            if lastLine is None or not hasattr(self, "lastLine"):
                self.lastLine = len(self.text[windowName]) - 1
            rnge, totalLines = self.getRangeEndingAtIndex(self.lastLine)
            pad = curses.newpad(totalLines + 1, wd)
        else:
            rnge = range(len(text))
            pad = curses.newpad(ht + 2, wd)

        for i in rnge:
            if pad.getyx()[1] != 0: pad.addstr('\n')
            if len(text[i]) == 0: pad.addstr(' ')
            if windowName == "display" and i == self.displaySelection:
                promptEnd = tuple(text[i][:len(self.prompt)]) == self.prompt and len(self.prompt)
                for j, item in enumerate(text[i]):
                    pad.addstr(*(item if j < promptEnd else (item[0], UI.YELLOW_ON_BLUE)))
                    # if pad.getyx()[0] >= ht: break
                    if pad.getyx()[0] >= totalLines: break
            else:
                for item in text[i]:
                    pad.addstr(*item)
                    # if pad.getyx()[0] >= ht: break
                    if pad.getyx()[0] >= (totalLines if windowName == "display" else ht): break


        wy, wx = window.getbegyx()
        py, px = pad.getyx()
        if windowName == "display": pRow = py - (px == 0) - ht + 1
        else: pRow = 0
        pad.noutrefresh(pRow, 0, wy, wx, wy + ht - 1, wx + wd - 1)
        # pminrow, pmincol, sminrow, smincol, smaxrow, smaxcol;
        # the p arguments refer to the upper left corner of the pad region to be displayed
        # and the s arguments define a clipping box on the screen within which the pad region is to be displayed.

    def doupdate(self):
        curses.curs_set(0)
        curses.doupdate()
        curses.curs_set(1)

    def drawBorders(self):
        for windowName in "display", "input":
            self.drawBorder(windowName)

    def drawBorder(self, windowName):
        win = self.borderWins[windowName]
        if self.activeWin == windowName:
            win.attron(UI.BRIGHT_WHITE_ON_BLACK)
            win.border(*((0, ) * 4 + (curses.ACS_LANTERN, ) * 4))
        else:
            win.attron(UI.GREY_ON_BLACK)
            win.box()
        win.noutrefresh()

    def getRangeEndingAtIndex(self, n):
        ht, wd = self.subwins["display"].getmaxyx()
        linesLeft, start = ht, n
        while linesLeft > 0 and start >= 0:
            chars = self.displayLineLength[start]
            if chars == 0:
                linesLeft -= 1
            else:
                lines, rem = divmod(chars, wd)
                linesLeft -= lines + (rem > 0)
            start -= 1
        return range(n, start, -1)[::-1], ht - linesLeft

    def moveDisplaySelection(self, dir):
        def selectionIsValid(i):
            line = self.text["display"][i]
            return line != [] and not any(len(t) == 2 and t[1] == UI.BRIGHT_RED_ON_BLACK for t in line)

        last = len(self.text["display"]) - 1
        curr = last if self.displaySelection is None else self.displaySelection + dir
        while 0 <= curr <= last and not selectionIsValid(curr):
            curr += dir
        if 0 <= curr <= last: self.displaySelection = curr
        return self.displaySelection

    def scrollDisplay(self, dy):
        if len(self.text["display"]) == 0 or dy == 0: return False  # cannot scroll if display is empty
        if self.lastLine is None: self.lastLine = len(self.text["display"]) - 1
        if self.lastLine + dy >= len(self.text["display"]): return False  # cannot scroll down if already at bottom
        if dy < 0 and self.getRangeEndingAtIndex(self.lastLine)[0][0] == 0: return False  # cannot scroll up if top line already in view
        dir = dy // abs(dy)
        self.lastLine += dir
        return dir + self.scrollDisplay(dy - dir)

    def saveHistory(self):
        with open(self.historyPath, "w") as f:
            f.write(json.dumps([*self.displayHistory]) + '\n')
            f.write(json.dumps([*self.inputHistory]) + '\n')

    def loadHistory(self):
        try:
            with open(self.historyPath) as f:
                line = f.readline()
                self.displayHistory = deque(json.loads(line) if line else [], DISPLAY_LINE_LIMIT)
                self.text["display"] = deque(([tuple(tup) if len(tup) == 1 else (tup[0], UI.pairIdxToCode[tup[1]]) for tup in line] for line in self.displayHistory), DISPLAY_LINE_LIMIT)
                self.displayLineLength = deque([sum(len(x[0]) for x in line) for line in self.text["display"]], DISPLAY_LINE_LIMIT)
                line = f.readline()
                self.inputHistory = json.loads(line) if line else []
        except FileNotFoundError:
            self.displayHistory = deque([], 150)
            self.text["display"] = deque([], 150)
            self.inputHistory = []


    def end(self):
        # Set everything back to normal
        self.stdscr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()


if __name__ == "__main__":
    # import tracemalloc
    # tracemalloc.start()
    # print("Loading dictionary...")
    # trie = Trie.fromTextFile('google-10000-english.txt')
    # mem_size, _mem_peak = tracemalloc.get_traced_memory()
    # print(f"Memory used: {mem_size=} bytes")
    # print(f"Trie stats:")
    # print(f"{trie.numWords() = }\n{trie.numChars() = }\n{trie.numNodes() = }")
    # print("Press any key...")
    ui = UI()
    # curses.raw()
    # ui.trie = trie
    while True:
        k = ui.stdscr.getch()
        ui.stdscr.addstr(f'key {str(k)} typed.\n')
        ui.stdscr.refresh()