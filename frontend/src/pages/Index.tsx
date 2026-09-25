import { DashboardStats } from "@/components/DashboardStats";
import { TransactionMonitor } from "@/components/TransactionMonitor";
import { RiskScoreChart } from "@/components/RiskScoreChart";
import { FraudAlerts } from "@/components/FraudAlerts";
import { GeoFraudMap } from "@/components/GeoFraudMap";
import { ThreatGauge } from "@/components/ThreatGauge";

const Index = () => {
  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          Fraud Detection Dashboard
        </h1>
        <p className="text-muted-foreground">
          Monitor transactions, detect fraud patterns, and protect your business
          in real-time
        </p>
      </div>

      <div className="space-y-8">
        <DashboardStats />

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          <GeoFraudMap />
          <ThreatGauge />
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          <TransactionMonitor />
          <div className="space-y-8">
            <RiskScoreChart />
            <FraudAlerts />
          </div>
        </div>
      </div>
    </main>
  );
};

export default Index;
