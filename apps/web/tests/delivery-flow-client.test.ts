import { expect, it, vi } from "vitest";
import { getSprintDeliveryFlow } from "../lib/delivery-flow";
import payload from "./fixtures/delivery-flow.json";

it("fetches the configured Flow endpoint without caching or modifying data", async () => {
  vi.stubEnv("ADI_API_BASE_URL", "http://adi-api.test:8000");
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => payload });
  vi.stubGlobal("fetch", fetchMock);
  expect(await getSprintDeliveryFlow()).toEqual(payload);
  expect(fetchMock.mock.calls[0][0].toString()).toBe("http://adi-api.test:8000/demo/sprint-08/delivery-flow");
  expect(fetchMock.mock.calls[0][1]).toMatchObject({ cache: "no-store", signal: expect.any(AbortSignal) });
});
it.each(["offline", "timeout"])("propagates %s to the unavailable state", async (reason) => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error(reason)));
  await expect(getSprintDeliveryFlow()).rejects.toThrow(reason);
});
it("rejects invalid successful responses", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) }));
  await expect(getSprintDeliveryFlow()).rejects.toThrow("invalid response");
});
