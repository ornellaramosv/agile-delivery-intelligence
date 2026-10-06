"""Deterministic Capacity Health from dated facts; no I/O or framework dependency."""
from datetime import datetime
from fractions import Fraction

from app.domain.delivery_flow import calculate_delivery_flow
from .capacity import capacity_result, primary_answer
from .forecast import number, regression_forecast, support_forecast
from .validation import validate_effort_evidence

DISCIPLINES = ('DEV', 'QA')
EFFORT_CATEGORY = {'planned': 'baseline_delivery', 'rework': 'rework', 'scope_added': 'post_planning_scope'}
CATEGORIES = (*EFFORT_CATEGORY.values(), 'support', 'release_regression', 'technical_enablement')


def support_history(periods):
    """Expose chronological standard-case evidence without altering forecasts."""
    history = []
    for period in sorted(periods, key=lambda p: (p['start_date'], p['sprint_id'])):
        standard = [case for case in period['cases'] if case['case_class'] == 'standard']
        actual = {}
        for case in standard:
            for discipline, hours in case['actual_hours'].items():
                key = discipline.upper()
                actual[key] = actual.get(key, number(0)) + number(hours)
        history.append({'sprint_id': period['sprint_id'],
                        'recency_weight': period['recency_weight'],
                        'standard_case_count': len(standard), 'actual_hours': actual})
    return history


def latest(rows, cutoff, default):
    observed = [r for r in rows if r['timestamp'] <= cutoff]
    return max(observed, key=lambda r: (r['timestamp'], r.get('id', ''))) if observed else default


def closed(case, cutoff):
    return any(e['event_type'] == 'engineering_closed' and e['timestamp'] <= cutoff for e in case['events'])


def support_remaining(case, cutoff, discipline, baseline_at):
    if case['received_at'] > cutoff or closed(case, cutoff):
        return number(0)
    # After formal entry, remaining work belongs to the linked sprint tasks.
    if any(e['event_type'] == 'entered_sprint' and e['timestamp'] <= cutoff for e in case['events']):
        return number(0)
    opening = case['planning_remaining_hours'] if case['received_at'] <= baseline_at else {'DEV': 0, 'QA': 0}
    return number(latest(case['remaining_observations'], cutoff, {'remaining_hours': opening})['remaining_hours'][discipline])


def release_state(release, cases, events, cutoff, dependencies, active_ids):
    if not release:
        return {'status': 'not_applicable', 'ready_for_regression': None, 'summary': None}
    states = {}
    for event in sorted(events, key=lambda e: (e['timestamp'], e['id'])):
        if event['timestamp'] <= cutoff and event['to_state'] and event['from_state'] != event['to_state']:
            states[event['work_item_id']] = event['to_state']
    scope = []
    for item in release['scope']:
        is_closed = item['closed_at'] <= cutoff if 'closed_at' in item else states.get(item['work_item_id']) == 'Closed'
        scope.append({**item, 'closed': is_closed})
    case_index = {c['id']: c for c in cases}
    case_states = [{'case_id': cid, 'engineering_closed': closed(case_index[cid], cutoff)} for cid in release['customer_case_ids']]
    started = [e for e in release['events'] if e['timestamp'] <= cutoff and e['event_type'] == 'regression_started']
    completed = [e for e in release['events'] if e['timestamp'] <= cutoff and e['event_type'] == 'regression_completed']
    ready = all(i['closed'] for i in scope) and all(c['engineering_closed'] for c in case_states)
    scope_ids = {s['work_item_id'] for s in scope}
    required = [item for item in scope if item['work_item_id'] in active_ids]
    closed_count = sum(item['closed'] for item in scope)
    required_closed = sum(item['closed'] for item in required)
    cases_closed = sum(case['engineering_closed'] for case in case_states)
    summary = {
        'total_scope_items': len(scope),
        'closed_scope_items': closed_count,
        'pending_scope_items': len(scope) - closed_count,
        'current_sprint_required_total': len(required),
        'current_sprint_required_closed': required_closed,
        'current_sprint_required_pending': len(required) - required_closed,
        'included_customer_cases_total': len(case_states),
        'included_customer_cases_engineering_closed': cases_closed,
        'included_customer_cases_pending': len(case_states) - cases_closed,
    }
    return {'release_id': release['release_id'], 'previous_release_id': release['previous_release_id'],
            'status': 'applicable', 'ready_for_regression': ready, 'scope': scope, 'customer_cases': case_states,
            'summary': summary,
            'current_sprint_required_ids': sorted(scope_ids & set(active_ids)),
            'current_sprint_future_release_ids': sorted(set(active_ids) - scope_ids),
            'regression_phase': 'completed' if completed else 'in_progress' if started else 'not_started',
            'regression_event_ids': [e['id'] for e in started + completed],
            'qa_available_for_certification': bool(completed),
            'dependency_context_ids': [d['id'] for d in dependencies if d['opened_at'] <= cutoff],
            'dependencies_are_readiness_gates': False}


