"""Frozen reconciliations and independent synthetic Capacity Health edge cases."""
from copy import deepcopy
from fractions import Fraction
import json

from fastapi.testclient import TestClient
import pytest

from app.domain.capacity_health import calculate_capacity_health
from app.domain.capacity_health.capacity import capacity_result, primary_answer
from app.domain.capacity_health.engine import api_values
from app.domain.capacity_health.forecast import regression_forecast, support_forecast
from app.main import app
from app.services.demo_capacity_health import load_capacity_inputs


@pytest.fixture
def inputs():
    return load_capacity_inputs()


@pytest.fixture
def result(inputs):
    return calculate_capacity_health(**inputs)


@pytest.mark.parametrize('discipline,support,product,actual,remaining', [
    ('DEV', Fraction('12.6'), 187, 179, 45), ('QA', Fraction('16.9'), 81, 81, 0),
])
def test_acceptance(result, discipline, support, product, actual, remaining):
    row = result['disciplines'][discipline]
    assert row['support']['forecast_hours'] == support
    assert row['support']['forecast_status'] == 'calculated'
    assert row['support']['forecasted_new_cases'] == Fraction('5.3')
    assert row['planned_product_capacity_hours'] == product
    assert row['consumption']['total_hours'] == actual
    assert row['remaining_delivery']['total_hours'] == remaining
    assert row['capacity']['future_scheduled_capacity_hours'] == 0
    assert row['capacity']['capacity_pressure'] is None
    assert row['capacity']['capacity_exhausted'] is True
    assert row['capacity']['uncovered_delivery_demand_hours'] == remaining


def test_full_consumption(result):
    assert result['disciplines']['DEV']['consumption'] == dict(baseline_delivery_hours=118,
        rework_hours=38, post_planning_scope_hours=11, support_hours=7,
        release_regression_hours=0, technical_enablement_hours=5, total_hours=179)
    assert result['disciplines']['QA']['consumption'] == dict(baseline_delivery_hours=50,
        rework_hours=7, post_planning_scope_hours=3, support_hours=10,
        release_regression_hours=11, technical_enablement_hours=0, total_hours=81)


def test_precision_and_variances(result):
    row = result['disciplines']['QA']
    assert row['regression']['forecast_hours'] == Fraction(419, 50)
    assert row['regression']['actual_vs_forecast_hours'] == Fraction(131, 50)
    assert row['support']['reserve_vs_forecast_hours'] == Fraction('-6.9')
    assert row['support']['actual_vs_reserve_hours'] == 0
    scope = result['scope_change']
    assert scope['effort_rate'] == Fraction(13, 188)
    assert api_values(scope)['effort_rate'] == .0691
    assert api_values(scope)['by_discipline']['DEV']['effort_rate'] == .0709
    assert api_values(scope)['by_discipline']['QA']['effort_rate'] == .0638


def test_scope_and_no_future_leakage(inputs, result):
    assert result['scope_change']['original_baseline_items'] == 10
    assert result['scope_change']['added_items'] == 1
    assert result['scope_change']['item_rate'] == Fraction(1, 10)
    assert result['scope_change']['added_estimated_hours'] == 13
    assert result['scope_change']['added_actual_hours'] == 14
    assert result['scope_change']['baseline_estimated_hours'] == 188
    before = calculate_capacity_health(**inputs, sprint_day=5)
    assert before['scope_change']['added_items'] == 0
    assert before['scope_change']['added_actual_hours'] == 0
    assert all(f['timestamp'] <= before['mode_context']['snapshot_at'] for f in before['what_changed']['facts'])
    converted = next(c for c in before['support']['cases'] if c['case_id'] == 'SUP-08-003')
    assert converted['linked_work_item_id'] is None


def test_daily_schedule_and_open_support(inputs, result):
    for row in result['daily_capacity']:
        for d, hours in [('DEV', 20), ('QA', 10)]:
            assert row['disciplines'][d]['capacity']['future_scheduled_capacity_hours'] == (10-row['sprint_day'])*hours
    first = calculate_capacity_health(**inputs, sprint_day=1)
    assert first['planning']['disciplines']['DEV']['support']['forecast_hours'] == Fraction('12.6')
    assert first['planning']['disciplines']['QA']['support']['forecast_hours'] == Fraction('16.9')


