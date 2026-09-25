import { useEffect, useState } from "react";

interface KPI {
  total_transactions: number;
  total_alerts: number;
  flagged_transactions: number;
  protection_rate: number;
  avg_risk_score: number;
}

function computeThreatLevel(k: KPI | null): { level: string; score: number } {
  if (!k) return { level: "Low", score: 0 };
  // Simple heuristic: blend alerts density and avg risk
  const density = k.total_transactions > 0 ? k.flagged_transactions / k.total_transactions : 0;
  const score = Math.min(100, Math.round(50 * density + 0.5 * k.avg_risk_score));
  let level = "Low";
  if (score >= 80) level = "Severe";
  else if (score >= 60) level = "High";
  else if (score >= 40) level = "Elevated";
  else if (score >= 20) level = "Guarded";
  return { level, score };
}

export const ThreatGauge = () => {
  const [kpis, setKpis] = useState<KPI | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/analytics/kpis");
        if (!res.ok) throw new Error("Failed to load KPIs");
        setKpis(await res.json());
      } catch (e: any) {
        setError(e?.message || "Failed to load KPIs");
      }
    };
    run();
  }, []);

  const { level, score } = computeThreatLevel(kpis);

  return (
    <div className="border-border shadow-soft rounded-lg p-6 bg-card">
      <div className="text-sm text-muted-foreground mb-2">System Threat Level</div>
      {error && <div className="text-destructive text-sm mb-2">{error}</div>}
      <div className="flex items-center gap-6">
        <div className="relative h-32 w-32">
          <svg viewBox="0 0 100 50" className="block">
            <path d="M10,50 A40,40 0 0 1 90,50" fill="none" stroke="#e5e7eb" strokeWidth="8" />
            <path d={`M10,50 A40,40 0 ${score>50?1:0} 1 ${10+0.8*score},${50 - Math.sqrt(Math.max(0,1600 - (0.8*score-40)**2))}`} fill="none" stroke="#ef4444" strokeWidth="8" />
          </svg>
          <div className="absolute inset-0 flex items-end justify-center pb-2 text-xl font-bold">{score}</div>
        </div>
        <div>
          <div className="text-2xl font-bold">{level}</div>
          <div className="text-sm text-muted-foreground">Based on recent alerts and risk</div>
        </div>
      </div>
    </div>
  );
};


