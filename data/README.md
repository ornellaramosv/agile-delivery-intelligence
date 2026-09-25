# Demo data

All scenario records are fictional and support delivery-intelligence implementation and testing.

- [Sprint 08: Atlas / Core Services](demo/sprint-08/README.md): first realistic scenario, with 11 User Stories, tasks, defects, and traceable delivery events.
- [Sprint 08 audit](demo/sprint-08/AUDIT.md): story outcomes, bugs, Task-effort totals, and daily event chronology for Product review.
- [Schema](schema.md): field definitions and snapshot/event conventions used by the fixture.
- `examples/empty-dataset.json`: original minimal collection placeholder, retained as a foundation example; use the Sprint 08 folder for the complete event-based fixture.
- `tests/test_sprint_08.py`: standalone fixture validation using the Python standard library.

Run from the repository root:

```sh
python3 -m unittest discover -s data/tests -v
```

The read-only Burndown, Delivery Flow, and Quality & Rework demo services load the frozen Sprint 08 records. Task hours remain outside Burndown and Delivery Flow; Quality & Rework aggregates explicitly classified rework effort. The fixture and its audit document retain the pre-implementation scenario contract; current behavior is documented in [Burndown Intelligence](../docs/burndown-intelligence.md). There is no dataset editing API or persistence.
