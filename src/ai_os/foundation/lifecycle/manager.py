from enum import Enum


class LifecycleState(Enum):
    STARTING = "starting"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"


class LifecycleManager:
    def __init__(self):
        self._state = LifecycleState.STOPPED

    def _transition_to(self, new_state: LifecycleState) -> None:
        valid_transitions = {
            LifecycleState.STOPPED: {LifecycleState.STARTING},
            LifecycleState.STARTING: {LifecycleState.READY},
            LifecycleState.READY: {LifecycleState.RUNNING, LifecycleState.STOPPING},
            LifecycleState.RUNNING: {LifecycleState.STOPPING},
            LifecycleState.STOPPING: {LifecycleState.STOPPED},
        }

        if new_state not in valid_transitions[self._state]:
            raise RuntimeError(
                f"Invalid lifecycle transition: "
                f"{self._state.value} -> {new_state.value}"
            )

        self._state = new_state

    def start(self) -> None:
        self._transition_to(LifecycleState.STARTING)
        self._transition_to(LifecycleState.READY)


    def stop(self) -> None:
        self._transition_to(LifecycleState.STOPPING)
        self._transition_to(LifecycleState.STOPPED)

    @property
    def state(self) -> LifecycleState:
        return self._state