def test_no_release(inputs):
    inputs['release_regression'] = None
    inputs['capacity_ledger']['time_entries'] = [e for e in inputs['capacity_ledger']['time_entries'] if e.get('category') != 'release_regression']
    result = calculate_capacity_health(**inputs)
    assert result['release_readiness']['status'] == 'not_applicable'
    for d in ('DEV', 'QA'):
        r = result['disciplines'][d]['regression']
        assert r['forecast_status'] == 'not_applicable'
        assert r['forecast_hours'] == r['actual_hours'] == r['reserved_hours'] == 0


def test_missing_support_history(inputs):
    inputs['support_cases']['historical_sprints'] = []
    result = calculate_capacity_health(**inputs, sprint_day=1)
    assert result['disciplines']['DEV']['support']['forecast_hours'] is None
    assert result['disciplines']['DEV']['support']['forecast_status'] == 'insufficient_history'
    assert result['disciplines']['DEV']['capacity']['effective_remaining_capacity_hours'] is None
    assert result['mode_context']['primary_answer']['answer'] == 'insufficient_data'
    assert 'DEV_SUPPORT_FORECAST' in result['mode_context']['primary_answer']['missing_inputs']


def test_missing_regression_history(inputs):
    inputs['regression_history'] = []
    result = calculate_capacity_health(**inputs, sprint_day=1)
    assert result['disciplines']['QA']['regression']['forecast_status'] == 'insufficient_history'
    assert result['disciplines']['QA']['capacity']['capacity_gap_hours'] is None
    assert result['mode_context']['primary_answer']['answer'] == 'insufficient_data'
    assert result['mode_context']['primary_answer']['missing_inputs'] == ['QA_REGRESSION_FORECAST']


def test_zero_case_history_is_not_absent_history():
    history = [{'recency_weight': 1, 'evidence_complete': True, 'cases': []}]
    forecast = support_forecast(history, 'DEV', 2)
    assert forecast['forecasted_new_cases'] == 0
    assert forecast['expected_hours_per_case'] is None
    assert forecast['forecast_hours'] is None
    assert support_forecast([], 'DEV', 2)['forecasted_new_cases'] is None


def test_mixed_zero_case_period_retains_frequency_without_guessing_effort():
    history = [{'recency_weight': .5, 'evidence_complete': True, 'cases': []},
               {'recency_weight': .5, 'evidence_complete': True, 'cases': [
                   {'case_class': 'standard', 'actual_hours': {'DEV': 4}}]}]
    forecast = support_forecast(history, 'DEV', 2)
    assert forecast['forecasted_new_cases'] == Fraction(1, 2)
    assert forecast['expected_hours_per_case'] is None
    assert forecast['forecast_hours'] is None
    assert forecast['forecast_status'] == 'insufficient_history'


def test_critical_history_excluded(inputs, result):
    history = inputs['support_cases']['historical_sprints']
    for period in history:
        period['cases'].append({'id': 'SYNTHETIC', 'case_class': 'critical', 'actual_hours': {'DEV': 999, 'QA': 999}})
    changed = calculate_capacity_health(**inputs)
    for d in ('DEV', 'QA'):
        assert changed['disciplines'][d]['support']['forecast_hours'] == result['disciplines'][d]['support']['forecast_hours']


def test_active_critical_preserves_evidence_without_consuming_standard_forecast(inputs):
    case = deepcopy(inputs['support_cases']['current_cases'][1])
    case.update(id='INC-08-SYNTHETIC', case_class='critical', customer_closed_at=None)
    case['events'] = [{'id': 'CRIT-001', 'timestamp': case['received_at'], 'event_type': 'received',
                       'description': 'Initial QA bypassed; urgent package preparation displaced normal work.'}]
    case['remaining_observations'] = [{'timestamp': case['received_at'], 'remaining_hours': {'DEV': 4, 'QA': 0}}]
    inputs['support_cases']['current_cases'].append(case)
    inputs['capacity_ledger']['time_entries'].append({'id': 'CRIT-TIME-001', 'timestamp': case['received_at'],
        'category': 'support', 'reference_id': case['id'], 'discipline': 'DEV', 'hours': 3})
    result = calculate_capacity_health(**inputs, sprint_day=2)
    disruption = result['critical_disruptions'][0]
    assert disruption['active'] is True
    assert disruption['actual_hours']['DEV'] == 3
    assert disruption['time_entry_ids'] == ['CRIT-TIME-001']
    row = result['disciplines']['DEV']
    assert row['support']['forecast_hours'] == Fraction('12.6')
    assert row['capacity']['remaining_support_demand_hours'] == Fraction('14.6')  # 12.6 - 2 standard actual + 4 critical
    assert any(f['kind'] == 'critical_disruption' for f in result['retrospective_breakpoints'])
    assert 'answer' in result['mode_context']['primary_answer']


