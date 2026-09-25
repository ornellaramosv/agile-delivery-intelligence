import { cloneElement, type ReactElement } from "react";
import { render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { DeliveryFlowResult } from "../lib/delivery-flow";
import payload from "./fixtures/delivery-flow.json";
import { DeliveryFlowView } from "../app/delivery-flow/components/delivery-flow-view";
import DeliveryFlowPage from "../app/delivery-flow/page";
import LoadingDeliveryFlow from "../app/delivery-flow/loading";

vi.mock("recharts", async (importOriginal) => {
  const original = await importOriginal<typeof import("recharts")>();
  return { ...original, ResponsiveContainer: ({ children }: { children: ReactElement }) =>
    cloneElement(children as ReactElement<{ width: number; height: number }>, { width: 800, height: 300 }) };
});
const data = payload as DeliveryFlowResult;
const day = (n: number) => within(screen.getByRole("article", { name: `Day ${n}` }));

it("renders metadata and API final scope, open and Closed totals", () => {
  render(<DeliveryFlowView data={data} />);
  const summary = within(screen.getByRole("region", { name: "Flow summary" }));
  for (const value of ["Atlas", "Core Services", "Sprint 08", "Active scope at Day 10", "11", "7", "4"]) {
    expect(summary.getByText(value)).toBeVisible();
  }
});

it("shows all current states, including Development, Returned to DEV and zero counts", () => {
  render(<DeliveryFlowView data={data} />);
  const composition = screen.getByRole("region", { name: "Current flow composition" });
  for (const state of data.workflow_states) {
    const row = within(composition).getByText(state).closest("div")!;
    expect(within(row).getByText(String(data.daily_snapshots.at(-1)!.states[state]))).toBeVisible();
  }
});

it("renders a real stacked chart and a complete tabular alternative", () => {
  render(<DeliveryFlowView data={data} />);
  expect(screen.getByRole("group", { name: "Workflow composition by sprint day" }).querySelector(".recharts-bar-rectangle")).toBeInTheDocument();
  expect(screen.getByText("View daily snapshot values")).toBeVisible();
  expect(screen.getByText(/Daily snapshots, not cumulative totals/)).toBeVisible();
});

it("shows Day 6 active scope and formal entry without changing baseline", () => {
  render(<DeliveryFlowView data={data} />);
  expect(day(5).getByText("10 active User Stories")).toBeVisible();
  expect(day(6).getByText("11 active User Stories")).toBeVisible();
  expect(day(6).getByText("US-111")).toBeVisible();
  expect(day(6).getByText("Scope entered")).toBeVisible();
  expect(day(6).getByText(/original baseline is unchanged/)).toBeVisible();
});

it.each([[3, "US-102"], [7, "US-105"]])("highlights the traceable QA return on Day %i", (n, id) => {
  render(<DeliveryFlowView data={data} />);
  const row = day(Number(n)).getByText(String(id)).closest("li")!;
  expect(within(row).getByText("QA → Returned to DEV")).toBeVisible();
  expect(within(row).getByText("QA return · Rework")).toBeVisible();
  expect(row).toHaveClass("flow-qa-return");
});

it("renders only supplied transitions and scope entries, excluding context event IDs", () => {
  render(<DeliveryFlowView data={data} />);
  for (const id of ["EVT-014", "EVT-030", "EVT-031", "EVT-045"]) {
    expect(screen.queryByText(id)).not.toBeInTheDocument();
  }
  expect(day(1).getByText("Opening scope")).toBeVisible();
  expect(day(1).getByText("No workflow transitions.")).toBeVisible();
});

it("renders API values rather than hardcoded scenario totals", () => {
  const changed = structuredClone(data);
  changed.sprint.project = "Presentation variant";
  Object.assign(changed.daily_snapshots.at(-1)!, { total_active_scope: 30, closed_stories: 20, open_stories: 10 });
  changed.daily_snapshots.at(-1)!.states.Development = 8;
  render(<DeliveryFlowView data={changed} />);
  const summary = within(screen.getByRole("region", { name: "Flow summary" }));
  for (const value of ["Presentation variant", "30", "20", "10"]) expect(summary.getByText(value)).toBeVisible();
  expect(within(screen.getByRole("region", { name: "Current flow composition" })).getByText("8")).toBeVisible();
});

it("renders loading", () => {
  render(<LoadingDeliveryFlow />);
  expect(screen.getByRole("status")).toHaveTextContent("Loading Delivery Flow");
  expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
});

it("renders an empty response without fabricated totals", () => {
  render(<DeliveryFlowView data={{ ...data, daily_snapshots: [], daily_movements: [] }} />);
  expect(screen.getByRole("status")).toHaveTextContent("No flow snapshots available");
  expect(screen.getAllByText("Unavailable")).toHaveLength(3);
  expect(screen.queryByRole("group", { name: "Workflow composition by sprint day" })).not.toBeInTheDocument();
});

it("renders the server page from the API", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => data }));
  render(await DeliveryFlowPage());
  expect(day(6).getByText("US-111")).toBeVisible();
});

it("renders API unavailable and a retry link", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
  render(await DeliveryFlowPage());
  expect(screen.getByRole("alert")).toHaveTextContent("Flow data is unavailable");
  expect(screen.getByRole("link", { name: "Try again" })).toHaveAttribute("href", "/delivery-flow");
});
