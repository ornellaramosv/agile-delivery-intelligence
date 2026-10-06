import { render, screen, within, fireEvent } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { CapacityResult } from "../lib/capacity-health";
import payload from "./fixtures/capacity-health.json";
import { CapacityHealthView } from "../app/capacity-health/components/capacity-health-view";
import CapacityHealthPage from "../app/capacity-health/page";
import LoadingCapacityHealth from "../app/capacity-health/loading";

const data = payload as CapacityResult;
const question = "Can we still finish the remaining work with the capacity we have left?";
function value(region: HTMLElement, label: string, expected: string) {
  expect(within(region).getByText(label).nextElementSibling).toHaveTextContent(expected);
}
it("renders Current Sprint metadata and the exact capacity question with backend reason", () => {
  render(<CapacityHealthView data={data} />);
  expect(screen.getByRole("heading", { level: 1, name: "Capacity Health" })).toBeVisible();
  expect(screen.getByText(/Atlas · Core Services · Sprint 08 · Fictional demo data/)).toBeVisible();
  const answer = within(screen.getByRole("region", { name: question }));
  expect(answer.getByText("No")).toBeVisible();
  expect(answer.getByText(data.mode_context.primary_answer.reason)).toBeVisible();
  expect(screen.queryByRole("heading", { name: "Critical disruption active" })).not.toBeInTheDocument();
});
it.each([["yes", "Yes"], ["no", "No"], ["insufficient_data", "Insufficient data"]] as const)("presents backend answer %s without inferring it from hours", (answer, label) => {
  const changed = structuredClone(data);
  changed.mode_context.primary_answer = { answer, reason: "Reason from domain", missing_inputs: [] };
  render(<CapacityHealthView data={changed} />);
  const region = within(screen.getByRole("region", { name: question }));
  expect(region.getByText(label)).toBeVisible();
  expect(region.getByText("Reason from domain")).toBeVisible();
});
it("renders API progress without using consumed effort or calculating counts", () => {
  const changed = structuredClone(data);
  changed.sprint_progress.current_scope = { closed: 8, total: 14, open: 6, completion_rate: .42 };
  render(<CapacityHealthView data={changed} />);
  expect(screen.getByRole("article", { name: "Original baseline" })).toHaveTextContent("6 / 10 Closed / Total4 Open");
  expect(screen.getByRole("article", { name: "Current scope" })).toHaveTextContent("8 / 14 Closed / Total6 Open");
  expect(screen.getByRole("article", { name: "Post-Planning Scope added" })).toHaveTextContent("1 / 1 Closed / Total0 Open");
  expect(screen.getByText(/Added scope changes the current scope, not the original commitment/)).toBeVisible();
});
it("shows separate DEV and QA capacity with gap in hours", () => {
  render(<CapacityHealthView data={data} />);
  const dev = screen.getByRole("article", { name: "DEV capacity" });
  value(dev, "Capacity Gap", "-45 h"); value(dev, "Remaining delivery demand", "45 h");
  value(dev, "Effective remaining capacity", "0 h"); value(dev, "Actual total consumption", "179 h");
  const qa = screen.getByRole("article", { name: "QA capacity" });
  value(qa, "Capacity Gap", "0 h"); value(qa, "Actual total consumption", "81 h");
});
it("preserves unavailable values and a proven no independently of missing forecasts", () => {
  const changed = structuredClone(data);
  Object.assign(changed.disciplines.DEV.capacity, { capacity_gap_hours: null, effective_remaining_capacity_hours: null, missing_inputs: ["SUPPORT_FORECAST"] });
  changed.disciplines.DEV.support.forecast_hours = null;
  changed.disciplines.DEV.support.forecast_status = "insufficient_history";
  changed.mode_context.primary_answer.missing_inputs = ["DEV_SUPPORT_FORECAST"];
  render(<CapacityHealthView data={changed} />);
  const dev = screen.getByRole("article", { name: "DEV capacity" });
  value(dev, "Capacity Gap", "Unavailable"); value(dev, "Effective remaining capacity", "Unavailable");
  expect(within(screen.getByRole("region", { name: question })).getByText("No")).toBeVisible();
  expect(screen.getByText(/DEV forecast: insufficient history/)).toBeVisible();
});
it("displays consumption categories exactly as supplied", () => {
  render(<CapacityHealthView data={data} />);
  const table = within(screen.getByRole("table", { name: "Recorded capacity consumption by discipline" }));
  for (const [label, dev, qa] of [["Baseline Delivery", "118 h", "50 h"], ["Rework", "38 h", "7 h"], ["Post-Planning Scope", "11 h", "3 h"],
    ["Support", "7 h", "10 h"], ["Release Regression", "0 h", "11 h"], ["Technical / Enablement", "5 h", "0 h"]]) {
    expect(table.getByRole("row", { name: `${label} ${dev} ${qa}` })).toBeVisible();
  }
});
it("keeps active disruption context and the normal answer, omitting resolved disruptions", () => {
  const changed = structuredClone(data);
  changed.critical_disruptions = [{ case_id: "INC-A", active: true, linked_work_item_id: "US-108", events: [
    { id: "INC-E1", event_type: "received", description: "Urgent package interrupts planned engineering work." }] },
    { case_id: "INC-DONE", active: false, linked_work_item_id: null, events: [] }];
  render(<CapacityHealthView data={changed} />);
  const critical = screen.getByRole("region", { name: "Critical disruption active" });
  expect(critical).toHaveTextContent("INC-A · Affected work: US-108");
  expect(critical).toHaveTextContent("Urgent package interrupts planned engineering work.");
  expect(screen.queryByText("INC-DONE")).not.toBeInTheDocument();
  expect(screen.getByRole("region", { name: question })).toBeVisible();
});
it("shows backend What Changed deltas and traceable scope/rework evidence", () => {
  render(<CapacityHealthView data={data} />);
  value(screen.getByRole("article", { name: "DEV changes" }), "Remaining delivery demand change", "-96 h");
  value(screen.getByRole("article", { name: "DEV changes" }), "Recorded consumption change", "+179 h");
  const section = within(screen.getByRole("region", { name: "What Changed?" }));
  expect(section.getByText(/EVT-021/)).toBeVisible();
  expect(section.getByText(/EVT-015/)).toBeVisible();
  expect(section.getByText("post planning scope").parentElement).toHaveTextContent("US-111");
});
it("uses release summary rather than recounting evidence rows", () => {
  const changed = structuredClone(data);
  if (changed.release_readiness.status !== "applicable") throw new Error("fixture");
  changed.release_readiness.summary.closed_scope_items = 4;
  changed.release_readiness.summary.pending_scope_items = 2;
  render(<CapacityHealthView data={changed} />);
  const release = screen.getByRole("region", { name: "Release Readiness" });
  value(release, "Total release scope", "4 / 6 Closed / Total · 2 Pending");
  value(release, "Current-sprint release-required US", "3 / 3 Closed / Total · 0 Pending");
  value(release, "Included customer / BOC engineering cases", "1 / 1 Closed / Total · 0 Pending");
  value(release, "Regression phase", "completed");
  expect(release).toHaveTextContent("Required for this release: US-101, US-102, US-110");
  expect(release).toHaveTextContent("Targeting future releases: US-103");
  expect(release).toHaveTextContent("not readiness gates");
});
it("hides the entire release section when not applicable", () => {
  render(<CapacityHealthView data={{ ...data, release_readiness: { status: "not_applicable", summary: null } }} />);
  expect(screen.queryByRole("region", { name: "Release Readiness" })).not.toBeInTheDocument();
});
it("shows support forecasts, reserves, actuals and all supplied standard-history periods", () => {
  render(<CapacityHealthView data={data} />);
  const support = within(screen.getByRole("table", { name: "Standard support hours" }));
  expect(support.getByRole("row", { name: "Forecast 12.6 h 16.9 h" })).toBeVisible();
  expect(support.getByRole("row", { name: "Reserved 13 h 10 h" })).toBeVisible();
  expect(support.getByRole("row", { name: "Actual 7 h 10 h" })).toBeVisible();
  const history = within(screen.getByRole("region", { name: "Historical support trend" }));
  expect(history.getAllByRole("listitem")).toHaveLength(4);
  for (const p of data.support.history) {
    const item = history.getByText(p.sprint_id).parentElement!;
    expect(item).toHaveTextContent(`${p.standard_case_count} standard cases`);
    for (const [discipline, h] of Object.entries(p.actual_hours)) value(item, discipline, `${h} h`);
  }
  expect(history.queryByText(/INC-/)).not.toBeInTheDocument();
});
it("does not invent absent support history", () => {
  render(<CapacityHealthView data={{ ...data, support: { history: [] } }} />);
  expect(screen.getByText("No historical support evidence available.")).toBeVisible();
});
it("distinguishes dependency elapsed duration from effort and keeps affected stories visible", () => {
  render(<CapacityHealthView data={data} />);
  const dep = screen.getByRole("region", { name: "Dependencies" });
  expect(dep).toHaveTextContent("US-107"); expect(dep).toHaveTextContent("pipeline · DevOps · Resolved");
  expect(dep).toHaveTextContent("Elapsed open duration: 100.5 h");
  expect(dep).toHaveTextContent("Actual technical effort: 3 h");
  expect(dep).toHaveTextContent("Elapsed calendar time is not team effort or lost capacity");
});
it("supports native accessible day/comparison GET controls", () => {
  render(<CapacityHealthView data={data} />);
  fireEvent.change(screen.getByLabelText("Sprint day"), { target: { value: "6" } });
  fireEvent.change(screen.getByLabelText("What Changed comparison"), { target: { value: "since_previous_working_day" } });
  const form = screen.getByRole("form", { name: "Current Sprint snapshot" }) as HTMLFormElement;
  expect(Object.fromEntries(new FormData(form))).toEqual({ sprint_day: "6", comparison: "since_previous_working_day" });
  expect(form).toHaveAttribute("action", "/capacity-health"); expect(form).toHaveAttribute("method", "get");
  expect(screen.getByRole("button", { name: "Apply snapshot" })).toBeVisible();
});
it("passes URL selections to the server-side API with current_sprint mode", async () => {
  const changed = structuredClone(data);
  changed.mode_context.sprint_day = 6;
  changed.mode_context.comparison = changed.what_changed.comparison = "since_previous_working_day";
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => changed });
  vi.stubGlobal("fetch", fetchMock);
  render(await CapacityHealthPage({ searchParams: Promise.resolve({ sprint_day: "6", comparison: "since_previous_working_day", mode: "retrospective" }) }));
  expect(fetchMock.mock.calls[0][0].searchParams.get("mode")).toBe("current_sprint");
  expect(fetchMock.mock.calls[0][0].searchParams.get("sprint_day")).toBe("6");
  expect(screen.getByLabelText("Sprint day")).toHaveValue("6");
  expect(screen.getByRole("region", { name: "What Changed?" })).toHaveTextContent("Since Previous Working Day");
});
it("renders API failure and preserves selection in retry", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
  render(await CapacityHealthPage({ searchParams: Promise.resolve({ sprint_day: "6", comparison: "since_previous_working_day" }) }));
  expect(screen.getByRole("alert")).toHaveTextContent("Capacity data is unavailable");
  expect(screen.getByRole("link", { name: "Try again" }).getAttribute("href")).toContain("sprint_day=6&comparison=since_previous_working_day");
});
it("renders loading without fabricated metrics", () => {
  render(<LoadingCapacityHealth />);
  expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
  expect(screen.getByRole("status")).toHaveTextContent("Loading Capacity Health");
});
it("handles empty snapshots without showing a capacity conclusion", () => {
  render(<CapacityHealthView data={{ ...data, daily_capacity: [] }} />);
  expect(screen.getByRole("status")).toHaveTextContent("No capacity results available");
  expect(screen.queryByRole("region", { name: question })).not.toBeInTheDocument();
});
