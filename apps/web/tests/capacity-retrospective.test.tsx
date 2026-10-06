import { cloneElement, type ReactElement } from "react";
import { render, screen, within, fireEvent } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { CapacityResult } from "../lib/capacity-health";
import { getRetrospectiveCapacityHealth } from "../lib/capacity-health";
import payload from "./fixtures/capacity-health.json";
import { RetrospectiveView, SprintTurningPoints } from "../app/capacity-health/components/retrospective-view";
import { CapacityHealthView } from "../app/capacity-health/components/capacity-health-view";
import RetrospectivePage from "../app/capacity-health/retrospective/page";
import LoadingRetrospective from "../app/capacity-health/retrospective/loading";

vi.mock("recharts", async importOriginal => {
  const original = await importOriginal<typeof import("recharts")>();
  return { ...original, ResponsiveContainer: ({ children }: { children: ReactElement }) =>
    cloneElement(children as ReactElement<{ width: number; height: number }>, { width: 380, height: 260 }) };
});
const data = { ...payload, mode_context: { ...payload.mode_context, mode: "retrospective" } } as CapacityResult;

it("requests only retrospective/day10/since_planning and leaves the payload unchanged", async () => {
  const mock = vi.fn().mockResolvedValue({ ok: true, json: async () => data });
  vi.stubGlobal("fetch", mock);
  expect(await getRetrospectiveCapacityHealth()).toEqual(data);
  expect(Object.fromEntries(mock.mock.calls[0][0].searchParams)).toEqual({ mode: "retrospective", sprint_day: "10", comparison: "since_planning" });
  expect(mock.mock.calls[0][1]).toMatchObject({ cache: "no-store", signal: expect.any(AbortSignal) });
});
it.each([{}, { ...data, retrospective_breakpoints: null }, payload])("rejects incomplete/wrong-mode API results", async invalid => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => invalid }));
  await expect(getRetrospectiveCapacityHealth()).rejects.toThrow("invalid response");
});
it("renders the final backend outcome, progress and mode links without editable snapshot selectors", () => {
  render(<RetrospectiveView data={data} />);
  const answer = screen.getByRole("region", { name: "Final capacity outcome" });
  expect(answer).toHaveTextContent(data.mode_context.primary_answer.reason);
  expect(within(answer).getByText("No")).toBeVisible();
  expect(screen.getByRole("article", { name: "Original baseline" })).toHaveTextContent("6 / 10");
  expect(screen.getByRole("article", { name: "Current scope" })).toHaveTextContent("7 / 11");
  expect(screen.getByRole("article", { name: "Post-Planning Scope added" })).toHaveTextContent("1 / 1");
  const modes = within(screen.getByRole("navigation", { name: "Capacity Health mode" }));
  expect(modes.getByRole("link", { name: "Retrospective" })).toHaveAttribute("aria-current", "page");
  expect(modes.getByRole("link", { name: "Current Sprint" })).toHaveAttribute("href", "/capacity-health");
  expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
});
it("keeps Current Sprint controls and adds a Retrospective link", () => {
  render(<CapacityHealthView data={payload as CapacityResult} />);
  expect(screen.getByRole("combobox", { name: "Sprint day" })).toHaveValue("10");
  expect(screen.getByRole("link", { name: "Current Sprint" })).toHaveAttribute("aria-current", "page");
  expect(screen.getByRole("link", { name: "Retrospective" })).toHaveAttribute("href", "/capacity-health/retrospective");
});
it("presents backend turning points chronologically with evidence and discipline", () => {
  render(<SprintTurningPoints points={[...data.retrospective_breakpoints].reverse()} />);
  const items = screen.getAllByRole("listitem");
  expect(items).toHaveLength(data.retrospective_breakpoints.length);
  const timestamps = items.map(item => item.querySelector("time")!.dateTime);
  expect(timestamps).toEqual([...timestamps].sort());
  expect(screen.getByText("Evidence: EVT-021").parentElement).toHaveTextContent("US-111");
  expect(screen.getByRole("heading", { name: "Regression started" })).toBeVisible();
  expect(screen.getByRole("heading", { name: "Regression completed" })).toBeVisible();
  expect(screen.getByRole("heading", { name: "Dependency resolved" })).toBeVisible();
  expect(screen.getAllByRole("heading", { name: "Rework" })).toHaveLength(3);
  expect(screen.getAllByRole("heading", { name: "Capacity gap crossing" })[0].parentElement).toHaveTextContent("Discipline: DEV");
});
it("preserves critical and unknown supplied evidence without inventing event IDs", () => {
  render(<SprintTurningPoints points={[
    { timestamp: "2030-04-10T10:00:00Z", kind: "critical_disruption", evidence_id: "CRIT-E1", case_id: "INC-1", work_item_id: "US-108" },
    { timestamp: "2030-04-11T18:00:00Z", kind: "capacity_gap_crossing", discipline: "QA", previous_gap_hours: 8, capacity_gap_hours: -3 },
  ]} />);
  expect(screen.getByRole("heading", { name: "Critical disruption" })).toBeVisible();
  expect(screen.getByText("Evidence: CRIT-E1")).toBeVisible();
  expect(screen.getByText(/Capacity gap: 8 h → -3 h/)).toBeVisible();
  expect(screen.queryByText(/Evidence: undefined/)).not.toBeInTheDocument();
});
it("plots separate DEV/QA series and exposes direct API daily values, preserving nulls", () => {
  const changed = structuredClone(data);
  changed.daily_capacity[0].disciplines.DEV.capacity.capacity_gap_hours = 123.45;
  changed.daily_capacity[0].disciplines.QA.capacity.effective_remaining_capacity_hours = null;
  render(<RetrospectiveView data={changed} />);
  expect(screen.getByRole("group", { name: "DEV daily capacity chart" })).toBeVisible();
  expect(screen.getByRole("group", { name: "QA daily capacity chart" })).toBeVisible();
  fireEvent.click(screen.getByText("DEV daily values")); fireEvent.click(screen.getByText("QA daily values"));
  expect(within(screen.getByRole("table", { name: "DEV daily capacity hours" })).getByText("123.45 h")).toBeVisible();
  expect(within(screen.getByRole("table", { name: "QA daily capacity hours" })).getByText("Unavailable")).toBeVisible();
});
it("keeps What Changed summaries and avoids duplicating timeline event evidence", () => {
  render(<RetrospectiveView data={data} />);
  const changes = screen.getByRole("region", { name: "What changed from Planning" });
  expect(changes).toHaveTextContent("-96 h");
  expect(changes).toHaveTextContent("+179 h");
  expect(within(changes).queryByText(/EVT-021/)).not.toBeInTheDocument();
  expect(screen.getByRole("region", { name: "Sprint turning points" })).toHaveTextContent("EVT-021");
});
it("retains resolved disruptions in retrospect, with their original evidence", () => {
  const changed = structuredClone(data);
  changed.critical_disruptions = [{ case_id: "INC-1", active: false, linked_work_item_id: "US-108", events: [
    { id: "CRIT-DONE", event_type: "engineering_closed", description: "Urgent package completed." }] }];
  render(<RetrospectiveView data={changed} />);
  const critical = screen.getByRole("region", { name: "Critical disruptions during the sprint" });
  expect(critical).toHaveTextContent("Completed by close"); expect(critical).toHaveTextContent("US-108");
  expect(critical).toHaveTextContent("Evidence: CRIT-DONE");
});
it("renders release/support/dependency outcomes and excludes critical history from the standard trend", () => {
  render(<RetrospectiveView data={data} />);
  expect(screen.getByRole("region", { name: "Release Readiness" })).toHaveTextContent("6 / 6 Closed / Total · 0 Pending");
  expect(screen.getByRole("table", { name: "Standard support hours" })).toHaveTextContent("12.6 h");
  const history = screen.getByRole("region", { name: "Historical support trend" });
  expect(history).toHaveTextContent("ATLAS-SPRINT-07"); expect(history).not.toHaveTextContent("INC-07");
  expect(screen.getByRole("region", { name: "Dependencies" })).toHaveTextContent("Elapsed open duration: 100.5 h");
  expect(screen.getByRole("region", { name: "Dependencies" })).toHaveTextContent("Actual technical effort: 3 h");
});
it("hides non-applicable release and absent disruptions; handles missing turning points", () => {
  render(<RetrospectiveView data={{ ...data, release_readiness: { status: "not_applicable", summary: null }, retrospective_breakpoints: [] }} />);
  expect(screen.queryByRole("region", { name: "Release Readiness" })).not.toBeInTheDocument();
  expect(screen.queryByRole("region", { name: "Critical disruptions during the sprint" })).not.toBeInTheDocument();
  expect(screen.getByText("No turning points recorded.")).toBeVisible();
});
it.each(["yes", "insufficient_data"] as const)("presents backend %s without deriving an answer", answer => {
  const changed = structuredClone(data);
  changed.mode_context.primary_answer = { answer, reason: "Backend explanation", missing_inputs: ["DEV_SUPPORT_FORECAST"] };
  render(<RetrospectiveView data={changed} />);
  expect(screen.getByRole("region", { name: "Final capacity outcome" })).toHaveTextContent(answer === "yes" ? "Yes" : "Insufficient data");
  expect(screen.getByText("Backend explanation")).toBeVisible();
});
it("renders loading", () => { render(<LoadingRetrospective />); expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true"); });
it("renders unavailable with a mode-specific retry", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
  render(await RetrospectivePage());
  expect(screen.getByRole("alert")).toHaveTextContent("Retrospective data is unavailable");
  expect(screen.getByRole("link", { name: "Try again" })).toHaveAttribute("href", "/capacity-health/retrospective");
});
it("renders the server page and handles empty daily data", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ ...data, daily_capacity: [] }) }));
  render(await RetrospectivePage());
  expect(screen.getByRole("status")).toHaveTextContent("No retrospective results available");
  expect(screen.queryByRole("region", { name: "Final capacity outcome" })).not.toBeInTheDocument();
});
