import { getSprintQualityRework } from "../../lib/quality-rework";
import { QualityReworkView, QualityUnavailable } from "./components/quality-rework-view";
import "../sprint-health/sprint-health.css";
import "./quality-rework.css";

export const dynamic = "force-dynamic";
export default async function QualityReworkPage() {
  let data;
  try { data = await getSprintQualityRework(); }
  catch { return <QualityUnavailable />; }
  return <QualityReworkView data={data} />;
}
