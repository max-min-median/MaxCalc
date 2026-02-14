# from expressions import Expression, Closure
# from tuples import *
# from number import RealNumber
# from operators import *
# import op
# from errors import ParseError
# import re

import expressions as X
import tuples as T
import number as N
import functions as F
import op
from vars import LValue, Value
from wordtoken import WordToken
from operators import *
from errors import *
import re
from settings import Settings

st = Settings()

# Performs surface-level parsing and validation. Does not attempt to split WordTokens or evaluate expressions.

def parse(s, offset=0, brackets='', parent=None):

    def addToken(token, m=None):  # modifies 'pos'!
        nonlocal i
        if token is not None:
            tokens.append(token)
            posList.append(tuple(offset + i + x for x in m.span(1)))
            # debug and print(f'{tuple(startPos + x for x in posList[-1])}: {t}')
        if m is not None:
            i += m.span()[1]

    def checkOpRegex():
        for regex in op.regex:
            if m := re.match(regex, ss):
                addToken(op.regex[regex], m)
                return True
        return False
    
    expr = X.Expression(inputStr=s, brackets=brackets, offset=offset)
    tokens, posList = expr.tokens, expr.tokenPos
    i = 0
    # print(f"Parsing '{s}', brackets: {brackets}, parent: {parent}")
    while ss := s[i:]:
        if (ch := ss[0]) == ',' or ch in ')]}' or (ch := ss[:2]) in [f'{T.ONE_TUPLE_INDICATOR}{ch}' for ch in ')]}']:  # last item in expression / tuple
            if parent is None:
                unexpected = "comma separator ','" if ch == ',' else f"delimiter '{ch}'"
                raise ParseError(f"Unexpected {unexpected} outside a tuple. Please enclose tuples in parentheses '()'.", (offset + i, offset + i + 1))
            elif ch != ',' and ch[-1] != parent.brackets[-1]:
                raise ParseError(f"Unexpected delimiter '{ch}'; should be '{(T.ONE_TUPLE_INDICATOR if len(ch) == 2 else '') + parent.brackets[-1]}' instead", (offset + i, offset + i + len(ch)))
            expr.inputStr = expr.inputStr[:i]
            validate(expr)
            return expr
        elif ss[0] in '([{': # tuple or bracketed expression
            tup = T.Tuple(inputStr=ss[0:], brackets={'(': '()', '[': '[]', '{': '{}'}[ss[0]], offset=i)
            i += 1
            while True:
                exprStartPos = i
                childExpr = parse(s[i:], offset=offset + i, brackets='', parent=tup)
                tup.tokens.append(childExpr)
                tup.tokenPos.append((exprStartPos, exprStartPos + len(childExpr.inputStr)))
                i += len(childExpr.inputStr)
                if s[i:i+1] == ',':
                    i += 1
                elif (rb := ' ') and i >= len(s) or (rb := s[i]) == tup.brackets[-1] or (rb := s[i:i+2]) == f'{T.ONE_TUPLE_INDICATOR}{tup.brackets[-1]}':
                    expr.tokenPos.append((tup.offset, i + len(rb)))
                    if len(tup) == 1 and len(tup.tokens[0].tokens) == 0:  # Tuple contains 1 empty expression; remove it.
                        tup.tokens, tup.tokenPos = [], []
                    if len(rb) != 2 and len(tup) == 1:  # convert 1-tuples to Expressions unless they end with ':)'
                        tup = tup.toExpr()
                    i += len(rb)
                    break
            expr.tokens.append(tup)

        elif m := re.match(r'(\d+(?:\.\d+)?|\.\d+)(?:[Ee](-?\d+))?', ss):   # Number. Cannot follow Number, spaceSeparator, or Var
            if (exponent := m.groups()[1]) is not None:
                addToken(N.RealNumber.fromScientificNotation(m.groups()[0], m.groups()[1]), m)
            else:
                addToken(N.RealNumber(m.groups()[0], fcf=True, epsilon=st.epsilon), m)
        elif checkOpRegex():
            continue
        elif m := re.match(r'([A-Za-z](?:\w*(?:\d(?!(?:[0-9.]))|[A-Za-z_](?![A-Za-z])))?)', ss):  # Word token (might be a concatenation of vars & possible func at the end) 
            # if tokens[-1] is not None and tokens[-1] is not Op.assignment: raise ParseError(f'Cannot assign to invalid l-value (pos {startPos + pos}). Did you mean "==" instead?')
            addToken(WordToken(m.group()), m)
        else:
            raise ParseError(f"Unrecognized symbol '{ss[0]}'", (offset + i, offset + i + 1))

    validate(expr)
    return expr


