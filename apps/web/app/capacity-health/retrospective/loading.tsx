import { RetrospectiveHeading } from "../components/retrospective-view";
import "../../sprint-health/sprint-health.css";
import "../capacity-health.css";

export default function LoadingCapacityRetrospective() {
  return <div className="sprint-health capacity-health"><RetrospectiveHeading />
    <section className="page-state" role="status" aria-live="polite" aria-busy="true">
      <h2>Loading Retrospective…</h2><p>Retrieving final outcomes and sprint turning points.</p>
    </section></div>;
}
