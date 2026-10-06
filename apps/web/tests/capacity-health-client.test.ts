import { expect, it, vi } from "vitest";
import { capacitySelection, getSprintCapacityHealth } from "../lib/capacity-health";
import payload from "./fixtures/capacity-health.json";

it("requests Current Sprint with the selected day and comparison, unchanged payload and no cache", async () => {
  vi.stubEnv("ADI_API_BASE_URL", "https://adi-api.test");
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => payload });
  vi.stubGlobal("fetch", fetchMock);
  const selection = { sprint_day: 6, comparison: "since_previous_working_day" } as const;
  expect(await getSprintCapacityHealth(selection)).toEqual(payload);
  const [url, options] = fetchMock.mock.calls[0];
  expect(url.origin + url.pathname).toBe("https://adi-api.test/demo/sprint-08/capacity-health");
  expect(Object.fromEntries(url.searchParams)).toEqual({ mode: "current_sprint", sprint_day: "6", comparison: "since_previous_working_day" });
  expect(options).toMatchObject({ cache: "no-store", signal: expect.any(AbortSignal) });
});
it("validates URL choices and ignores Retrospective mode", () => {
  expect(capacitySelection({})).toEqual({ sprint_day: 10, comparison: "since_planning" });
  expect(capacitySelection({ sprint_day: "6", comparison: "since_previous_working_day", mode: "retrospective" })).toEqual({ sprint_day: 6, comparison: "since_previous_working_day" });
  for (const day of ["0", "11", "2.5", "bad", ["1", "2"]]) {
    expect(capacitySelection({ sprint_day: day, comparison: "bad" })).toEqual({ sprint_day: 10, comparison: "since_planning" });
  }
});
it.each(["offline", "timeout"])("propagates %s", async reason => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error(reason)));
  await expect(getSprintCapacityHealth(capacitySelection({}))).rejects.toThrow(reason);
});
it("rejects HTTP failures", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 503 }));
  await expect(getSprintCapacityHealth(capacitySelection({}))).rejects.toThrow("503");
});
it.each([{}, { ...payload, support: {} }, { ...payload, sprint_progress: null },
  { ...payload, release_readiness: { status: "applicable" } },
  { ...payload, mode_context: { ...payload.mode_context, mode: "retrospective" } }])("rejects incomplete or wrong-mode responses", async data => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => data }));
  await expect(getSprintCapacityHealth(capacitySelection({}))).rejects.toThrow("invalid response");
});
