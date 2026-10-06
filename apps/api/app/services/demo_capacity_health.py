"""Repository-relative fixture loading and API formatting for Capacity Health."""
import json
from pathlib import Path

from app.domain.capacity_health import calculate_capacity_health
from app.domain.capacity_health.engine import api_values

DATA_PATH = Path(__file__).resolve().parents[4] / 'data' / 'demo'


def load_capacity_inputs():
    files = {'sprint': 'sprint', 'work_items': 'work-items', 'tasks': 'tasks', 'events': 'delivery-events',
             'capacity_plan': 'capacity-plan', 'capacity_ledger': 'capacity-ledger', 'task_capacity_map': 'task-capacity-map',
             'dependencies': 'dependencies', 'scope_decisions': 'scope-decisions', 'release_regression': 'release-regression'}
    inputs = {key: json.loads((DATA_PATH / 'sprint-08' / f'{name}.json').read_text(encoding='utf-8')) for key, name in files.items()}
    for key, name in [('support_cases', 'support-cases'), ('regression_history', 'regression-history')]:
        inputs[key] = json.loads((DATA_PATH / 'capacity-history' / f'{name}.json').read_text(encoding='utf-8'))
    return inputs


def sprint_08_capacity_health(**options):
    return api_values(calculate_capacity_health(**load_capacity_inputs(), **options))
