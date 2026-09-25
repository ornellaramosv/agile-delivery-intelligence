import type { FirstPassOutcome } from "../../../lib/quality-rework";
export const formatRate = (rate: number | null) => rate === null ? "Unavailable" :
  new Intl.NumberFormat("en", { style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(rate);
export const outcomeLabel = (outcome: FirstPassOutcome) => outcome === null ? "Not yet determined" : {
  passed: "Passed", failed: "Failed", not_reached_qa: "Not reached QA", excluded: "Excluded",
}[outcome];
