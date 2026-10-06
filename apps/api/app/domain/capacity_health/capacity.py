"""Capacity arithmetic and the Product Owner-approved missing-evidence decision."""
from .forecast import number


def capacity_result(*, future, delivery, support_forecast, support_actual, support_known,
                    regression_forecast, regression_actual, regression_known, technical_known, critical_known=0):
    def remaining(forecast, actual, known):
        return None if forecast is None else max(forecast - actual, known, number(0))
    support = remaining(support_forecast, support_actual, support_known)
    if support is not None:
        support += critical_known
    regression = remaining(regression_forecast, regression_actual, regression_known)
    # A calculated residual is also known demand, even if another component is missing.
    lower = (support_known + critical_known if support is None else support) + (
        regression_known if regression is None else regression) + technical_known
    maximum = max(future - lower, number(0))
    missing = [name for name, value in [('SUPPORT_FORECAST', support),
                                      ('REGRESSION_FORECAST', regression)] if value is None]
    total = None if missing else support + regression + technical_known
    # When even the upper bound is zero, effective capacity is established exactly.
    effective = None if missing and maximum > 0 else maximum
    gap = None if effective is None else effective - delivery
    return {
        'future_scheduled_capacity_hours': future,
        'remaining_support_demand_hours': support,
        'known_critical_support_remaining_hours': critical_known,
        'remaining_regression_demand_hours': regression,
        'remaining_technical_demand_hours': technical_known,
        'remaining_non_delivery_demand_hours': total,
        'known_non_delivery_demand_lower_bound_hours': lower,
        'maximum_possible_delivery_capacity_hours': maximum,
        'non_delivery_capacity_shortfall_hours': None if total is None else max(total - future, number(0)),
        'non_delivery_shortfall_lower_bound_hours': max(lower - future, number(0)),
        'effective_remaining_capacity_hours': effective,
        'capacity_gap_hours': gap,
        'capacity_pressure': delivery / effective if effective else None,
        'capacity_exhausted': None if effective is None else effective == 0,
        'uncovered_delivery_demand_hours': None if gap is None else max(-gap, number(0)),
        'uncovered_delivery_demand_lower_bound_hours': max(delivery - maximum, number(0)),
        'missing_inputs': missing,
    }


def primary_answer(disciplines):
    required = {d: r for d, r in disciplines.items() if r['remaining_delivery']['total_hours'] > 0}
    missing = [f'{d}_{name}' for d, r in required.items() for name in r['capacity']['missing_inputs']]
    if not required:
        return {'answer': 'yes', 'reason': 'Yes — no delivery work remains.', 'missing_inputs': []}
    shortfalls = []
    for d, row in required.items():
        c = row['capacity']
        hours = c['uncovered_delivery_demand_lower_bound_hours']
        if hours > 0:
            qualifier = 'at least ' if c['missing_inputs'] else ''
            shortfalls.append(f'{d} is short by {qualifier}{float(hours):.2f} h based on known demand')
    if shortfalls:
        return {'answer': 'no', 'reason': 'No — ' + '; '.join(shortfalls) + '.', 'missing_inputs': missing}
    if missing:
        return {'answer': 'insufficient_data',
                'reason': 'Required forecasts are unavailable (' + ', '.join(missing) +
                          '), so remaining effective capacity cannot be determined.', 'missing_inputs': missing}
    return {'answer': 'yes', 'reason': 'Yes — effective capacity covers remaining delivery hours in every required discipline.',
            'missing_inputs': []}