def calculate_capacity_health(*, sprint, work_items, tasks, events, capacity_plan,
                              capacity_ledger, task_capacity_map, dependencies,
                              scope_decisions, release_regression, support_cases,
                              regression_history, sprint_day=None, comparison='since_planning',
                              mode='current_sprint'):
    days = sprint['working_days']
    last_day = len(days)
    selected = last_day if sprint_day is None else sprint_day
    if type(selected) is not int or not 1 <= selected <= last_day:
        raise ValueError('sprint_day must identify a sprint working day')
    if comparison not in ('since_planning', 'since_previous_working_day'):
        raise ValueError('Unsupported comparison')
    if mode not in ('current_sprint', 'retrospective'):
        raise ValueError('Unsupported mode')
    flow = calculate_delivery_flow(sprint=sprint, work_items=work_items, events=events)
    discipline_map = {r['task_id']: r['discipline'] for r in task_capacity_map}
    task_index = {t['id']: t for t in tasks}
    if set(discipline_map) != set(task_index) or len(discipline_map) != len(task_capacity_map):
        raise ValueError('Every task must have exactly one discipline mapping')
    if set(discipline_map.values()) - set(DISCIPLINES):
        raise ValueError('Unsupported discipline')
    cases = support_cases['current_cases']
    validate_effort_evidence(tasks, capacity_ledger, cases, dependencies, release_regression, sprint['snapshot_at'])
    planning_at = sprint['baseline_at']
    forecasts = {}
    for d in DISCIPLINES:
        opening = sum(support_remaining(c, planning_at, d, planning_at) for c in cases if c['case_class'] == 'standard')
        forecasts[d] = {'support': support_forecast(support_cases['historical_sprints'], d, opening),
                        'regression': regression_forecast(regression_history, release_regression, d)}

    def cutoff(day):
        return planning_at if day == 0 else days[day - 1]['date'] + 'T18:00:00Z'

    def scope(day):
        return set(sprint['original_baseline_work_item_ids']) if day == 0 else set(flow['daily_snapshots'][day-1]['story_states'])

    def snapshot(day):
        at = cutoff(day)
        active = scope(day)
        by_discipline = {}
        entries = [e for e in capacity_ledger['time_entries'] if e['timestamp'] <= at and day > 0]
        for d in DISCIPLINES:
            actual = {cat: number(0) for cat in CATEGORIES}
            for entry in entries:
                if 'task_id' in entry:
                    if discipline_map[entry['task_id']] != d:
                        continue
                    category = EFFORT_CATEGORY[task_index[entry['task_id']]['effort_kind']]
                else:
                    if entry['discipline'] != d:
                        continue
                    category = entry['category']
                actual[category] += number(entry['hours'])
            remaining = {kind: number(0) for kind in EFFORT_CATEGORY.values()}
            for task in tasks:
                if discipline_map[task['id']] != d or task['work_item_id'] not in active or task['created_at'] > at:
                    continue
                category = EFFORT_CATEGORY[task['effort_kind']]
                if day == last_day:
                    # Frozen final Task values remain authoritative, never inferred from estimates.
                    rem = number(task['remaining_hours'])
                elif task['completed_at'] and task['completed_at'] <= at:
                    rem = number(0)
                else:
                    observations = [o for o in capacity_ledger['task_remaining_observations'] if o['task_id'] == task['id']]
                    rem = number(latest(observations, at, {'remaining_hours': task['estimated_hours']})['remaining_hours'])
                remaining[category] += rem
            if day == last_day:
                for kind, category in EFFORT_CATEGORY.items():
                    actual[category] = sum(number(t['completed_hours']) for t in tasks
                                           if discipline_map[t['id']] == d and t['effort_kind'] == kind)
            support_known = sum(support_remaining(c, at, d, planning_at) for c in cases if c['case_class'] == 'standard')
            critical_known = sum(support_remaining(c, at, d, planning_at) for c in cases if c['case_class'] == 'critical')
            standard_case_ids = {c['id'] for c in cases if c['case_class'] == 'standard'}
            standard_actual = sum(number(e['hours']) for e in entries if e.get('category') == 'support'
                                  and e['reference_id'] in standard_case_ids and e['discipline'] == d)
            regression_known = number(latest(release_regression['remaining_observations'], at,
                                            {'remaining_hours': 0})['remaining_hours']) if release_regression and d == 'QA' else number(0)
            technical_known = sum(number(latest(dep['remaining_observations'], at,
                                               {'remaining_hours': {'DEV': 0, 'QA': 0}})['remaining_hours'][d])
                                  for dep in dependencies if dep['opened_at'] <= at and
                                  (dep['resolved_at'] is None or dep['resolved_at'] > at))
            gross = sum(number(row['gross_hours'][d]) for row in capacity_plan['daily_schedule'])
            future = sum(number(row['gross_hours'][d]) for row in capacity_plan['daily_schedule'] if row['sprint_day'] > day)
            support_reserve = number(capacity_plan['reserves'][d]['support_hours'])
            regression_reserve = number(capacity_plan['reserves'][d]['regression_hours']) if release_regression and d == 'QA' else number(0)
            def variance(kind, reserve, consumed):
                forecast = forecasts[d][kind]['forecast_hours']
                return {**forecasts[d][kind], 'reserved_hours': reserve, 'actual_hours': consumed,
                        'reserve_vs_forecast_hours': None if forecast is None else reserve - forecast,
                        'actual_vs_reserve_hours': consumed - reserve,
                        'actual_vs_forecast_hours': None if forecast is None else consumed - forecast}
            total_remaining = sum(remaining.values())
            by_discipline[d] = {
                'gross_capacity_hours': gross,
                'planned_product_capacity_hours': gross - support_reserve - regression_reserve,
                'support': {**variance('support', support_reserve, standard_actual),
                            'critical_actual_hours': actual['support'] - standard_actual},
                'regression': variance('regression', regression_reserve, actual['release_regression']),
                'consumption': {**{cat + '_hours': value for cat, value in actual.items()}, 'total_hours': sum(actual.values())},
                'remaining_delivery': {'baseline_hours': remaining['baseline_delivery'], 'rework_hours': remaining['rework'],
                                       'post_planning_scope_hours': remaining['post_planning_scope'], 'total_hours': total_remaining},
                'capacity': capacity_result(future=future, delivery=total_remaining,
                                            support_forecast=forecasts[d]['support']['forecast_hours'], support_actual=standard_actual,
                                            support_known=support_known, regression_forecast=forecasts[d]['regression']['forecast_hours'],
                                            regression_actual=actual['release_regression'], regression_known=regression_known,
                                            technical_known=technical_known, critical_known=critical_known)}
        return {'sprint_day': day, 'timestamp': at, 'disciplines': by_discipline,
                'primary_answer': primary_answer(by_discipline)}

    planning = snapshot(0)
    daily = [snapshot(day) for day in range(1, selected + 1)]
    current = daily[-1]
    at = cutoff(selected)
    baseline = set(sprint['original_baseline_work_item_ids'])
    active = scope(selected)
    added = active - baseline
    story_states = flow['daily_snapshots'][selected - 1]['story_states']

    def progress(ids, include_rate=True):
        closed_count = sum(story_states.get(item_id) == 'Closed' for item_id in ids)
        result = {'total': len(ids), 'closed': closed_count, 'open': len(ids) - closed_count}
        if include_rate:
            result['completion_rate'] = number(closed_count) / len(ids) if ids else None
        return result

    sprint_progress = {'original_baseline': progress(baseline),
                       'current_scope': progress(active),
                       'post_planning_scope': progress(added, include_rate=False)}
    def task_total(ids, field, discipline=None):
        return sum(number(t[field]) for t in tasks if t['work_item_id'] in ids
                   and (discipline is None or discipline_map[t['id']] == discipline)
                   and (t['effort_kind'] != 'rework'))
    baseline_est = task_total(baseline, 'estimated_hours')
    added_est = task_total(added, 'estimated_hours')
    added_actual = sum(r['consumption']['post_planning_scope_hours'] for r in current['disciplines'].values())
    def ratio(a, b):
        return a / b if b else None
    scope_change = {'original_baseline_items': len(baseline), 'added_items': len(added), 'added_work_item_ids': sorted(added),
                    'item_rate': ratio(number(len(added)), len(baseline)), 'baseline_estimated_hours': baseline_est,
                    'added_estimated_hours': added_est, 'added_actual_hours': added_actual,
                    'effort_rate': ratio(added_est, baseline_est),
                    'by_discipline': {d: {'baseline_estimated_hours': task_total(baseline, 'estimated_hours', d),
                                           'added_estimated_hours': task_total(added, 'estimated_hours', d),
                                           'effort_rate': ratio(task_total(added, 'estimated_hours', d), task_total(baseline, 'estimated_hours', d))}
                                      for d in DISCIPLINES},
                    'decision_evidence': [r for r in scope_decisions if r['timestamp'] <= at]}
    dependency_results = []
    for dep in dependencies:
        if dep['opened_at'] > at:
            continue
        end = min(dep['resolved_at'] or at, at)
        elapsed = number((datetime.fromisoformat(end) - datetime.fromisoformat(dep['opened_at'])).total_seconds()) / 3600
        dep_entries = [e for e in capacity_ledger['time_entries'] if e.get('reference_id') == dep['id'] and e['timestamp'] <= at]
        dependency_results.append({'id': dep['id'], 'type': dep['type'], 'owner': dep['owner'], 'work_item_ids': dep['work_item_ids'],
                                   'opened_at': dep['opened_at'], 'resolved_at': dep['resolved_at'] if dep['resolved_at'] and dep['resolved_at'] <= at else None,
                                   'elapsed_open_hours': elapsed, 'technical_actual_hours': sum(number(e['hours']) for e in dep_entries),
                                   'time_entry_ids': [e['id'] for e in dep_entries]})
    case_results = []
    for case in cases:
        if case['received_at'] > at:
            continue
        case_entries = [e for e in capacity_ledger['time_entries'] if e.get('reference_id') == case['id'] and e['timestamp'] <= at]
        case_results.append({'case_id': case['id'], 'case_class': case['case_class'],
                             'engineering_closed': closed(case, at),
                             'customer_closed': bool(case['customer_closed_at'] and case['customer_closed_at'] <= at),
                             'linked_work_item_id': case['linked_work_item_id'] if case['linked_work_item_id'] in active else None,
                             'events': [e for e in case['events'] if e['timestamp'] <= at],
                             'actual_hours': {d: sum(number(e['hours']) for e in case_entries if e['discipline'] == d) for d in sorted(set(DISCIPLINES) | {e['discipline'] for e in case_entries})},
                             'time_entry_ids': [e['id'] for e in case_entries]})
    critical = [{**c, 'active': not c['engineering_closed'], 'context': 'Critical disruption active' if not c['engineering_closed'] else 'Critical disruption completed'}
                for c in case_results if c['case_class'] == 'critical']
    facts = []
    def fact(timestamp, kind, evidence_id, **detail):
        if planning_at < timestamp <= at:
            facts.append({'timestamp': timestamp, 'kind': kind, 'evidence_id': evidence_id, **detail})
    for event in events:
        if event['event_type'] == 'scope_added' or (event['from_state'] == 'QA' and event['to_state'] == 'Returned to DEV'):
            fact(event['timestamp'], 'post_planning_scope' if event['event_type'] == 'scope_added' else 'rework',
                 event['id'], work_item_id=event['work_item_id'])
    for entry in capacity_ledger['time_entries']:
        category = EFFORT_CATEGORY[task_index[entry['task_id']]['effort_kind']] if 'task_id' in entry else entry['category']
        fact(entry['timestamp'], 'effort_recorded', entry['id'], category=category, hours=number(entry['hours']),
             discipline=discipline_map[entry['task_id']] if 'task_id' in entry else entry['discipline'],
             reference_id=entry.get('task_id', entry.get('reference_id')))
    for observation in capacity_ledger['task_remaining_observations']:
        fact(observation['timestamp'], 'remaining_delivery_observed', observation['id'],
             task_id=observation['task_id'], remaining_hours=number(observation['remaining_hours']))
    if selected == last_day:
        for task in tasks:
            fact(sprint['snapshot_at'], 'remaining_delivery_observed', task['id'],
                 task_id=task['id'], remaining_hours=number(task['remaining_hours']),
                 source='frozen tasks.json final observation')
    for dep in dependencies:
        fact(dep['opened_at'], 'dependency_opened', dep['id'])
        if dep['resolved_at']:
            fact(dep['resolved_at'], 'dependency_resolved', dep['id'])
    for case in cases:
        for event in case['events']:
            kind = 'critical_disruption' if case['case_class'] == 'critical' and event['event_type'] == 'received' else 'support_' + event['event_type']
            fact(event['timestamp'], kind, event['id'], case_id=case['id'])
    if release_regression:
        for event in release_regression['events']:
            fact(event['timestamp'], event['event_type'], event['id'])
    facts.sort(key=lambda e: (e['timestamp'], e['evidence_id'], e['kind']))
    previous = planning if comparison == 'since_planning' or selected == 1 else daily[-2]
    changes = {d: {'remaining_delivery_change_hours': current['disciplines'][d]['remaining_delivery']['total_hours'] - previous['disciplines'][d]['remaining_delivery']['total_hours'],
                   'consumption_change_hours': {k: v - previous['disciplines'][d]['consumption'][k] for k, v in current['disciplines'][d]['consumption'].items()}}
               for d in DISCIPLINES}
    breakpoints = [f for f in facts if f['kind'] in ('rework', 'post_planning_scope', 'regression_started', 'regression_completed',
                                                    'dependency_opened', 'dependency_resolved', 'critical_disruption')]
    for before, after in zip([planning] + daily, daily):
        for d in DISCIPLINES:
            old = before['disciplines'][d]['capacity']['capacity_gap_hours']
            new = after['disciplines'][d]['capacity']['capacity_gap_hours']
            if old is not None and new is not None and (old < 0) != (new < 0):
                breakpoints.append({'timestamp': after['timestamp'], 'kind': 'capacity_gap_crossing', 'discipline': d,
                                    'previous_gap_hours': old, 'capacity_gap_hours': new, 'sprint_day': after['sprint_day']})
    breakpoints.sort(key=lambda e: (e['timestamp'], e['kind']))
    return {'sprint': {k: sprint[k] for k in ('id', 'name', 'project', 'backlog', 'start_date', 'end_date')},
            'mode_context': {'mode': mode, 'comparison': comparison, 'sprint_day': selected, 'snapshot_at': at,
                             'comparison_at': previous['timestamp'], 'primary_answer': current['primary_answer']},
            'planning': {'snapshot_at': planning_at, 'disciplines': planning['disciplines']},
            'disciplines': current['disciplines'], 'daily_capacity': daily,
            'release_readiness': release_state(release_regression, cases, events, at, dependencies, active),
            'scope_change': scope_change, 'sprint_progress': sprint_progress,
            'support': {'history': support_history(support_cases['historical_sprints']),
                        'cases': case_results, 'excluded_critical_history_ids': [c['id'] for period in support_cases['historical_sprints']
                                                                              for c in period['cases'] if c['case_class'] == 'critical']},
            'dependencies': {'items': dependency_results, 'duration_unit': 'elapsed calendar hours; not effort'},
            'critical_disruptions': critical,
            'what_changed': {'comparison': comparison, 'from_at': previous['timestamp'], 'to_at': at,
                             'by_discipline': changes, 'facts': [f for f in facts if f['timestamp'] > previous['timestamp']]},
            'retrospective_breakpoints': breakpoints,
            'insights': [{'kind': 'capacity_answer', **current['primary_answer']}]}


def api_values(value, key=''):
    """Only the response boundary rounds; domain values retain exact precision."""
    if isinstance(value, dict):
        return {k: api_values(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [api_values(v, key) for v in value]
    if isinstance(value, Fraction):
        return float(round(value, 4 if key.endswith('_rate') or key == 'capacity_pressure' else 2))
    return value
