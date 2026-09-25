import { getSprintDeliveryFlow } from "../../lib/delivery-flow";
import { DeliveryFlowView, DeliveryFlowUnavailable } from "./components/delivery-flow-view";
import "../sprint-health/sprint-health.css";
import "./delivery-flow.css";

export const dynamic = "force-dynamic";

export default async function DeliveryFlowPage() {
  let data;
  try {
    data = await getSprintDeliveryFlow();
  } catch {
    return <DeliveryFlowUnavailable />;
  }
  return <DeliveryFlowView data={data} />;
}
