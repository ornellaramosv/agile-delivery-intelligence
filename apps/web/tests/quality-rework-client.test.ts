import { expect, it, vi } from "vitest";
import { getSprintQualityRework } from "../lib/quality-rework";
import payload from "./fixtures/quality-rework.json";

it("fetches the configured endpoint without caching or modifying payload", async () => {
  vi.stubEnv("ADI_API_BASE_URL", "http://adi-api.test:8000");
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => payload });
  vi.stubGlobal("fetch", fetchMock);
  expect(await getSprintQualityRework()).toEqual(payload);
  expect(fetchMock.mock.calls[0][0].toString()).toBe("http://adi-api.test:8000/demo/sprint-08/quality-rework");
  expect(fetchMock.mock.calls[0][1]).toMatchObject({ cache: "no-store", signal: expect.any(AbortSignal) });
});
it.each(["offline", "timeout"])("propagates %s", async (reason) => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error(reason)));
  await expect(getSprintQualityRework()).rejects.toThrow(reason);
});
it("rejects malformed successful results", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) }));
  await expect(getSprintQualityRework()).rejects.toThrow("invalid response");
});
