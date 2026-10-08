import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <h1>ADI doesn&apos;t track the work. It explains the delivery.</h1>
      <p>Transform Agile execution data into delivery risk, causal context, and management traceability.</p>
      <p>Sprint Intelligence v0.1.0 is released and stable. Capacity Health v0.2.0 is feature-complete and pending final release.</p>
      <h2>Explore the delivery evidence</h2>
      <ul>
        <li><Link href="/sprint-health">Sprint Health</Link> explains remaining delivery work, daily movement, and its causes.</li>
        <li><Link href="/delivery-flow">Delivery Flow</Link> shows where User Stories are located and how they moved.</li>
        <li><Link href="/quality-rework">Quality &amp; Rework</Link> connects first-pass QA, rework cycles, defect evidence, and effort.</li>
        <li>Capacity Health: <Link href="/capacity-health">Current Sprint</Link> explains remaining DEV and QA capacity; <Link href="/capacity-health/retrospective">Retrospective</Link> traces sprint turning points and capacity evolution.</li>
      </ul>
      <p>All demo data is fictional. Analysis is at team level, not individual productivity. Capacity is not progress. SLA intelligence is not implemented.</p>
    </>
  );
}
