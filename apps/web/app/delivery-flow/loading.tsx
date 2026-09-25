import { DeliveryFlowHeading } from "./components/delivery-flow-view";
import "../sprint-health/sprint-health.css";
import "./delivery-flow.css";

export default function LoadingDeliveryFlow() {
  return <div className="sprint-health delivery-flow"><DeliveryFlowHeading />
    <section className="page-state" role="status" aria-live="polite" aria-busy="true">
      <h2>Loading Delivery Flow…</h2><p>Retrieving workflow snapshots and story movements.</p>
    </section>
  </div>;
}
