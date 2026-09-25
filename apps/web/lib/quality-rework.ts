/** Read-only Quality & Rework API contract. No frontend metric calculations. */
export type FirstPassOutcome = "passed" | "failed" | "not_reached_qa" | "excluded" | null;
export type ReworkEffort = { tasks: number; task_ids: string[]; estimated_hours: number; completed_hours: number; remaining_hours: number };
export type QualityStory = {
  work_item_id: string; source: string; carry_over: boolean; reached_qa: boolean;
  first_pass_population: boolean; first_pass_outcome: FirstPassOutcome; outcome_reason: string | null;
  final_state: string; rework_cycles: number; related_bugs: string[]; rework_effort: ReworkEffort;
  evidence: { first_qa_event_id: string | null; first_attempt_outcome_event_id: string | null; acceptance_event_ids: string[] };
};
export type ReworkCycle = {
  id: string; work_item_id: string; cycle_number: number; sprint_day: number; timestamp: string;
  related_bug_id: string | null; qa_rejection_event_id: string; return_to_dev_event_id: string;
  bug_detection_event_id: string | null; qa_recertification_event_ids: string[];
  acceptance_event_id: string | null; status: "active" | "completed";
  bug_resolution_event_id: string | null; bug_resolution_status: "resolved" | "unresolved" | null;
  bug_record_status: string | null;
};
export type QualitySummary = {
  eligible_qa_stories: number; first_pass_successes: number; first_pass_failures: number;
  first_pass_qa_rate: number | null; stories_with_rework: number; total_rework_cycles: number;
  active_rework_cycles_at_sprint_end: number; resolved_rework_cycles: number; rework_bug_count: number;
  rework_task_count: number; rework_estimated_hours: number; rework_completed_hours: number; rework_remaining_hours: number;
};
export type QualityReworkResult = {
  sprint: { id: string; name: string; project: string; backlog: string; start_date: string; end_date: string; timezone: string };
  quality_summary: QualitySummary; stories: QualityStory[]; rework_cycles: ReworkCycle[]; rework_effort: ReworkEffort;
};
export async function getSprintQualityRework(): Promise<QualityReworkResult> {
  const origin = process.env.ADI_API_BASE_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(new URL("/demo/sprint-08/quality-rework", origin), {
    cache: "no-store", signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) throw new Error(`Quality & Rework API returned ${response.status}`);
  const data: QualityReworkResult = await response.json();
  if (!data.sprint || !data.quality_summary || !data.rework_effort
      || !Array.isArray(data.stories) || !Array.isArray(data.rework_cycles)) {
    throw new Error("Quality & Rework API returned an invalid response");
  }
  return data;
}
