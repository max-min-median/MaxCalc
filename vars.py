from errors import EvaluationError


class Value:
    def __init__(self, name='<Value>', value=None):
        self.name = name
        self._value = value

    def __str__(self):
        return self.name

    def __repr__(self): return str(self)

    def __len__(self): return 1

    def disp(self, fracMaxLength, finalPrecision):
        return str(self)
    
    def morphCopy(self, cls=None):  # makes a copy of the object, optionally changing its class
        if cls is None: cls = type(self)
        cpy = cls.__new__(cls)
        cpy.__dict__.update(self.__dict__)
        return cpy

    def value(self, *args, **kwargs):
        raise NotImplementedError(f'subclass {type(self)} has no implementation of value()')


class Var(Value):
    def __init__(self, name):
        super().__init__(name=name)

    def value(self, *args, mem=None, **kwargs):
        if mem is None: raise EvaluationError(f"No memory provided to Var object '{self.name}'")
        val = mem.get(self.name)
        if val is None: raise EvaluationError(f"Variable '{self.name}' not found in memory!")
        return val


class LValue(Value):  # variable ready for assignment. Has NO value
    def __init__(self, name='<lValue>', value=None):
        super().__init__(name=name, value=value)

    def value(self, *args, **kwargs):
        return self

    def makeVar(self, value=None):
        if value is None: raise ValueError(f'No value to assign to "{self.name}"')
        return Var(name=self.name, value=value)