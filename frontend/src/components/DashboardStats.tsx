import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, AlertTriangle, Shield, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import { apiService, KPIData } from "@/services/api";

export const DashboardStats = () => {
  const [kpis, setKpis] = useState<KPIData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchKPIs = async () => {
      try {
        const data = await apiService.getKPIs();
        setKpis(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch KPIs');
        console.error('Error fetching KPIs:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchKPIs();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchKPIs, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        {[...Array(4)].map((_, index) => (
          <Card key={index} className="border-border shadow-soft">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-20 bg-muted animate-pulse rounded" />
              <div className="h-4 w-4 bg-muted animate-pulse rounded" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-24 bg-muted animate-pulse rounded mb-2" />
              <div className="h-3 w-32 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        <Card className="col-span-full border-destructive">
          <CardContent className="pt-6">
            <div className="text-center text-destructive">
              <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load dashboard data</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const stats = kpis
    ? [
        {
          title: "Total Transactions",
          value: Number(kpis.total_transactions ?? 0).toLocaleString(),
          change: kpis.transactions_change ?? "+0%",
          icon: Activity,
          color: "text-primary",
        },
        {
          title: "Fraud Detected",
          value: Number(kpis.fraud_detected ?? 0).toLocaleString(),
          change: kpis.fraud_change ?? "0%",
          icon: AlertTriangle,
          color: "text-risk-high",
        },
        {
          title: "Protection Rate",
          value: `${Number(kpis.protection_rate ?? 0).toFixed(2)}%`,
          change: kpis.protection_change ?? "0%",
          icon: Shield,
          color: "text-risk-low",
        },
        {
          title: "Avg Risk Score",
          value: Number(kpis.avg_risk_score ?? 0).toFixed(1),
          change: kpis.risk_score_change ?? "0%",
          icon: TrendingUp,
          color: "text-risk-medium",
        },
      ]
    : [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
      {stats.map((stat, index) => (
        <Card key={index} className="border-border shadow-soft">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {stat.title}
            </CardTitle>
            <stat.icon className={`h-4 w-4 ${stat.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{stat.value}</div>
            <p className="text-xs text-muted-foreground">
              <span className={stat.change.startsWith('+') ? 'text-risk-low' : 'text-risk-high'}>
                {stat.change}
              </span>{' '}
              from last month
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};