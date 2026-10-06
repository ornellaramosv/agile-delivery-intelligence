export function hours(value: number | null, signed = false): string {
  if (value === null) return "Unavailable";
  return `${new Intl.NumberFormat("en", { maximumFractionDigits: 2, signDisplay: signed ? "exceptZero" : "auto" }).format(value)} h`;
}
export function words(value: string) { return value.replaceAll("_", " "); }
export function timestamp(value: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC" }).format(new Date(value)) + " UTC";
}
