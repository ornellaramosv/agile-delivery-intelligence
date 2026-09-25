import { cloneElement, type ReactElement } from "react";
import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { BurndownResult } from "../lib/burndown";
import payload from "./fixtures/burndown.json";
import { SprintHealthView } from "../app/sprint-health/components/sprint-health-view";
import SprintHealthPage from "../app/sprint-health/page";
import LoadingSprintHealth from "../app/sprint-health/loading";

// jsdom has no layout. Keep the real chart, replacing only container measurement.
vi.mock("recharts", async (importOriginal) => {
  const original = await importOriginal<typeof import("recharts")>();
  return { ...original, ResponsiveContainer: ({ children }: { children: ReactElement }) =>
    cloneElement(children as ReactElement<{ width: number; height: number }>, { width: 800, height: 300 }) };
});

// Captured from the approved endpoint; tests check presentation, not calculations.
const data = payload as BurndownResult;

function day(number: number) {
  return within(screen.getByRole("article", { name: `Day ${number}` }));
}

describe("Sprint Health presentation", () => {
  it("renders API metadata, duration, baseline and final remaining work", () => {
    render(<SprintHealthView data={data} />);
    const summary = within(screen.getByRole("region", { name: "Sprint summary" }));
    for (const label of ["Atlas", "Core Services", "Sprint 08", "10 working days", "Original baseline", "Remaining at Day 10"]) {
      expect(summary.getByText(label)).toBeVisible();
    }
    expect(summary.getByText("10")).toBeVisible();
    expect(summary.getByText("5")).toBeVisible();
    expect(summary.queryByText(/healthy|at risk/i)).not.toBeInTheDocument();
  });

  it("renders each backend snapshot without inventing an expected trajectory", () => {
    render(<SprintHealthView data={data} />);
    for (const [index, snapshot] of data.daily_snapshots.entries()) {
      const previous = data.daily_snapshots[index - 1];
      const expected = `${previous?.current_remaining_work ?? "—"} → ${snapshot.current_remaining_work}`;
      expect(day(snapshot.sprint_day).getByText(expected)).toBeVisible();
    }
    expect(screen.getByText(/fixed reference, not an expected trajectory/)).toBeVisible();
    expect(screen.getByRole("group", { name: "Actual remaining work by sprint day" }).querySelector(".recharts-line-curve")).toBeInTheDocument();
  });

  it.each([[3, "Up"], [4, "Up"], [5, "Flat"], [6, "Flat"]])("renders backend movement on Day %i as %s", (number, movement) => {
    render(<SprintHealthView data={data} />);
    expect(day(Number(number)).getByText(movement)).toBeVisible();
  });

  it("preserves both Day 6 causes alongside the zero net movement", () => {
    render(<SprintHealthView data={data} />);
    const row = day(6);
    expect(row.getByText("11 → 11")).toBeVisible();
    expect(row.getByText("0")).toBeVisible();
    expect(row.getByText(/Story closed/)).toBeVisible();
    expect(row.getByText("US-110")).toBeVisible();
    expect(row.getByText("−1")).toBeVisible();
    expect(row.getByText(/Scope added after baseline/)).toBeVisible();
    expect(row.getByText("US-111")).toBeVisible();
    expect(row.getByText("+1")).toBeVisible();
    expect(row.getByText("EVT-021")).toBeVisible();
    expect(row.getByText("EVT-024")).toBeVisible();
  });

  it("renders flatline and upward insight details with Bug and story IDs", () => {
    render(<SprintHealthView data={data} />);
    const flat = within(screen.getByRole("article", { name: "Flatline, Days 5–6" }));
    expect(flat.getByText("11 remaining delivery work items")).toBeVisible();
    expect(flat.getByText("US-111")).toBeVisible();
    const upward = within(screen.getByRole("article", { name: "Upward Movement, Day 3" }));
    expect(upward.getByText("Day 3 · 9 → 10")).toBeVisible();
    expect(upward.getByText("BUG-001")).toBeVisible();
    expect(upward.getByText(/against US-102/)).toBeVisible();
  });

  it("displays an empty response without fabricated zero metrics", () => {
    render(<SprintHealthView data={{ ...data, daily_snapshots: [], insights: [] }} />);
    expect(screen.getByRole("status")).toHaveTextContent("No daily snapshots available");
    expect(screen.queryByRole("group", { name: "Actual remaining work by sprint day" })).not.toBeInTheDocument();
    expect(screen.getAllByText("Unavailable")).toHaveLength(3);
  });

  it("presents the initial observation without a made-up previous-day value", () => {
    render(<SprintHealthView data={data} />);
    expect(day(1).getByText("Initial snapshot")).toBeVisible();
    expect(day(1).getByText("— → 10")).toBeVisible();
  });

  it("renders a loading state", () => {
    render(<LoadingSprintHealth />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading Sprint Health");
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
  });

  it("renders the API result through the server page", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => data }));
    render(await SprintHealthPage());
    expect(day(6).getByText("Flat")).toBeVisible();
  });

  it("renders API failure with a simple reload link", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
    render(await SprintHealthPage());
    expect(screen.getByRole("alert")).toHaveTextContent("Sprint data is unavailable");
    expect(screen.getByRole("link", { name: "Try again" })).toHaveAttribute("href", "/sprint-health");
    expect(screen.queryByText("Original baseline")).not.toBeInTheDocument();
  });

  it("uses presentation values from the response rather than hardcoded scenario totals", () => {
    const modified = structuredClone(data);
    modified.sprint.project = "Fictional variant";
    modified.daily_snapshots[5].current_remaining_work = 42;
    modified.daily_snapshots[5].explanation.movement = "down";
    modified.daily_snapshots[5].explanation.delta = -7;
    render(<SprintHealthView data={modified} />);
    expect(screen.getByText("Fictional variant")).toBeVisible();
    expect(day(6).getByText("11 → 42")).toBeVisible();
    expect(day(6).getByText("Down")).toBeVisible();
    expect(day(6).getByText("−7")).toBeVisible();
  });
});