def capacity_row(future, delivery, support=None, known=5, regression=0):
    cap = capacity_result(future=Fraction(future), delivery=Fraction(delivery), support_forecast=support,
                          support_actual=0, support_known=known, regression_forecast=regression,
                          regression_actual=0, regression_known=0, technical_known=0)
    return {'remaining_delivery': {'total_hours': delivery}, 'capacity': cap}


@pytest.mark.parametrize('future,delivery,forecast,answer', [
    (20, 25, None, 'no'), (40, 25, None, 'insufficient_data'),
    (40, 0, None, 'yes'), (40, 25, 10, 'yes'), (0, 25, None, 'no'), (0, 0, None, 'yes'),
])
def test_approved_missing_evidence_rules(future, delivery, forecast, answer):
    row = capacity_row(future, delivery, forecast)
    result = primary_answer({'DEV': row})
    assert result['answer'] == answer
    if future == 20:
        assert 'at least 10.00 h' in result['reason']
    if delivery == 0:
        assert 'no delivery work remains' in result['reason']
    if future == 40 and forecast is None:
        for field in ('effective_remaining_capacity_hours', 'capacity_gap_hours', 'capacity_pressure', 'uncovered_delivery_demand_hours'):
            assert row['capacity'][field] is None


def test_no_overrides_unknown_other_discipline():
    result = primary_answer({'DEV': capacity_row(40, 25), 'QA': capacity_row(10, 20, 0, known=0)})
    assert result['answer'] == 'no'
    assert result['missing_inputs'] == ['DEV_SUPPORT_FORECAST']


def test_zero_effective_capacity_and_no_infinity():
    row = capacity_row(5, 10, 12)
    assert row['capacity']['effective_remaining_capacity_hours'] == 0
    assert row['capacity']['capacity_pressure'] is None
    assert row['capacity']['capacity_gap_hours'] == -10
    assert row['capacity']['non_delivery_capacity_shortfall_hours'] == 7
    json.dumps(api_values(row), allow_nan=False)


def test_open_support_lower_bound_can_exceed_forecast():
    row = capacity_row(40, 25, 2, known=12)
    assert row['capacity']['remaining_support_demand_hours'] == 12
    assert row['capacity']['effective_remaining_capacity_hours'] == 28


def test_known_regression_residual_contributes_to_lower_bound():
    row = capacity_row(40, 25, None, known=5, regression=15)
    assert row['capacity']['maximum_possible_delivery_capacity_hours'] == 20
    assert primary_answer({'DEV': row})['answer'] == 'no'


def test_unresolved_and_overlapping_dependencies(inputs):
    result = calculate_capacity_health(**inputs, sprint_day=5)
    assert len(result['dependencies']['items']) == 2
    assert result['disciplines']['DEV']['capacity']['remaining_technical_demand_hours'] == 7
    final = calculate_capacity_health(**inputs)
    assert final['disciplines']['DEV']['consumption']['technical_enablement_hours'] == 5
    dep = final['dependencies']['items'][1]
    assert dep['resolved_at'] is None
    assert dep['technical_actual_hours'] == 2
    assert dep['elapsed_open_hours'] > 100  # calendar duration never becomes DEV consumption
    assert final['disciplines']['DEV']['capacity']['remaining_technical_demand_hours'] == 2


def test_conversion_does_not_double_count(result):
    case = next(c for c in result['support']['cases'] if c['case_id'] == 'SUP-08-003')
    assert case['actual_hours'] == {'DEV': 3, 'QA': 5}
    assert result['scope_change']['added_actual_hours'] == 14
    assert case['engineering_closed'] is True and case['customer_closed'] is False
    assert result['disciplines']['DEV']['consumption']['total_hours'] == 179


def test_cross_sprint_readiness_and_early_regression(inputs):
    before = calculate_capacity_health(**inputs, sprint_day=6)['release_readiness']
    assert before['ready_for_regression'] is False
    assert next(i for i in before['scope'] if i['work_item_id'] == 'US-102')['closed'] is False
    ready = calculate_capacity_health(**inputs, sprint_day=7)['release_readiness']
    assert ready['ready_for_regression'] is True
    assert len(ready['scope']) == 6
    assert sum('closed_at' in i for i in ready['scope']) == 3
    assert ready['dependencies_are_readiness_gates'] is False
    regression = calculate_capacity_health(**inputs, sprint_day=8)['release_readiness']
    assert regression['regression_phase'] == 'in_progress'
    done = calculate_capacity_health(**inputs, sprint_day=9)['release_readiness']
    assert done['regression_phase'] == 'completed'
    assert done['qa_available_for_certification'] is True
    assert 'US-111' in done['current_sprint_future_release_ids']


