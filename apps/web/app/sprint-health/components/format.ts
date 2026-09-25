import type { Cause, Movement } from "../../../lib/burndown";

export const causeLabels: Record<Cause["type"], string> = {
  story_closed: "Story closed",
  scope_added: "Scope added after baseline",
  closure_blocking_bug_created: "Bug added rework",
  closure_blocking_bug_resolved: "Bug resolved",
};

export const movementLabels: Record<Movement, string> = { up: "Up", flat: "Flat", down: "Down" };

export function signed(value: number | null): string {
  if (value === null) return "—";
  return value > 0 ? `+${value}` : value < 0 ? `−${Math.abs(value)}` : "0";
}

export function dateLabel(value: string): string {
  return new Intl.DateTimeFormat("en", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" })
    .format(new Date(`${value}T00:00:00Z`));
}
