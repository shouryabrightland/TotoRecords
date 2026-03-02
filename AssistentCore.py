from enum import Enum

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

    def start_state(self, state):
        self.Active_state.append(state)
        self.current_state = state
        print(f"[STATE] → {state.name}")
        print("current State -->",self.get_state())

        for callback in self.listeners:
            callback(state,True)
    
    def end_state(self, state):
        self.Active_state.remove(state)
        self.current_state = self.Active_state[-1] if self.Active_state else AssistantState.IDLE
        print(f"[STATE] ← {state.name}")
        for callback in self.listeners:
            callback(state,False)
        print("current State -->",self.get_state())
    
    def get_state(self):
        return self.current_state

    def on_state_change(self, callback):
        self.listeners.append(callback)