def test_open_engineering_case_blocks_release_but_customer_case_does_not(inputs):
    case = inputs['support_cases']['current_cases'][0]
    case['customer_closed_at'] = None
    assert calculate_capacity_health(**inputs, sprint_day=7)['release_readiness']['ready_for_regression'] is True
    case['events'] = [e for e in case['events'] if e['event_type'] != 'engineering_closed']
    assert calculate_capacity_health(**inputs, sprint_day=7)['release_readiness']['ready_for_regression'] is False


def test_changed_since_planning_and_previous_day(inputs):
    planning = calculate_capacity_health(**inputs, sprint_day=6)
    assert planning['what_changed']['by_discipline']['DEV']['remaining_delivery_change_hours'] == (
        planning['disciplines']['DEV']['remaining_delivery']['total_hours'] - 141)
    previous = calculate_capacity_health(**inputs, sprint_day=6, comparison='since_previous_working_day')
    assert previous['what_changed']['from_at'] == '2030-04-12T18:00:00Z'
    facts = previous['what_changed']['facts']
    assert any(f['kind'] == 'post_planning_scope' and f['evidence_id'] == 'EVT-021' for f in facts)
    assert not any(f['kind'] == 'rework' for f in facts)
    assert any(f['kind'] == 'rework' for f in planning['what_changed']['facts'])
    assert any(f['kind'] == 'dependency_resolved' for f in facts)


def test_first_day_comparison_and_retrospective(inputs):
    first = calculate_capacity_health(**inputs, sprint_day=1, comparison='since_previous_working_day')
    assert first['what_changed']['from_at'] == inputs['sprint']['baseline_at']
    retro = calculate_capacity_health(**inputs, mode='retrospective')
    kinds = {b['kind'] for b in retro['retrospective_breakpoints']}
    assert {'regression_started', 'rework', 'post_planning_scope', 'dependency_opened', 'capacity_gap_crossing'} <= kinds


def test_deterministic_and_non_mutating(inputs):
    original = deepcopy(inputs)
    a = calculate_capacity_health(**inputs)
    assert a == calculate_capacity_health(**inputs)
    assert original == inputs


def test_api_matches_domain(inputs):
    client = TestClient(app)
    result = client.get('/demo/sprint-08/capacity-health')
    assert result.status_code == 200
    assert result.json() == api_values(calculate_capacity_health(**inputs))
    response = client.get('/demo/sprint-08/capacity-health?sprint_day=6&comparison=since_previous_working_day&mode=retrospective')
    assert response.json() == api_values(calculate_capacity_health(**inputs, sprint_day=6, comparison='since_previous_working_day', mode='retrospective'))


@pytest.mark.parametrize('query', ['sprint_day=0', 'sprint_day=11', 'comparison=other', 'mode=other'])
def test_api_rejects_invalid_options(query):
    assert TestClient(app).get('/demo/sprint-08/capacity-health?' + query).status_code == 422


@pytest.mark.parametrize('option', [{'sprint_day': 0}, {'comparison': 'other'}, {'mode': 'other'}])
def test_domain_rejects_invalid_options(inputs, option):
    with pytest.raises(ValueError):
        calculate_capacity_health(**inputs, **option)


@pytest.mark.parametrize('defect', ['duplicate_time', 'unreconciled_time', 'support_after_conversion', 'negative_remaining'])
def test_reject_inconsistent_effort_evidence(inputs, defect):
    ledger = inputs['capacity_ledger']
    if defect == 'duplicate_time':
        ledger['time_entries'].append(deepcopy(ledger['time_entries'][0]))
    elif defect == 'unreconciled_time':
        next(e for e in ledger['time_entries'] if 'task_id' in e)['hours'] += 1
    elif defect == 'support_after_conversion':
        next(e for e in ledger['time_entries'] if e.get('reference_id') == 'SUP-08-003')['timestamp'] = '2030-04-19T10:00:00Z'
    else:
        ledger['task_remaining_observations'][0]['remaining_hours'] = -1
    with pytest.raises(ValueError):
        calculate_capacity_health(**inputs)
