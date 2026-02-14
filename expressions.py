from settings import Settings
from operators import *
from errors import CalculatorError, ParseError
import op
from vars import *
from wordtoken import WordToken
from functions import Function, LFunc

st = Settings()
dummy = Var('dummy')


class Expression(Value):

    def __init__(self, inputStr=None, brackets='', offset=0):
        self.inputStr = inputStr  # only the part of the string relevant to this Expression.
        self.tokens = []
        self.tokenPos = []  # position of individual tokens within this Expression.
        self.parsed = None
        self.parsedPos = None
        self.brackets = brackets  # 2-char string, '()', '[]', '{}' or an empty string.
        self.offset = offset  # position of this Expression relative to input string.


    def value(self, mem, debug=False):

        from tuples import Tuple, LTuple

        def evaluate(power=0, index=0, skipEval=False):  # returns (Value, endIndex)
            def tryOperate(L, *args, **kwargs):
                try:
                    ret = dummy if skipEval else token.function(L, *args, **kwargs)
                    if debug: print(f"{str(token).strip(): ^3}:", ', '.join((str(L),) + tuple(str(a) for a in args)))
                    return ret
                except CalculatorError as e:
                    raise (type(e))(e.args[0], tokenPos)

            L = None
            while True:
                token = self.parsed[index]
                tokenPos = self.parsedPos[index]
                if isinstance(token, WordToken) and not skipEval:
                    try:
                        splitList, varList = token.splitWordToken(mem, self.parsed[index+1])
                    except CalculatorError as e:
                        raise (type(e))(e.args[0], self.parsedPos[index])
                    self.parsed[index:index+1] = varList
                    prev = 0
                    self.parsedPos[index:index+1] = [(self.parsedPos[index][0] + prev, self.parsedPos[index][0] + (prev := prev + len(s))) for s in ([''] + splitList)[:-1]]
                    continue
                match L, token:
                    case None, Value() | WordToken():
                        L = dummy if skipEval else token.value(mem=mem)
                        index += 1
                        continue
                    # case None, Postfix() | Infix():
                    #     raise ParseError(f"Unexpected operator '{token.name}'", self.parsedPos[index])
                    # non-Fn-Fn : Low
                    # non-Fn-Prefix : Low
                    # non-Fn-non-Fn : High
                    # Fn-Fn : High
                    case Function(), Expression():
                        if not isinstance(token, Tuple): self.parsed[index] = Tuple.fromExpr(token)
                        token = op.functionInvocation
                    case Value(), Function() | Prefix() if not isinstance(L, Function):  # Fn-Fn = High, nonFn-Fn = Low
                        # implicit mult of value to function / prefix, slightly lower precedence. For cases like 'sin2xsin3y'
                        # also need to handle stuff like 1/2()
                        token = op.implicitMultPrefix
                    case Value(), Value() | Expression():
                        token = op.implicitMult
                match token:
                    case Operator() if token.power[0] <= power: return L, index - 1
                    case Prefix():
                        L, index = evaluate(power=token.power[1], index=index+1, skipEval=skipEval)
                        L = tryOperate(L)
                    case Ternary():
                        if token == op.ternary_else:
                            raise ParseError("Unexpected operator ' : '", self.parsedPos[index])
                        from number import zero
                        ternaryIndex = index
                        if not skipEval: isTrue = op.eq.function(L, zero) == zero
                        trueVal, index = evaluate(power=token.power[1], index=index+1, skipEval=skipEval or not isTrue)
                        if self.parsed[index + 1] != op.ternary_else: raise ParseError("Missing else clause ':' for ternary operator", self.parsedPos[ternaryIndex])
                        falseVal, index = evaluate(power=op.ternary_else.power[1], index=index+2, skipEval=skipEval or isTrue)
                        if not skipEval: L = trueVal if isTrue else falseVal
                    case Postfix():
                        L = tryOperate(L)
                    case op.assignment | op.lambdaArrow:
                        if not isinstance(L, LValue) and not skipEval: raise ParseError(f"Invalid LValue for operator '{token.name}'", self.parsedPos[index - 1])
                        oldIndex = index
                        if isinstance(L, LFunc) or token == op.lambdaArrow:  # create a function
                            closure = mem.copy()
                            if token == op.lambdaArrow:
                                funcName = None
                                if not isinstance(L, LTuple):  # build a tuple with this
                                    innerExpr = self.morphCopy(Expression)
                                    innerExpr.brackets = ''
                                    innerExpr.tokens = self.parsed[index - 1: index]
                                    innerExpr.tokenPos = self.parsedPos[index - 1: index]
                                    funcParams = LTuple(innerExpr)
                                else:
                                    funcParams = L
                            else:
                                funcName, funcParams = L.name, L.params
                            if isinstance(closureExpression := self.parsed[index + 1], Closure):
                                oldIndex += 1
                                index += 1
                                closureExpression.value(closure)  # populate closure with the expressions inside it.
                            _dummy_, index = evaluate(power=token.power[1], index = index + 1, skipEval=True)
                            expr = self.morphCopy()
                            expr.brackets = ''
                            expr.tokens = self.parsed[oldIndex + 1: index + 1]
                            expr.tokenPos = self.parsedPos[oldIndex + 1: index + 1]
                            expr.inputStr = expr.inputStr[expr.tokenPos[0][0]: expr.tokenPos[-1][1]]
                            toAssign = Function(funcName, funcParams, expr, closure)
                        elif isinstance(L, LValue):
                            toAssign, index = evaluate(power=token.power[1], index = index + 1, skipEval=skipEval)
                        else: toAssign = None
                        L = tryOperate(L, toAssign, mem=mem)
                        # f(x) = g(y) = x + y
                        # handle LFunc and WordTokens differently.
                        # - LFunc: save the following Expression without evaluating it.
                        # - WordToken: save the VALUE of the following Expression.
                    case Infix():
                        from number import zero, one
                        oldIndex = index
                        exp, index = evaluate(power=token.power[1], index = index + 1 - (token in [op.implicitMult, op.implicitMultPrefix, op.functionInvocation]), skipEval = skipEval or token == op.logicalAND and op.eq.function(L, zero) == one or token == op.logicalOR and op.eq.function(L, zero) == zero)
                        if isinstance(exp, LValue): raise ParseError(f"Invalid operation on LValue", self.parsedPos[oldIndex])
                        L = tryOperate(L, exp)
                    case None:
                        return L, index - 1
                index += 1


        self.parsed = self.tokens + [None, None]
        self.parsedPos = self.tokenPos + [(9999, 9999), (9999, 9999)]
        return evaluate()[0]


    def __str__(self):
        # from number import RealNumber
        s = ''
        for token in self.tokens:
            s += token.fromString if hasattr(token, 'fromString') else str(token)
        if self.brackets:
            s = self.brackets[0] + s + self.brackets[-1]
        return s

    def __repr__(self): return f"Expression('{str(self)}')"


class Closure(Expression):

    def __repr__(self): return f"Closure('{str(self)}')"