from vars import Value
from errors import EvaluationError
import number as N

class String(Value):

    def __init__(self, val):
        self.string = val

    def __str__(self):
        return "\"" + self.string + "\""

    def __len__(self): return len(self.string)

    def value(self, *args, **kwargs):
        return self

    def __add__(self, other):
        # if isinstance(other, (int, float)): other = RealNumber(other)
        return String(self.string + (other.string if isinstance(other, String) else str(other)))

    def __radd__(self, other):
        return String(str(other) + self.string)

    def __neg__(self): raise EvaluationError("Invalid operation on string")
    def __sub__(self, other): raise EvaluationError("Invalid operation on strings")

    def __mul__(self, other):
        if not (isinstance(other, N.RealNumber) and other.isInt()): raise EvaluationError("Can only multiply a string with an integer")
        return String(self.string * int(other))

    __rmul__ = __mul__
    __rsub__ = __truediv__ = __rtruediv__ = __mod__ = __rmod__ = __pow__ = __rpow__ = __floordiv__ = __sub__

    def __gt__(self, other):
        if not isinstance(other, String): raise EvaluationError("Cannot compare string with other types")
        return self.string > other.string

    def __lt__(self, other):
        if not isinstance(other, String): raise EvaluationError("Cannot compare string with other types")
        return self.string < other.string

    def __eq__(self, other):
        if not isinstance(other, String): raise EvaluationError("Cannot compare string with other types")
        return self.string == other.string

    def __ne__(self, other): return not self == other
    def __ge__(self, other): return not self < other
    def __le__(self, other): return not self > other

    def value(self, *args, **kwargs): return self


# test code
if __name__ == '__main__':
    pass