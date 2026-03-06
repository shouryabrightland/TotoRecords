from enum import Enum

from modules.Logging import Log

class AssistantState(Enum):
    IDLE = 0
    LISTENING = 1
    THINKING = 2
    SPEAKING = 4
    ERROR = 5
    LOADING = 6


class AssistantCore:

    def __init__(self,initial_state=AssistantState.IDLE):
        self.current_state = initial_state
        self.listeners = []
        self.Active_state = []  # store job identifiers
        self.log = Log("AssistantCore", Log.INFO,"AssistentCore.log")
        self.log.info("AssistantCore Initialized in state",initial_state.name)

    def start_state(self, state):
        self.Active_state.append(state)
        self.current_state = state
        self.log.info(f"[STATE] → {state.name}")
        self.log.info(f"current State --> {self.get_state()}")

        for callback in self.listeners:
            callback(state,True)
    
    def end_state(self, state):
        try:
            self.Active_state.remove(state)
        except ValueError:
            self.log.error(f"Attempted to end state {state.name} which is not active.")
            return
        self.current_state = self.Active_state[-1] if self.Active_state else AssistantState.IDLE
        self.log.info(f"[STATE] ← {state.name}")
        self.log.info(f"current State --> {self.get_state()}")
        for callback in self.listeners:
            callback(state,False)
    
    def get_state(self):
        return self.current_state

    def on_state_change(self, callback):
        self.listeners.append(callback)

