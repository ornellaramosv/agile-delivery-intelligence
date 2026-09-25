import { render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import type { QualityReworkResult } from "../lib/quality-rework";
import payload from "./fixtures/quality-rework.json";
import { QualityReworkView } from "../app/quality-rework/components/quality-rework-view";
import QualityReworkPage from "../app/quality-rework/page";
import LoadingQualityRework from "../app/quality-rework/loading";

const data = payload as QualityReworkResult;
function assertValue(region: HTMLElement, label: string, value: string) {
  expect(within(region).getByText(label).nextElementSibling).toHaveTextContent(value);
}

it("renders metadata and all backend summary values", () => {
  render(<QualityReworkView data={data} />);
  const summary = screen.getByRole("region", { name: "Quality summary" });
  for (const text of ["Atlas", "Core Services", "Sprint 08"]) expect(within(summary).getByText(text)).toBeVisible();
  for (const [label, value] of [["Eligible QA stories", "7"], ["First-pass successes", "4"], ["First-pass failures", "3"],
    ["First-pass QA Rate", "57.1%"], ["Stories with rework", "3"], ["Active rework cycles", "1"]]) assertValue(summary, label, value);
});

it("visualizes the backend ratio without reclassifying the population", () => {
  render(<QualityReworkView data={data} />);
  expect(screen.getByText("4 passed / 7 eligible")).toBeVisible();
  expect(screen.getByRole("meter", { name: "First-pass QA rate" })).toHaveAttribute("value", String(data.quality_summary.first_pass_qa_rate));
  expect(screen.getByText(/Client-incident scope-added work is excluded/)).toBeVisible();
});

it.each([["US-101", "Passed"], ["US-102", "Failed"], ["US-104", "Failed"], ["US-110", "Passed"],
  ["US-107", "Not reached QA"], ["US-108", "Not reached QA"], ["US-109", "Not reached QA"], ["US-111", "Excluded"]])(
  "renders %s classification as %s", (id, label) => {
    render(<QualityReworkView data={data} />);
    expect(within(screen.getByRole("article", { name: `QA ${id}` })).getByText(label)).toBeVisible();
  });

it("explains carry-over eligibility and excluded/not-reached stories", () => {
  render(<QualityReworkView data={data} />);
  expect(within(screen.getByRole("article", { name: "QA US-110" })).getByText("Eligible · Carry-over")).toBeVisible();
  const incident = within(screen.getByRole("article", { name: "QA US-111" }));
  expect(incident.getByText("Outside denominator")).toBeVisible();
  expect(incident.getByText(/Client incident/)).toBeVisible();
  expect(incident.queryByText(/^(Passed|Failed)$/)).not.toBeInTheDocument();
  expect(within(screen.getByRole("article", { name: "QA US-108" })).getByText("No QA attempt in this sprint.")).toBeVisible();
});

it("renders three rework stories, cycle totals and linked Bugs", () => {
  render(<QualityReworkView data={data} />);
  expect(screen.getAllByRole("article", { name: /^Rework US-/ })).toHaveLength(3);
  const overview = screen.getByRole("region", { name: "Rework Intelligence" });
  for (const [label, value] of [["Stories with rework", "3"], ["Total rework cycles", "3"], ["Completed cycles", "2"], ["Active cycles", "1"], ["Linked Bugs", "3"]]) assertValue(overview, label, value);
  expect(within(screen.getByRole("article", { name: "Rework US-102" })).getByText("Cycle 1 · BUG-001")).toBeVisible();
});

it("identifies active rework with failure and unresolved defect evidence", () => {
  render(<QualityReworkView data={data} />);
  const story = within(screen.getByRole("article", { name: "Rework US-104" }));
  for (const text of ["Failed", "Active rework", "Final state: Returned to DEV", "Cycle 1 · BUG-002", "Bug resolution: unresolved"]) {
    expect(story.getByText(text)).toBeVisible();
  }
  expect(story.getByText(/QA rejection \/ return to DEV: EVT-017/)).toBeVisible();
});

it("shows completed rework independently of first-pass failure, with traceable events", () => {
  render(<QualityReworkView data={data} />);
  const story = within(screen.getByRole("article", { name: "Rework US-102" }));
  for (const text of ["Failed", "Completed", "Final state: Closed", "Rework acceptance: EVT-030", "QA rejection / return to DEV: EVT-015"]) expect(story.getByText(text)).toBeVisible();
  expect(story.getByText(/QA → Returned to DEV/)).toBeVisible();
});

it("presents total and story effort without normalizing overruns", () => {
  render(<QualityReworkView data={data} />);
  const total = screen.getByRole("region", { name: "Rework effort" });
  for (const [label, value] of [["Rework tasks", "7"], ["Estimated hours", "45"], ["Completed hours", "45"], ["Remaining hours", "8"]]) assertValue(total, label, value);
  const story = screen.getByRole("article", { name: "Rework US-104" });
  for (const [label, value] of [["Rework tasks", "1"], ["Estimated hours", "16"], ["Completed hours", "12"], ["Remaining hours", "8"]]) assertValue(story, label, value);
  expect(within(total).getByText(/may exceed estimated hours/)).toBeVisible();
});

it("uses API summary precision and totals instead of calculating from story rows", () => {
  const changed = structuredClone(data);
  Object.assign(changed.quality_summary, { eligible_qa_stories: 12, first_pass_successes: 8, first_pass_failures: 2, first_pass_qa_rate: 0.625 });
  changed.rework_effort.completed_hours = 60;
  render(<QualityReworkView data={changed} />);
  const summary = screen.getByRole("region", { name: "Quality summary" });
  assertValue(summary, "Eligible QA stories", "12");
  assertValue(summary, "First-pass successes", "8");
  assertValue(summary, "First-pass QA Rate", "62.5%");
  assertValue(screen.getByRole("region", { name: "Rework effort" }), "Completed hours", "60");
});

it("renders unavailable rate and unknown outcome without fabricating a result", () => {
  const changed = structuredClone(data);
  changed.quality_summary.first_pass_qa_rate = null;
  changed.stories[0].first_pass_outcome = null;
  render(<QualityReworkView data={changed} />);
  expect(screen.queryByRole("meter")).not.toBeInTheDocument();
  expect(within(screen.getByRole("article", { name: "QA US-101" })).getByText("Not yet determined")).toBeVisible();
});

it("renders loading", () => {
  render(<LoadingQualityRework />);
  expect(screen.getByRole("status")).toHaveTextContent("Loading Quality & Rework");
  expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
});
it("renders an empty quality result without fabricated metrics", () => {
  render(<QualityReworkView data={{ ...data, stories: [], rework_cycles: [] }} />);
  expect(screen.getByRole("status")).toHaveTextContent("No quality results available");
  expect(screen.queryByRole("region", { name: "Quality summary" })).not.toBeInTheDocument();
});
it("renders the server page with API results", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => data }));
  render(await QualityReworkPage());
  expect(screen.getByText("4 passed / 7 eligible")).toBeVisible();
});
it("renders API failure and retry", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
  render(await QualityReworkPage());
  expect(screen.getByRole("alert")).toHaveTextContent("Quality data is unavailable");
  expect(screen.getByRole("link", { name: "Try again" })).toHaveAttribute("href", "/quality-rework");
});
