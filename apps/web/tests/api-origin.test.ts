import { expect, it, vi } from "vitest";
import { getApiOrigin } from "../lib/api-origin";
import { getSprintBurndown } from "../lib/burndown";
import { getSprintDeliveryFlow } from "../lib/delivery-flow";
import { getSprintQualityRework } from "../lib/quality-rework";

it("keeps the local development fallback", () => {
  vi.stubEnv("NODE_ENV", "development");
  vi.stubEnv("ADI_API_BASE_URL", "");
  expect(getApiOrigin()).toBe("http://127.0.0.1:8000");
});

it.each([getSprintBurndown, getSprintDeliveryFlow, getSprintQualityRework])(
  "rejects missing production configuration before making a request", async (client) => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("ADI_API_BASE_URL", "");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    await expect(client()).rejects.toThrow("ADI_API_BASE_URL is required in production");
    expect(fetchMock).not.toHaveBeenCalled();
  },
);

it("normalizes an origin with a trailing slash for safe endpoint joining", () => {
  vi.stubEnv("ADI_API_BASE_URL", " https://adi.example/ ");
  expect(new URL("/health", getApiOrigin()).href).toBe("https://adi.example/health");
});

it.each(["https://adi.example/api", "https://user:password@adi.example", "file:///tmp", "https://adi.example?x=1", "https://adi.example/#fragment"])(
  "rejects an ambiguous or unsupported API origin: %s", (value) => {
    vi.stubEnv("ADI_API_BASE_URL", value);
    expect(getApiOrigin).toThrow("ADI_API_BASE_URL must be");
  },
);
