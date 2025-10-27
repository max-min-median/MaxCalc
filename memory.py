from number import *
from functions import Function, FuncComposition
import op
from settings import Settings

st = Settings()


class Memory:

    # Base class intended for use by Functions.

    globalMem = None

    baseList = {
        'e': e,
        'pi': pi,
        'i': imag_i,
        'P': op.permutation,   # These are here so that
        'C': op.combination,   # they are overrideable.
    }

    topList = {
        'abs': op.absolute,   # These override user vars
        'arg': op.argument,
        'conj': op.conjugate,
        'Im': op.imPart,
        'Re': op.realPart,
        'sgn': op.signum,
        'sin': op.sin,
        'cosec': op.csc,
        'csc': op.csc,
        'cos': op.cos,
        'sec': op.sec,
        'tan': op.tan,
        'cot': op.cot,
        'sinh': op.sinh,
        'cosh': op.cosh,
        'tanh': op.tanh,
        'asin': op.arcsin,
        'arcsin': op.arcsin,
        'acos': op.arccos,
        'arccos': op.arccos,
        'atan': op.arctan,
        'arctan': op.arctan,
        'sqrt': op.sqrt,
        'ln': op.ln,
        'lg': op.lg,
        'normcdf': op.normcdf,
        'normpdf': op.normpdf,
        'invnorm': op.invnorm,
    }

    def __init__(self, filename=None):
        self.vars = {}

    def get(self, str):
        seq = [Memory.topList, self.vars if self is not Memory.globalMem else {}, Memory.globalMem.vars, Memory.baseList]
        for dct in seq:
            if str in dct: return dct[str]

    def add(self, str, val):
        if isinstance(val, Number): val = val.fastContinuedFraction(epsilon=st.epsilon)
        self.vars[str] = val

    def delete(self, key):  # Functions should never have stuff in their memory deleted
        raise NotImplementedError
    
    def copy(self):
        cpy = Memory()
        cpy.__dict__.update(self.__dict__)
        cpy.vars = self.vars.copy()
        return cpy
    
    def __iter__(self): yield from self.vars

    def __str__(self):
        return "{{" + '; '.join([f"{v}" if isinstance(v, Function) and k == v.name else f"{k} = {v}" for k, v in self.vars.items()]) + "}}"

    def strWithout(self, keyWithout):
        return "{{" + '; '.join([f"{v}" if isinstance(v, Function) and k == v.name else f"{k} = {v}" for k, v in self.vars.items() if k != keyWithout]) + "}}"

    def fullDict(self):
        return Memory.baseList | Memory.globalMem.vars | self.vars | Memory.topList

    # def __getitem__(self, key): return self.get(key)
    # def __setitem__(self, key, value): self.add(key, value)
    # def __delitem__(self, key): self.delete(key)
    

class GlobalMemory(Memory):

    def __init__(self, filepath=None):
        if filepath is None: raise MemoryError("Must specify a memory file.")
        from pathlib import Path
        self.vars = {}
        self.trie = None
        self.filepath = filepath
        self.writeLock = True
        Memory.globalMem = self
        if filepath.exists(): self.load()

    def add(self, string, val, save=True):
        if string == 'ans':
            # if 'ans' in self.vars: self.vars.pop('ans')
            self.vars['ans'] = val
        else:
            if isinstance(val, Number): val = val.fastContinuedFraction(epsilon=st.epsilon)
            needSort = string not in self.vars
            self.vars[string] = val
            if self.trie is not None: self.trie.insert(string)
            if needSort:
                self.vars = {k: self.vars[k] for k in sorted(self.vars, key=lambda x: -isinstance(self.vars[x], Function))}
        if not self.writeLock and save: self.save()

    def delete(self, string):
        strList = string.replace(',', ' ').split()
        deleted = []
        for s in strList:
            if s in self.vars:
                del self.vars[s]
                deleted.append(s)
                if s not in self.baseList:
                    self.trie.delete(s)
        if not self.writeLock and deleted: self.save()
        return deleted

    def copy(self):
        return Memory()  # global returns a blank Memory object when copy is called

    def save(self):
        with open(self.filepath, "w") as f:
            for var, value in self.vars.items():
                if isinstance(value, FuncComposition):
                    f.write(f"{var} = {value.name}\n")
                elif isinstance(value, Function):
                    if var != value.name: f.write(f"{var} = ")
                    f.write(f"{str(value)}\n")
                else:
                    f.write(f"{var} = {value.fromString if hasattr(value, 'fromString') else str(value)}\n")

    def load(self):
        import parser
        with open(self.filepath) as f:
            for line in f:
                parser.parse(line).value(mem=self)
        self.writeLock = False
        self.save()