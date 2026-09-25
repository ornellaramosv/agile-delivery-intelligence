import { QualityHeading } from "./components/quality-rework-view";
import "../sprint-health/sprint-health.css";
import "./quality-rework.css";

export default function LoadingQualityRework() {
  return <div className="sprint-health quality-rework"><QualityHeading />
    <section className="page-state" role="status" aria-live="polite" aria-busy="true">
      <h2>Loading Quality &amp; Rework…</h2><p>Retrieving QA outcomes, rework evidence, and task effort.</p>
    </section></div>;
}
