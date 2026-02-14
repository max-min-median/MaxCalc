from operators import Prefix, Infix
import number as N
import functions as F
from vars import Var
from errors import ParseError

class WordToken:
    def __init__(self, name='<wordToken>'):
        self.name = name

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return str(self.name)

    def splitWordToken(self, mem, nextToken):
        # returns a list of possible splits of the string.
        # 'greediest' (longer tokens are prioritized) splits come first.
        def trySplit(s, numAllowed=False, onlyFuncsAllowed=False):
            if s == '': return [[]], [[]]
            lst, varList = [], []
            for i in reversed(range(len(s))):
                val = mem.get(thisWord := s[:i+1])
                if val is not None:
                    if isinstance(val, N.Number): thisWord = Var(thisWord)
                    else: thisWord = val
                    if onlyFuncsAllowed and not isinstance(thisWord, F.Function): continue
                    if i == len(s) - 1 and isinstance(thisWord, Prefix) and not isinstance(nextToken, Value): continue  # allow stuff like 'ksin3.0pi'
                elif numAllowed and not onlyFuncsAllowed and s[:i+1].isdigit() and not s[i+1:i+2].isdigit():
                    thisWord = N.RealNumber(s[:i+1])
                else:
                    continue
                splitRest, splitRestVars = trySplit(s[i+1:], numAllowed=isinstance(thisWord, (Prefix, Infix)), onlyFuncsAllowed=(type(thisWord) == F.Function))
                lst += [[s[:i+1]] + spl for spl in splitRest]
                varList += [[thisWord] + spl for spl in splitRestVars]
            return lst, varList
        
        splitList, varList = trySplit(self.name)

        if len(splitList) == 0: raise ParseError(f"Unable to parse '{self.name}'")
        # tmp = ['∙'.join(s) for s in splitList]
        if len(splitList) > 1:
            from UI import UI
            UI().addText("display", ("Warning: ", UI["YELLOW"]["BLACK"]), (f"Found {len(splitList)} ways to parse ", ), (self.name, UI["BRIGHT_PURPLE"]["BLACK"]), ('.', ))
            tmp = [item for substr in splitList[0] for item in ((substr, UI["BRIGHT_PURPLE"]["BLACK"]), ("∙", ))][:-1]
            UI().addText("display", (" (Using ", ), *tmp, (")", ), startNewLine=False)
            # ': " + ", ".join(tmp) + f". (selecting '{tmp[0]}')")
        return splitList[0], varList[0]

    def morphCopy(self, cls=None):  # makes a copy of the object, optionally changing its class
        if cls is None: cls = type(self)
        cpy = cls.__new__(cls)
        cpy.__dict__.update(self.__dict__)
        return cpy