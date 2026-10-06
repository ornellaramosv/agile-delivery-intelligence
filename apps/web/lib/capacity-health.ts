import { getApiOrigin } from "./api-origin";

export type CapacityMode = "current_sprint" | "retrospective";
export type Discipline = "DEV" | "QA";
export type Comparison = "since_planning" | "since_previous_working_day";
export type CapacitySelection = { sprint_day: number; comparison: Comparison };
// This demo endpoint accepts Days 1–10. These are request options, not progress metrics.
export const SPRINT_DAYS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] as const;
export const COMPARISONS: Record<Comparison, string> = {
  since_planning: "Since Planning", since_previous_working_day: "Since Previous Working Day",
};
export function capacitySelection(params: Record<string, string | string[] | undefined>): CapacitySelection {
  const day = typeof params.sprint_day === "string" ? Number(params.sprint_day) : 10;
  return { sprint_day: Number.isInteger(day) && day >= 1 && day <= 10 ? day : 10,
    comparison: params.comparison === "since_previous_working_day" ? "since_previous_working_day" : "since_planning" };
}
export function capacityQuery(selection: CapacitySelection) {
  return new URLSearchParams({ mode: "current_sprint", sprint_day: String(selection.sprint_day), comparison: selection.comparison });
}
export const CONSUMPTION_LABELS = {
  baseline_delivery_hours: "Baseline Delivery", rework_hours: "Rework", post_planning_scope_hours: "Post-Planning Scope",
  support_hours: "Support", release_regression_hours: "Release Regression", technical_enablement_hours: "Technical / Enablement",
} as const;
export type Consumption = Record<keyof typeof CONSUMPTION_LABELS | "total_hours", number>;
export type Forecast = { forecast_hours: number | null; forecast_status: "calculated" | "insufficient_history" | "not_applicable";
  reserved_hours: number; actual_hours: number };
export type CapacityDiscipline = {
  remaining_delivery: { total_hours: number };
  consumption: Consumption; support: Forecast;
  capacity: { effective_remaining_capacity_hours: number | null; capacity_gap_hours: number | null;
    missing_inputs: string[]; uncovered_delivery_demand_lower_bound_hours: number };
};
export type Progress = { total: number; closed: number; open: number; completion_rate?: number | null };
export type ReleaseSummary = {
  total_scope_items: number; closed_scope_items: number; pending_scope_items: number;
  current_sprint_required_total: number; current_sprint_required_closed: number; current_sprint_required_pending: number;
  included_customer_cases_total: number; included_customer_cases_engineering_closed: number; included_customer_cases_pending: number;
};
export type ReleaseReadiness = { status: "not_applicable"; summary: null } | {
  status: "applicable"; release_id: string; ready_for_regression: boolean; summary: ReleaseSummary;
  regression_phase: string; current_sprint_required_ids: string[]; current_sprint_future_release_ids: string[];
};
export type CapacityFact = { timestamp: string; kind: string; evidence_id: string; work_item_id?: string;
  task_id?: string; case_id?: string; reference_id?: string; category?: string; discipline?: string;
  hours?: number; remaining_hours?: number; source?: string };
export type CapacityBreakpoint = { timestamp: string; kind: string; evidence_id?: string;
  work_item_id?: string; case_id?: string; discipline?: string; sprint_day?: number;
  previous_gap_hours?: number; capacity_gap_hours?: number };
export type DailyCapacity = { sprint_day: number; timestamp: string; disciplines: Record<Discipline, CapacityDiscipline> };
export type CapacityResult = {
  sprint: { id: string; name: string; project: string; backlog: string };
  mode_context: { mode: CapacityMode; sprint_day: number; comparison: Comparison; snapshot_at: string;
    primary_answer: { answer: "yes" | "no" | "insufficient_data"; reason: string; missing_inputs: string[] } };
  sprint_progress: { original_baseline: Progress; current_scope: Progress; post_planning_scope: Progress };
  disciplines: Record<Discipline, CapacityDiscipline>;
  daily_capacity: DailyCapacity[];
  retrospective_breakpoints: CapacityBreakpoint[];
  critical_disruptions: { case_id: string; active: boolean; linked_work_item_id: string | null;
    events: { id: string; event_type: string; description?: string }[] }[];
  what_changed: { comparison: Comparison; from_at: string; to_at: string;
    by_discipline: Record<Discipline, { remaining_delivery_change_hours: number; consumption_change_hours: Consumption }>;
    facts: CapacityFact[] };
  release_readiness: ReleaseReadiness;
  support: { history: { sprint_id: string; recency_weight: number; standard_case_count: number; actual_hours: Record<string, number> }[] };
  dependencies: { items: { id: string; type: string; owner: string; work_item_ids: string[];
    elapsed_open_hours: number; technical_actual_hours: number; resolved_at: string | null; time_entry_ids: string[] }[] };
};

/** Called from the server page only; backend values are returned without metric calculations. */
export async function getSprintCapacityHealth(selection: CapacitySelection): Promise<CapacityResult> {
  return fetchCapacityHealth(selection, "current_sprint");
}
export async function getRetrospectiveCapacityHealth(): Promise<CapacityResult> {
  return fetchCapacityHealth({ sprint_day: 10, comparison: "since_planning" }, "retrospective");
}
async function fetchCapacityHealth(selection: CapacitySelection, mode: CapacityMode): Promise<CapacityResult> {
  const url = new URL("/demo/sprint-08/capacity-health", getApiOrigin());
  url.search = capacityQuery(selection).toString();
  url.searchParams.set("mode", mode);
  const response = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(10_000) });
  if (!response.ok) throw new Error(`Capacity Health API returned ${response.status}`);
  const data: CapacityResult = await response.json();
  if (!data.sprint || data.mode_context?.mode !== mode || !data.mode_context.primary_answer
      || (mode === "retrospective" && !Array.isArray(data.retrospective_breakpoints))
      || !data.sprint_progress || !data.disciplines?.DEV || !data.disciplines.QA
      || !data.what_changed?.by_discipline || !Array.isArray(data.what_changed.facts)
      || !data.release_readiness || (data.release_readiness.status === "applicable" && !data.release_readiness.summary)
      || !Array.isArray(data.daily_capacity) || !Array.isArray(data.support?.history)
      || !Array.isArray(data.dependencies?.items) || !Array.isArray(data.critical_disruptions)) {
    throw new Error("Capacity Health API returned an invalid response");
  }
  return data;
}
