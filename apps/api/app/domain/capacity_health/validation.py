"""Guard effort evidence against duplicate consumption and conflicting final totals."""
from .forecast import number


def validate_effort_evidence(tasks, ledger, cases, dependencies, release, snapshot_at):
    task_index = {t['id']: t for t in tasks}
    if len(task_index) != len(tasks):
        raise ValueError('Task IDs must be unique')
    references = {'support': {c['id'] for c in cases},
                  'technical_enablement': {d['id'] for d in dependencies},
                  'release_regression': {release['release_id']} if release else set()}
    totals = {tid: number(0) for tid in task_index}
    ids = set()
    for entry in ledger['time_entries']:
        if entry['id'] in ids:
            raise ValueError('Time entry IDs must be unique')
        ids.add(entry['id'])
        hours = number(entry['hours'])
        if hours <= 0 or entry['timestamp'] > snapshot_at:
            raise ValueError('Time entries need positive hours within the observation window')
        if 'task_id' in entry:
            if entry['task_id'] not in task_index or 'category' in entry or 'reference_id' in entry:
                raise ValueError('Task time must reference one Task only')
            task = task_index[entry['task_id']]
            if not task['created_at'] <= entry['timestamp'] <= (task['completed_at'] or snapshot_at):
                raise ValueError('Task time must occur within the Task lifetime')
            totals[task['id']] += hours
        else:
            if entry['category'] not in references or entry['reference_id'] not in references[entry['category']]:
                raise ValueError('Non-delivery time requires a known evidence reference')
            if entry['category'] == 'release_regression' and entry['discipline'] != 'QA':
                raise ValueError('Regression is QA effort')
            if entry['category'] == 'support':
                case = next(c for c in cases if c['id'] == entry['reference_id'])
                entered = [e['timestamp'] for e in case['events'] if e['event_type'] == 'entered_sprint']
                if entry['timestamp'] < case['received_at'] or (entered and entry['timestamp'] >= min(entered)):
                    raise ValueError('Support effort must precede formal sprint-work entry')
    for tid, total in totals.items():
        if total != number(task_index[tid]['completed_hours']):
            raise ValueError('Task time entries must reconcile with authoritative completed hours')
    observed = set()
    for observation in ledger['task_remaining_observations']:
        tid = observation['task_id']
        if observation['id'] in observed or tid not in task_index:
            raise ValueError('Remaining observations require unique IDs and known Tasks')
        observed.add(observation['id'])
        if number(observation['remaining_hours']) < 0:
            raise ValueError('Remaining effort cannot be negative')
        if not task_index[tid]['created_at'] <= observation['timestamp'] <= snapshot_at:
            raise ValueError('Remaining observations must be inside the Task observation window')
