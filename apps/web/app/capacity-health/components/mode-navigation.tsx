import Link from "next/link";
import type { CapacityMode } from "../../../lib/capacity-health";

export function CapacityModeNavigation({ mode }: { mode: CapacityMode }) {
  return <nav className="capacity-mode-navigation" aria-label="Capacity Health mode">
    <Link href="/capacity-health" aria-current={mode === "current_sprint" ? "page" : undefined}>Current Sprint</Link>
    <Link href="/capacity-health/retrospective" aria-current={mode === "retrospective" ? "page" : undefined}>Retrospective</Link>
  </nav>;
}
