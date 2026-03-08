import sys
import random
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Signal, Slot, QTimer


class AssistantBackend(QObject):
    stateChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self._state = "idle"

        # Simulate random state change every 5 sec (for testing)
        self.timer = QTimer()
        self.timer.timeout.connect(self.random_state)
        self.timer.start(5000)

    def random_state(self):
        self._state = random.choice(["idle", "listening", "thinking"])
        self.stateChanged.emit(self._state)

    @Slot(str)
    def setState(self, new_state):
        self._state = new_state
        self.stateChanged.emit(self._state)


app = QApplication(sys.argv)
engine = QQmlApplicationEngine()

backend = AssistantBackend()
engine.rootContext().setContextProperty("backend", backend)

engine.load("main.qml")

if not engine.rootObjects():
    sys.exit(-1)

sys.exit(app.exec())