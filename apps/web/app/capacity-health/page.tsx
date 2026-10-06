import { capacitySelection, getSprintCapacityHealth } from "../../lib/capacity-health";
import { CapacityHealthView, CapacityUnavailable } from "./components/capacity-health-view";
import "../sprint-health/sprint-health.css";
import "./capacity-health.css";

export const dynamic = "force-dynamic";
export default async function CapacityHealthPage({ searchParams }: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const selection = capacitySelection(await searchParams);
  let data;
  try { data = await getSprintCapacityHealth(selection); }
  catch { return <CapacityUnavailable selection={selection} />; }
  return <CapacityHealthView data={data} />;
}