def validate(expr):
    # Validation checks
    i = 1
    # Remove space separators that come at the start or end
    if len(expr.tokens) > 0 and expr.tokens[0] == op.spaceSeparator: expr.tokens.pop(0); expr.tokenPos.pop(0)
    if len(expr.tokens) > 0 and expr.tokens[-1] == op.spaceSeparator: expr.tokens.pop(); expr.tokenPos.pop()
    lst, posList = [None] + expr.tokens + [None], [None] + expr.tokenPos + [None]
    while i < len(lst) - 1:
        # Transform / remove some types of tokens
        match lst[i-1:i+2]:
            case [_any_, PrefixFunction(), None]: raise ParseError(f"Missing inputs for function '{str(lst[i])}'", posList[i])
            case [_any_, PrefixFunction(), _notExpression_] if not isinstance(_notExpression_, X.Expression):
                raise ParseError(f"'{str(lst[i])}' must be followed by bracketed expression.", posList[i])
            # Bin cannot follow Bin / UL / None
            case [Infix() | Prefix() | None, Infix(), _any_]: raise ParseError(f"Unexpected operator '{str(lst[i])}'", posList[i])
            # Bin cannot precede Bin / UR / None
            case [_any_, Infix(), Infix() | Postfix()]: raise ParseError(f"Invalid operand for '{str(lst[i])}'", posList[i])
            case [_any_, Infix() | Prefix(), None]:
                raise ParseError(f"Missing operand for '{str(lst[i])}'", posList[i])
            # L to R: Convert +/- to positive/negative if they come after Bin / UL
            case [None | Infix() | Prefix(), op.ambiguousPlus | op.ambiguousMinus, _any_]:
                lst[i] = op.positive if lst[i] == op.ambiguousPlus else op.negative
                i -= 2
            # L to R: If not, convert +/- to addition/subtraction
            case [_any_, op.ambiguousPlus | op.ambiguousMinus, _any2_]:
                lst[i] = op.addition if lst[i] == op.ambiguousPlus else op.subtraction
                i -= 2
            case [op.assignment | op.lambdaArrow, X.Expression(), _maybeSpaceSeparator_] if not isinstance(lst[i], X.Closure) and lst[i].brackets == '{}' and len(lst[i]) == 1 and isinstance(w := lst[i].tokens[0], X.Expression) and w.brackets == '{}':
                lst[i] = lst[i].morphCopy(X.Closure)
                lst[i].tokenPos = lst[i].tokens[0].tokenPos
                lst[i].tokens = lst[i].tokens[0].tokens
                lst[i].brackets = '{{', '}}'
                if lst[i + 1] == op.spaceSeparator:
                    lst.pop(i + 1)
                    posList.pop(i + 1)
                # change Expression to a Closure
                # if lst[i+1] is a space separator, remove it.
                # put a op.closureCombiner (Infix) after the new Closure.
            # Numbers cannot follow space separators or evaluables
            case [Value() | op.spaceSeparator, N.RealNumber(), _any_]: raise ParseError(f"Number '{str(lst[i])}' cannot follow space separator or an evaluable expression", posList[i])
            # UR has to follow an evlauable or other UR
            case [_operand_, Postfix(), _any_] if not isinstance(_operand_, (Value, WordToken, Postfix)): raise ParseError(f"Unexpected operator '{str(lst[i])}'", posList[i])
            # UL cannot precede Bin, UR or None
            # case [Infix() | Prefix() | Value(), LValue(), _any_] if lst[i-1] != op.assignment: raise ParseError(f"RValue cannot be the target of an assignment", posList[i])
            case [_any_, WordToken(), op.assignment | op.lambdaArrow]:
                lst[i] = lst[i].morphCopy(LValue)
                i -= 2
            case [_any_, X.Expression(), op.assignment | op.lambdaArrow] if not isinstance(lst[i], T.LTuple):
                lst[i] = T.LTuple(lst[i])
                if lst[i + 1] == op.assignment and isinstance(lst[i - 1], WordToken):  # combine lst[i - 1] and lst[i] into an LFunc
                    lst[i - 1: i + 1] = [F.LFunc(lst[i - 1], lst[i])]
                    posList[i - 1: i + 1] = [(posList[i - 1][0], posList[i][1])]
                    i -= 1
                    continue
        i += 1
    expr.tokens, expr.tokenPos = lst[1:-1], posList[1:-1]

