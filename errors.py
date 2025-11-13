class CalculatorError(Exception):
    def __init__(self, errorMsg='Calculator Error!', *args):
        super().__init__(errorMsg, *args)
        # self.message = errorMsg

class VariableError(CalculatorError):
    def __init__(self, errorMsg='Variable error!', *args):
        super().__init__(errorMsg, *args)

class EvaluationError(CalculatorError):
    def __init__(self, errorMsg='Evaluation error!', *args):
        super().__init__(errorMsg, *args)

class NumberError(CalculatorError):
    def __init__(self, errorMsg='Number error!', *args):
        super().__init__(errorMsg, *args)

class ParseError(CalculatorError):
    def __init__(self, errorMsg='Parse error!', *args):
        super().__init__(errorMsg, *args)

class SettingsError(CalculatorError):
    def __init__(self, errorMsg='Settings error!', *args):
        super().__init__(errorMsg, *args)
