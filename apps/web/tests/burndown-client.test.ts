import { expect, it, vi } from "vitest";
import { getSprintBurndown } from "../lib/burndown";
import payload from "./fixtures/burndown.json";

it("loads the configured server endpoint without caching or altering the payload", async () => {
  vi.stubEnv("ADI_API_BASE_URL", "http://adi-api.test:8000");
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => payload });
  vi.stubGlobal("fetch", fetchMock);
  expect(await getSprintBurndown()).toEqual(payload);
  expect(fetchMock.mock.calls[0][0].toString()).toBe("http://adi-api.test:8000/demo/sprint-08/burndown");
  expect(fetchMock.mock.calls[0][1]).toMatchObject({ cache: "no-store", signal: expect.any(AbortSignal) });
});

it.each(["offline", "timeout"])("propagates %s failure to the page state", async (reason) => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error(reason)));
  await expect(getSprintBurndown()).rejects.toThrow(reason);
});

it("rejects malformed successful API responses", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) }));
  await expect(getSprintBurndown()).rejects.toThrow("invalid response");
});
