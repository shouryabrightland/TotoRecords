import datetime

class Log:

    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3

    LEVEL_NAMES = {
        DEBUG: "DEBUG",
        INFO: "INFO",
        WARN: "WARN",
        ERROR: "ERROR"
    }

    def __init__(self, name="APP", level=INFO, logfile="Assistent.log"):
        self.name = name
        self.level = level
        self.logfile = logfile

    def _write(self, level, *msg):

        if level < self.level:
            return

        time = datetime.datetime.now().strftime("%H:%M:%S")

        text = f"[{time}] [{self.name}] [{self.LEVEL_NAMES[level]}] " + " ".join(map(str, msg))

        if self.logfile:
            with open(self.logfile, "a") as f:
                f.write(text + "\n")

    def debug(self, *msg):
        self._write(self.DEBUG, *msg)

    def info(self, *msg):
        self._write(self.INFO, *msg)

    def warn(self, *msg):
        self._write(self.WARN, *msg)

    def error(self, *msg):
        self._write(self.ERROR, *msg)