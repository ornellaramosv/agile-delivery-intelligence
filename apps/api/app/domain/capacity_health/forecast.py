"""Evidence-based forecasts. Fractions preserve precision until API formatting."""
from fractions import Fraction


def number(value):
    return Fraction(str(value))


def support_forecast(history, discipline, planning_open):
    missing = {'forecast_hours': None, 'forecast_status': 'insufficient_history',
               'forecasted_new_cases': None, 'expected_hours_per_case': None}
    if not history or any(not p['evidence_complete'] for p in history):
        return missing
    weights = [number(p['recency_weight']) for p in history]
    if sum(weights) != 1 or any(w <= 0 for w in weights):
        raise ValueError('History weights must be positive and sum to one')
    populations = [[c for c in p['cases'] if c['case_class'] == 'standard'] for p in history]
    count = sum(len(cases) * w for cases, w in zip(populations, weights))
    observed = [(cases, w) for cases, w in zip(populations, weights) if cases]
    if len(observed) != len(history) or any(discipline not in c['actual_hours'] for cases, _ in observed for c in cases):
        return {**missing, 'forecasted_new_cases': count}
    # Preserve the approved weights: a zero-case period has no measurable hours/case.
    effort = sum(sum(number(c['actual_hours'][discipline]) for c in cases) / len(cases) * w
                 for cases, w in observed)
    return {'forecast_hours': count * effort + number(planning_open),
            'forecast_status': 'calculated', 'forecasted_new_cases': count,
            'expected_hours_per_case': effort}


def regression_forecast(history, release, discipline):
    if not release or discipline != 'QA':
        return {'forecast_hours': number(0), 'forecast_status': 'not_applicable'}
    if not history or any(p['scope_count'] <= 0 for p in history):
        return {'forecast_hours': None, 'forecast_status': 'insufficient_history'}
    weights = [number(p['recency_weight']) for p in history]
    if sum(weights) != 1 or any(w <= 0 for w in weights):
        raise ValueError('History weights must be positive and sum to one')
    per_item = sum(number(p['actual_qa_hours']) / p['scope_count'] * w
                   for p, w in zip(history, weights))
    return {'forecast_hours': per_item * len(release['scope']), 'forecast_status': 'calculated'}
