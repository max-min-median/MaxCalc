from errors import SettingsError
import json

class Settings:

    _instance = None

    def __new__(cls, filename=None):
        if cls._instance is None: cls._instance = super().__new__(cls)
        if filename is not None: cls._instance._loadFile(filename)
        return cls._instance

    def _loadFile(self, filename=None):
        from number import RealNumber
        with open(filename) as f: self._settings = json.loads(f.readline())
        self._filename = filename
        self.epsilon = RealNumber(1, 10 ** self._settings['working_precision'], fcf=False)
        self.finalEpsilon = RealNumber(1, 10 * 10 ** self._settings['final_precision'], fcf=False)
        self._version = 0

    def set(self, key, value):
        # if key not in self._settings: raise SettingsError(f"key '{key}' not found in settings")
        self._settings[key] = value
        from number import RealNumber
        if key == 'working_precision':
            self.epsilon = RealNumber(1, 10 ** value, fcf=False)
        elif key == 'final_precision':
            self.finalEpsilon = RealNumber(1, 10 * 10 ** value, fcf=False)
        elif key == 'keyboard':
            from UI import UI
            UI().setupKeyboard()
        with open(self._filename, "w") as f:
            f.write(json.dumps(self._settings))

    def get(self, key):
        if key not in self._settings:
            raise SettingsError(f"key '{key}' not found in settings")
        return self._settings[key]