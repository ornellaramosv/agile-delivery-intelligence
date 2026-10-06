import { getRetrospectiveCapacityHealth } from "../../../lib/capacity-health";
import { RetrospectiveView, RetrospectiveUnavailable } from "../components/retrospective-view";
import "../../sprint-health/sprint-health.css";
import "../capacity-health.css";

export const dynamic = "force-dynamic";
export default async function CapacityRetrospectivePage() {
  let data;
  try { data = await getRetrospectiveCapacityHealth(); }
  catch { return <RetrospectiveUnavailable />; }
  return <RetrospectiveView data={data} />;
}
