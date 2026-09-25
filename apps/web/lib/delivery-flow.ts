/** API presentation contract. State names and their order come from the backend. */
export type FlowSnapshot = {
  sprint_day: number;
  date: string;
  states: Record<string, number>;
  story_states: Record<string, string>;
  open_stories: number;
  closed_stories: number;
  total_active_scope: number;
};
export type FlowMovement = {
  event_id: string;
  work_item_id: string;
  timestamp: string;
  from_state: string;
  to_state: string;
};
export type FlowDay = {
  sprint_day: number;
  date: string;
  movements: FlowMovement[];
  scope_entries: (Omit<FlowMovement, "from_state"> & { from_state: null })[];
};
export type DeliveryFlowResult = {
  sprint: { id: string; name: string; project: string; backlog: string; start_date: string; end_date: string; timezone: string };
  workflow_states: string[];
  daily_snapshots: FlowSnapshot[];
  daily_movements: FlowDay[];
};

/** Server-side fetch, consistent with the Burndown service. */
export async function getSprintDeliveryFlow(): Promise<DeliveryFlowResult> {
  const origin = process.env.ADI_API_BASE_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(new URL("/demo/sprint-08/delivery-flow", origin), {
    cache: "no-store", signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) throw new Error(`Delivery Flow API returned ${response.status}`);
  const data: DeliveryFlowResult = await response.json();
  if (!data.sprint || !Array.isArray(data.workflow_states) || !Array.isArray(data.daily_snapshots)
      || !Array.isArray(data.daily_movements)) {
    throw new Error("Delivery Flow API returned an invalid response");
  }
  return data;
}
