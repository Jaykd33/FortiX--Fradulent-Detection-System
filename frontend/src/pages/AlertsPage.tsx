import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface Alert {
  transaction_id: string;
  amount: number;
  currency: string;
  transaction_type: string;
  sender_id: string;
  receiver_id: string;
  device_fingerprint: string | null;
  ip_address: string | null;
  geo_location: string | null;
  risk_score: number | null;
  status: string;
  created_at: string;
  alert_severity: string;
  alert_rule_name: string;
  alert_description: string;
  alert_is_active: boolean;
}

interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

interface AlertsResponse {
  alerts: Alert[];
  pagination: Pagination;
}

const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    fetchAlerts();
  }, [currentPage]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://127.0.0.1:8000/api/tables/alerts?page=${currentPage}&page_size=50`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch alerts');
      }

      const data: AlertsResponse = await response.json();
      setAlerts(data.alerts);
      setPagination(data.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-red-600 text-white';
      case 'high':
        return 'bg-red-500 text-white';
      case 'medium':
        return 'bg-yellow-500 text-white';
      case 'low':
        return 'bg-blue-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getRiskScoreColor = (score: number | null) => {
    if (score === null) return 'text-gray-600';
    if (score >= 85) return 'text-red-700 font-bold';
    if (score >= 70) return 'text-red-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading && alerts.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading alerts...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">Flagged Alerts</h1>
      
      {error && (
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="text-center text-red-600">
              <p>{error}</p>
              <Button onClick={fetchAlerts} className="mt-2">Retry</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Card */}
      {pagination && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Alert Summary</CardTitle>
            <CardDescription>High-risk transactions requiring attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{pagination.total}</div>
                <div className="text-sm text-gray-600">Total Alerts</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {alerts.filter(a => a.alert_severity === 'Medium').length}
                </div>
                <div className="text-sm text-gray-600">Medium Risk</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {alerts.filter(a => a.alert_severity === 'High').length}
                </div>
                <div className="text-sm text-gray-600">High Risk</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alerts Table */}
      <Card>
        <CardHeader>
          <CardTitle>Alert Details</CardTitle>
          <CardDescription>
            {pagination && `Showing ${alerts.length} of ${pagination.total} flagged transactions`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-50">
                  <th className="border border-gray-300 px-4 py-2 text-left">Transaction ID</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Amount</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Type</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Sender</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Risk Score</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Severity</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Rule</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Description</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Created At</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert) => (
                  <tr key={alert.transaction_id} className="hover:bg-gray-50">
                    <td className="border border-gray-300 px-4 py-2 font-mono text-sm">
                      {alert.transaction_id.substring(0, 8)}...
                    </td>
                    <td className="border border-gray-300 px-4 py-2">
                      {alert.currency} {alert.amount.toLocaleString()}
                    </td>
                    <td className="border border-gray-300 px-4 py-2">{alert.transaction_type}</td>
                    <td className="border border-gray-300 px-4 py-2">{alert.sender_id}</td>
                    <td className={`border border-gray-300 px-4 py-2 font-semibold ${getRiskScoreColor(alert.risk_score)}`}>
                      {alert.risk_score !== null ? alert.risk_score.toFixed(1) : 'N/A'}
                    </td>
                    <td className="border border-gray-300 px-4 py-2">
                      <Badge className={getSeverityColor(alert.alert_severity)}>
                        {alert.alert_severity}
                      </Badge>
                    </td>
                    <td className="border border-gray-300 px-4 py-2 text-sm">
                      {alert.alert_rule_name}
                    </td>
                    <td className="border border-gray-300 px-4 py-2 text-sm max-w-xs truncate">
                      {alert.alert_description}
                    </td>
                    <td className="border border-gray-300 px-4 py-2 text-sm">
                      {alert.created_at ? new Date(alert.created_at).toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {alerts.length === 0 && !loading && (
            <div className="text-center py-8 text-gray-500">
              <p>No alerts found. Upload and analyze a dataset to see flagged transactions.</p>
            </div>
          )}

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <div className="text-sm text-gray-600">
                Page {pagination.page} of {pagination.total_pages}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage(prev => Math.min(pagination.total_pages, prev + 1))}
                  disabled={currentPage === pagination.total_pages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AlertsPage;
