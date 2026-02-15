import functions as F

class Operator:
    def __init__(self, name='<op>', function=lambda x: 'undefined op'):
        self.name = name
        self.function = function
    
    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    @property
    def power(self):  # binding power for determining precedence
        import op
        return op.power[self] if self in op.power else None

class Prefix(Operator):
    def __init__(self, name='<un_op_l>', function=lambda x: 'undefined un_op_left'):
        super().__init__(name, function)

class PrefixFunction(Prefix):
    def __init__(self, name='<un_op_l_parens>', function=lambda x: 'undefined un_op_left requiring parens'):
        super().__init__(name, function)

class Postfix(Operator):
    def __init__(self, name='<un_op_r>', function=lambda x: 'undefined un_op_right'):
        super().__init__(name, function)

class Infix(Operator):
    def __init__(self, name='<bin_op>', function=lambda x, y: 'undefined bin_op'):
        super().__init__(name, function)

class Ternary(Infix):
    def __init__(self, name='<ternary_op>', function=lambda x, y: 'undefined tern_op'):
        super().__init__(name, function)