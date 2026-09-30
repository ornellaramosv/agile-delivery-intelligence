/** Server-side configuration shared by the three presentation clients. */
export function getApiOrigin(): string {
  const configured = process.env.ADI_API_BASE_URL?.trim();
  if (!configured) {
    if (process.env.NODE_ENV === "production") {
      throw new Error("ADI_API_BASE_URL is required in production");
    }
    return "http://127.0.0.1:8000";
  }
  const url = new URL(configured);
  if (!["http:", "https:"].includes(url.protocol) || url.username || url.password
      || url.pathname !== "/" || url.search || url.hash) {
    throw new Error("ADI_API_BASE_URL must be an HTTP(S) origin without credentials, path, query or fragment");
  }
  return url.origin;
}
