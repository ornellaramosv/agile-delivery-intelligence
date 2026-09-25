/** Presentation contract for GET /demo/sprint-08/burndown. No domain calculations. */
export type Movement = "up" | "flat" | "down";

export type Cause = {
  type: "story_closed" | "scope_added" | "closure_blocking_bug_created" | "closure_blocking_bug_resolved";
  id: string;
  work_item_id: string;
  effect: number;
  event_id: string;
  timestamp: string;
};

export type DailySnapshot = {
  sprint_day: number;
  date: string;
  original_baseline: number;
  open_baseline_stories: number;
  open_scope_added_stories: number;
  open_closure_blocking_bugs: number;
  current_remaining_work: number;
  closed_baseline_stories: number;
  closed_scope_added_stories: number;
  scope_added_total: number;
  active_rework_bugs: string[];
  composition: {
    open_baseline_story_ids: string[];
    open_scope_added_story_ids: string[];
    open_closure_blocking_bug_ids: string[];
  };
  explanation: { day: number; movement: Movement | null; delta: number | null; causes: Cause[] };
};

export type Insight = {
  type: "upward_movement";
  sprint_day: number;
  previous_remaining: number;
  current_remaining: number;
  delta: number;
  causes: Cause[];
} | {
  type: "flatline";
  start_day: number;
  end_day: number;
  number_of_days: number;
  remaining_work: number;
  contributing_context: { sprint_day: number; causes: Cause[]; event_ids: string[] }[];
};

export type BurndownResult = {
  sprint: { id: string; name: string; project: string; backlog: string; start_date: string; end_date: string; timezone: string };
  configuration: { flatline_threshold_days: number };
  daily_snapshots: DailySnapshot[];
  insights: Insight[];
};

/** Called only by the Next.js server page. The browser never needs the API origin. */
export async function getSprintBurndown(): Promise<BurndownResult> {
  const origin = process.env.ADI_API_BASE_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(new URL("/demo/sprint-08/burndown", origin), {
    cache: "no-store",
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) throw new Error(`Burndown API returned ${response.status}`);
  const data: BurndownResult = await response.json();
  if (!data.sprint || !Array.isArray(data.daily_snapshots) || !Array.isArray(data.insights)) {
    throw new Error("Burndown API returned an invalid response");
  }
  return data;
}