# test code
if __name__ == '__main__':
    from memory import Memory
    mem = Memory()
    st._loadFile("settings.txt")

    def testFunc():
        exp1 = parse('f(xab, xac) = 2 + 3')
        exp2 = parse('f(foobar) = 2 + 3')
        exp3 = parse('gf(barf) = 2 + 3')
        print(exp1.value(mem=mem))
        print(exp2.value(mem=mem))
        print(exp3.value(mem=mem))
        pass

    def testClosures():
        exp0 = parse('f(x) = {{y = 2}}(x + 5(3 + 4))(3y) + 5xy')
        exp1 = parse('f(x) = {(y = 2)} x + y')
        exp2 = parse('x => {{y = 3}} y => z')
        pass

    def testTuple():
        # exp0 = parse('(3, 4) + (1, 2)')
        # exp1 = parse('5+(3+5,1,2-3)-9')
        exp01 = parse('(1, 2, 3)')
        exp5 = parse('(a,(b,c),(d=3,f)) = (1,(2,3),(,5))')
        exp0 = parse('(1 + 2)')
        exp2 = parse('5  +  (   3 +   5, 1,,2 - 3  ) - 9')
        exp3 = parse('5 + ( 3 + 5 , (1, 5, 7) , (((2 , 7), 0), 2, 5)) - 9')
        exp4 = parse('{5, 3, 2[2, 4')
        exp6 = parse('nC2')
        print(str(exp6))
        pass
    
    def test1():
        exp0 = parse('3 + 3')
        print(exp0.value(mem))
        exp1 = parse('25 - cos +3pi + (5 sqrt(4)) - 4abc + sqr')
        print(str(exp1))
        parse('5P2 + (5)')
        parse('10C3')
        parse('cos(32x+0.5) + sin(6pi/3) - f(3) + g')
        exp2 = parse('--5--4++-+3-90')
        print(str(exp2))
        parse('k f(5)') # k*f(5)
        parse('300ab^2 c') # 300a*b^2*c
        exp3 = parse('300ab^2c') # 300a*b^(2*c)
        print(str(exp3))
        parse('1/2 x') # 1/2*x
        parse('2/3x') # 2/(3*x)
        exp7 = parse('7!/5!3!') # 7!/(5!*3!)
        print(str(exp7))
        parse('2.3pi')
        parse('k')
        parse('25 - cos +3pi + (5 sqrt(4)) - 4abc + sqr')
        exp4 = parse('   2^k  x + 3^abc + 2/3 x -   3x/5')
        print(str(exp4))
        exp5 = parse('2[3 + 4{5 + 6(7/4)}]')
        print(str(exp5))
        exp6 = parse('a = bc = def = 73')
        print(str(exp6))
        exp8 = parse('5!')
        exp9 = parse('fracpix2(3ab^2-4sqrsqrt5)')
        exp10 = parse('f(g) = 35x + 2y')
        exp11 = parse('fracpix2 = 35x + 2y')
        exp12 = parse('testfunc(xy) = x + 5y - 23 cos h')
        exp13 = parse('ab = fracsin3.2(b=3)/b - 23 cos h')
        exp14 = parse('(b=2) + sinb23(x+5) cos h')
        # (b=2) + <WT>(exp)<cos><WT>
        exp14 = parse('a + (b=2)^fracsin 2b')
        # (b=2) + <WT>(exp)<cos><WT>
        # print(str(exp8))
        # print(exp11.value)
        # result = exp8.value
        # result2 = exp7.value
        pass

    test1()
    testClosures()
