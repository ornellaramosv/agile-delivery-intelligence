import { getSprintBurndown } from "../../lib/burndown";
import { SprintHealthUnavailable, SprintHealthView } from "./components/sprint-health-view";
import "./sprint-health.css";

export const dynamic = "force-dynamic";

export default async function SprintHealthPage() {
  let data;
  try {
    data = await getSprintBurndown();
  } catch {
    return <SprintHealthUnavailable />;
  }
  return <SprintHealthView data={data} />;
}
