import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';

interface KPI {
  total_transactions: number;
  total_alerts: number;
  flagged_transactions: number;
  protection_rate: number;
  avg_risk_score: number;
}

interface RiskDistribution {
  name: string;
  count: number;
}

interface FraudByType {
  type: string;
  count: number;
}

interface FraudOverTime {
  date: string;
  total_transactions: number;
  flagged_count: number;
  avg_risk_score: number;
}

interface RiskDriver { feature: string; importance: number }
interface FraudByMerchant { merchant_category: string; count: number }
interface FraudByAuth { method: string; count: number }

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const AnalyticsPage: React.FC = () => {
  const [kpis, setKpis] = useState<KPI | null>(null);
  const [riskDistribution, setRiskDistribution] = useState<RiskDistribution[]>([]);
  const [fraudByType, setFraudByType] = useState<FraudByType[]>([]);
  const [fraudOverTime, setFraudOverTime] = useState<FraudOverTime[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [riskDrivers, setRiskDrivers] = useState<RiskDriver[]>([]);
  const [fraudByMerchant, setFraudByMerchant] = useState<FraudByMerchant[]>([]);
  const [fraudByAuth, setFraudByAuth] = useState<FraudByAuth[]>([]);

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Fetch all analytics data in parallel
      const [kpisRes, riskRes, fraudTypeRes, fraudTimeRes, driversRes, merchRes, authRes] = await Promise.all([
        fetch('http://127.0.0.1:8000/api/analytics/kpis'),
        fetch('http://127.0.0.1:8000/api/analytics/risk_distribution'),
        fetch('http://127.0.0.1:8000/api/analytics/fraud_by_type'),
        fetch('http://127.0.0.1:8000/api/analytics/fraud_over_time'),
        fetch('http://127.0.0.1:8000/api/analytics/risk_drivers'),
        fetch('http://127.0.0.1:8000/api/analytics/fraud_by_merchant_category'),
        fetch('http://127.0.0.1:8000/api/analytics/fraud_by_auth_method'),
      ]);

      if (!kpisRes.ok || !riskRes.ok || !fraudTypeRes.ok || !fraudTimeRes.ok || !driversRes.ok || !merchRes.ok || !authRes.ok) {
        throw new Error('Failed to fetch analytics data');
      }

      const [kpisData, riskData, fraudTypeData, fraudTimeData, driversData, merchData, authData] = await Promise.all([
        kpisRes.json(),
        riskRes.json(),
        fraudTypeRes.json(),
        fraudTimeRes.json(),
        driversRes.json(),
        merchRes.json(),
        authRes.json(),
      ]);

      setKpis(kpisData);
      setRiskDistribution(riskData);
      setFraudByType(fraudTypeData);
      setFraudOverTime(fraudTimeData);
      setRiskDrivers(driversData.slice(0, 10));
      setFraudByMerchant(merchData);
      setFraudByAuth(authData);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading analytics data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center text-red-600">
          <h2 className="text-xl font-semibold mb-2">Error Loading Analytics</h2>
          <p>{error}</p>
          <button 
            onClick={fetchAnalyticsData}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">Analytics Dashboard</h1>
      
      {/* KPI Cards */}
      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Total Transactions</CardTitle>
              <CardDescription>All analyzed transactions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kpis.total_transactions.toLocaleString()}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Total Alerts</CardTitle>
              <CardDescription>High-risk transactions flagged</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{kpis.total_alerts.toLocaleString()}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Protection Rate</CardTitle>
              <CardDescription>Percentage of safe transactions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{kpis.protection_rate.toFixed(2)}%</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Average Risk Score</CardTitle>
              <CardDescription>Mean risk across all transactions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kpis.avg_risk_score.toFixed(1)}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Risk Score Distribution</CardTitle>
            <CardDescription>Distribution of risk scores across all transactions</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={riskDistribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Fraud by Type Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Fraud by Transaction Type</CardTitle>
            <CardDescription>Distribution of fraud by transaction type</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={fraudByType}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ type, percent }) => `${type} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {fraudByType.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Fraud Over Time Chart */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Fraud Trends Over Time</CardTitle>
          <CardDescription>Fraud incidents and risk scores over the last 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={fraudOverTime}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Line 
                yAxisId="left" 
                type="monotone" 
                dataKey="flagged_count" 
                stroke="#ff7300" 
                name="Flagged Transactions"
              />
              <Line 
                yAxisId="right" 
                type="monotone" 
                dataKey="avg_risk_score" 
                stroke="#8884d8" 
                name="Average Risk Score"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Risk Drivers */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>What Our AI Looks For</CardTitle>
          <CardDescription>Top feature importances from the current model</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={[...riskDrivers].reverse()} layout="vertical" margin={{ left: 80 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="feature" width={200} />
              <Tooltip />
              <Bar dataKey="importance" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Fraud by Merchant Category and Auth Method */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Fraud by Merchant Category</CardTitle>
            <CardDescription>Top business types associated with fraud</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={fraudByMerchant}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="merchant_category" interval={0} angle={-30} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Fraud by Authentication Method</CardTitle>
            <CardDescription>Distribution of fraudulent transactions by auth method</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={fraudByAuth} dataKey="count" nameKey="method" cx="50%" cy="50%" outerRadius={90} label>
                  {fraudByAuth.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AnalyticsPage;
