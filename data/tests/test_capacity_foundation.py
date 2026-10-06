"""Validate fictional Capacity Health facts and their links to frozen v1 evidence."""
import json
import math
import unittest
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1] / 'demo'


def load(folder, name):
    return json.loads((DEMO / folder / (name + '.json')).read_text(encoding='utf-8'))


class CapacityFoundationValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sprint = load('sprint-08', 'sprint')
        cls.tasks = {t['id']: t for t in load('sprint-08', 'tasks')}
        cls.items = {i['id']: i for i in load('sprint-08', 'work-items')}
        cls.events = {e['id']: e for e in load('sprint-08', 'delivery-events')}
        cls.plan = load('sprint-08', 'capacity-plan')
        cls.mapping = load('sprint-08', 'task-capacity-map')
        cls.ledger = load('sprint-08', 'capacity-ledger')
        cls.dependencies = load('sprint-08', 'dependencies')
        cls.decisions = load('sprint-08', 'scope-decisions')
        cls.release = load('sprint-08', 'release-regression')
        cls.support = load('capacity-history', 'support-cases')
        cls.regression = load('capacity-history', 'regression-history')

    def test_schedule_and_reserves(self):
        self.assertEqual(self.plan['sprint_id'], self.sprint['id'])
        self.assertEqual(self.plan['disciplines'], ['DEV', 'QA'])
        for row, day in zip(self.plan['daily_schedule'], self.sprint['working_days'], strict=True):
            self.assertEqual(row['date'], day['date'])
            self.assertEqual(row['sprint_day'], day['sprint_day'])
            self.assertEqual(row['gross_hours'], {'DEV': 20, 'QA': 10})
        self.assertEqual(self.plan['reserves'], {'DEV': {'support_hours': 13, 'regression_hours': 0},
                                                'QA': {'support_hours': 10, 'regression_hours': 9}})

    def test_mapping_complete_unique_and_no_effort_duplication(self):
        self.assertEqual(len(self.mapping), len(self.tasks))
        self.assertEqual({r['task_id'] for r in self.mapping}, set(self.tasks))
        for row in self.mapping:
            self.assertEqual(set(row), {'task_id', 'discipline'})
            self.assertIn(row['discipline'], ('DEV', 'QA'))
            expected = 'QA' if self.tasks[row['task_id']]['type'].startswith('QA ') else 'DEV'
            self.assertEqual(row['discipline'], expected)

    def test_task_time_reconciles_without_changing_final_values(self):
        totals = defaultdict(float)
        for e in self.ledger['time_entries']:
            if 'task_id' in e:
                self.assertIn(e['task_id'], self.tasks)
                totals[e['task_id']] += e['hours']
                task = self.tasks[e['task_id']]
                self.assertGreaterEqual(e['timestamp'], task['created_at'])
                self.assertLessEqual(e['timestamp'], task['completed_at'] or self.sprint['snapshot_at'])
        for tid, t in self.tasks.items():
            self.assertEqual(totals[tid], t['completed_hours'])

    def test_task_observations_are_dated_raw_facts(self):
        rows = self.ledger['task_remaining_observations']
        self.assertEqual(len({r['id'] for r in rows}), len(rows))
        for row in rows:
            task = self.tasks[row['task_id']]
            self.assertEqual(set(row), {'id', 'timestamp', 'task_id', 'remaining_hours'})
            self.assertGreaterEqual(row['remaining_hours'], 0)
            self.assertGreaterEqual(row['timestamp'], task['created_at'])
            self.assertLess(row['timestamp'], self.sprint['snapshot_at'])
            if task['completed_at'] and row['timestamp'] >= task['completed_at']:
                self.assertEqual(row['remaining_hours'], 0)

    def test_entry_ids_dates_numbers_and_references(self):
        entries = self.ledger['time_entries']
        self.assertEqual(len({e['id'] for e in entries}), len(entries))
        references = {'support': {c['id'] for c in self.support['current_cases']},
                      'technical_enablement': {d['id'] for d in self.dependencies},
                      'release_regression': {self.release['release_id']}}
        dates = {d['date'] for d in self.sprint['working_days']}
        for row in entries:
            self.assertTrue(math.isfinite(row['hours']))
            self.assertGreater(row['hours'], 0)
            dt = datetime.fromisoformat(row['timestamp'])
            self.assertIsNotNone(dt.tzinfo)
            self.assertIn(dt.date().isoformat(), dates)
            if 'task_id' not in row:
                self.assertIn(row['reference_id'], references[row['category']])
                self.assertIn(row['discipline'], ('DEV', 'QA'))

    def test_non_task_actuals(self):
        totals = defaultdict(float)
        for row in self.ledger['time_entries']:
            if 'task_id' not in row:
                totals[(row['category'], row['discipline'])] += row['hours']
        self.assertEqual(dict(totals), {('support', 'DEV'): 7, ('support', 'QA'): 10,
                                       ('technical_enablement', 'DEV'): 5, ('release_regression', 'QA'): 11})

    def test_support_history_counts_and_effort(self):
        expected = [(8, 16, 24, 6), (7, 14, 21, 4), (5, 10, 15, 2), (4, 8, 12, 1)]
        ids = []
        for period, (count, dev, qa, arch) in zip(self.support['historical_sprints'], expected, strict=True):
            self.assertTrue(period['evidence_complete'])
            standard = [c for c in period['cases'] if c['case_class'] == 'standard']
            self.assertEqual(len(standard), count)
            for discipline, total in [('DEV', dev), ('QA', qa), ('Architecture', arch)]:
                self.assertEqual(sum(c['actual_hours'][discipline] for c in standard), total)
            for case in period['cases']:
                self.assertIn(case['case_class'], ('standard', 'critical'))
                ids.append(case['id'])
            self.assertLess(period['start_date'], self.sprint['start_date'])
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual([p['recency_weight'] for p in self.support['historical_sprints']], [.1, .2, .3, .4])

    def test_support_opening_and_lifecycle(self):
        opening = [c for c in self.support['current_cases'] if c['received_at'] <= self.sprint['baseline_at']]
        self.assertEqual(len(opening), 1)
        self.assertEqual(opening[0]['planning_remaining_hours'], {'DEV': 2, 'QA': 1})
        allowed = {'received', 'qa_validation', 'technical_investigation', 'not_reproducible',
                   'entered_sprint', 'prepared_for_future_release', 'engineering_closed'}
        for case in self.support['current_cases']:
            self.assertIn(case['case_class'], ('standard', 'critical'))
            self.assertEqual(case['events'][0]['timestamp'], case['received_at'])
            self.assertEqual(case['events'][0]['event_type'], 'received')
            self.assertEqual([e['timestamp'] for e in case['events']], sorted(e['timestamp'] for e in case['events']))
            for event in case['events']:
                self.assertIn(event['event_type'], allowed)
            for observation in case['remaining_observations']:
                self.assertGreaterEqual(observation['timestamp'], case['received_at'])
                self.assertEqual(set(observation['remaining_hours']), {'DEV', 'QA'})
                self.assertTrue(all(h >= 0 for h in observation['remaining_hours'].values()))

    def test_conversion_time_boundary_and_scope_decision(self):
        for decision in self.decisions:
            event = self.events[decision['delivery_event_id']]
            self.assertEqual(event['event_type'], 'scope_added')
            self.assertEqual(decision['timestamp'], event['timestamp'])
            self.assertEqual(decision['work_item_id'], event['work_item_id'])
            case = next(c for c in self.support['current_cases'] if c['id'] == decision['support_case_id'])
            self.assertEqual(case['linked_work_item_id'], event['work_item_id'])
            self.assertFalse(self.items[event['work_item_id']]['original_baseline'])
            for row in self.ledger['time_entries']:
                if row.get('reference_id') == case['id']:
                    self.assertLess(row['timestamp'], event['timestamp'])
                if row.get('task_id') in self.tasks and self.tasks[row['task_id']]['work_item_id'] == event['work_item_id']:
                    self.assertGreaterEqual(row['timestamp'], event['timestamp'])
            self.assertIsNone(case['customer_closed_at'])
            self.assertTrue(any(e['event_type'] == 'engineering_closed' for e in case['events']))

    def test_dependencies_and_technical_effort(self):
        expected = [('DEP-001', 'pipeline', 'DevOps', ['US-107'], 3),
                    ('DEP-002', 'architecture', 'Architecture', ['US-108'], 2)]
        for dep, (did, kind, owner, items, hours) in zip(self.dependencies, expected, strict=True):
            self.assertEqual((dep['id'], dep['type'], dep['owner'], dep['work_item_ids']), (did, kind, owner, items))
            self.assertTrue(set(items) <= set(self.items))
            self.assertEqual(dep['remaining_observations'][0]['timestamp'], dep['opened_at'])
            rows = [e for e in self.ledger['time_entries'] if e.get('reference_id') == did]
            self.assertEqual(sum(e['hours'] for e in rows), hours)
            for row in rows:
                self.assertGreaterEqual(row['timestamp'], dep['opened_at'])
                self.assertLessEqual(row['timestamp'], dep['resolved_at'] or self.sprint['snapshot_at'])

    def test_regression_history(self):
        self.assertEqual([(r['release_id'], r['scope_count'], r['actual_qa_hours'], r['recency_weight']) for r in self.regression],
                         [('REL-05', 5, 7, .2), ('REL-06', 8, 12, .3), ('REL-07', 6, 8, .5)])

    def test_cross_sprint_scope_ready_before_regression(self):
        release = self.release
        self.assertEqual(len(release['scope']), 6)
        self.assertEqual(len({i['work_item_id'] for i in release['scope']}), 6)
        started = next(e['timestamp'] for e in release['events'] if e['event_type'] == 'regression_started')
        for item in release['scope']:
            if item['origin_sprint_id'] == self.sprint['id']:
                closed = next(e for e in self.events.values() if e['work_item_id'] == item['work_item_id'] and e['to_state'] == 'Closed')
                self.assertLess(closed['timestamp'], started)
            else:
                self.assertLess(item['closed_at'], self.sprint['baseline_at'])
                self.assertTrue(item['certification_evidence_id'])
        for case_id in release['customer_case_ids']:
            case = next(c for c in self.support['current_cases'] if c['id'] == case_id)
            closed = next(e for e in case['events'] if e['event_type'] == 'engineering_closed')
            self.assertLess(closed['timestamp'], started)

    def test_regression_effort_window_and_qa_resumes(self):
        started, completed = [e['timestamp'] for e in self.release['events']]
        rows = [e for e in self.ledger['time_entries'] if e.get('category') == 'release_regression']
        self.assertEqual(sum(e['hours'] for e in rows), 11)
        for row in rows:
            self.assertEqual(row['discipline'], 'QA')
            self.assertGreaterEqual(row['timestamp'], started)
            self.assertLessEqual(row['timestamp'], completed)
        self.assertLess(completed, self.sprint['snapshot_at'])
        resumed = [e for e in self.ledger['time_entries'] if e.get('task_id') == 'TASK-017' and e['timestamp'] > completed]
        self.assertTrue(resumed)

    def test_fixture_has_no_calculated_capacity_outputs(self):
        forbidden = {'capacity_gap_hours', 'forecast_hours', 'capacity_pressure', 'health_score',
                     'effective_remaining_capacity_hours', 'snapshots', 'answer', 'employee_id'}
        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(set(value) & forbidden)
                for child in value.values(): inspect(child)
            elif isinstance(value, list):
                for child in value: inspect(child)
        for record in [self.plan, self.mapping, self.ledger, self.dependencies, self.decisions,
                       self.release, self.support, self.regression]:
            inspect(record)


if __name__ == '__main__':
    unittest.main()
