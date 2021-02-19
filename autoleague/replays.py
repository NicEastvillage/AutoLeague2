from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any

import requests
from rlbottraining.history.metric import Metric
from watchdog.events import LoggingEventHandler
from watchdog.observers import Observer


class ReplayPreference(Enum):
    NONE = 'none'  # Ignore replays
    SAVE = 'save'  # Save in replays directory
    CALCULATED_GG = 'calculated_gg'  # Save in replays directory and also upload to https://calculated.gg/


def upload_to_calculated_gg(replay_path: Path):
    with open(replay_path, 'rb') as f:
        response = requests.post('https://calculated.gg/api/upload', files={'replays': f})
        print(f'upload response to {replay_path.name}: {response}')


@dataclass
class ReplayData:
    replay_path: Path = None
    replay_id: str = None


def parse_replay_id(replay_path: Path) -> str:
    replay_id, extension = replay_path.name.split('.')
    assert extension == 'replay'
    return replay_id


@dataclass
class ReplayMonitor(Metric):

    replay_preference: ReplayPreference

    replay_path: Path = None
    replay_id: str = None
    observer: Observer = None

    def to_json(self) -> Dict[str, Any]:
        return {
            'replay_id': self.replay_id,
            'replay_path': self.replay_path,
        }

    def replay_data(self) -> ReplayData:
        return ReplayData(
            replay_id=self.replay_id,
            replay_path=self.replay_path,
        )

    def ensure_monitoring(self):
        if self.observer is not None:
            return
        replay_monitor = self
        class SetReplayId(LoggingEventHandler):
            def on_modified(set_replay_id_self, event):
                if event.is_directory: return
                assert event.src_path.endswith('.replay')
                nonlocal replay_monitor
                replay_path = Path(event.src_path)
                if replay_monitor.replay_preference == ReplayPreference.CALCULATED_GG:
                    upload_to_calculated_gg(replay_path)
                replay_monitor.replay_id = parse_replay_id(replay_path)
                replay_monitor.replay_path = replay_path

            def on_created(self, event):
                pass
            def on_deleted(self, event):
                pass
            def on_moved(self, event):
                pass

        self.observer = Observer()
        self.observer.daemon = True
        self.observer.schedule(SetReplayId(), str(get_replay_dir()), recursive=True)
        self.observer.start()

    def stop_monitoring(self):
        self.observer.stop()
        self.observer.join(1)


def get_replay_dir() -> Path:
    possibilities = [
        Path.home() / 'documents' / 'My Games' / 'Rocket League' / 'TAGame' / 'Demos',
        Path.home() / 'OneDrive' / 'documents' / 'My Games' / 'Rocket League' / 'TAGame' / 'Demos'
    ]
    for path in possibilities:
        if path.exists():
            return path
    raise FileExistsError("Could not find replay directory!")
