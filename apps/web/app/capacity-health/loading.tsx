import { CapacityHeading } from "./components/capacity-health-view";
import "../sprint-health/sprint-health.css";
import "./capacity-health.css";

export default function LoadingCapacityHealth() {
  return <div className="sprint-health capacity-health"><CapacityHeading />
    <section className="page-state" role="status" aria-live="polite" aria-busy="true">
      <h2>Loading Capacity Health…</h2><p>Retrieving capacity, sprint progress and supporting evidence.</p>
    </section></div>;
}
