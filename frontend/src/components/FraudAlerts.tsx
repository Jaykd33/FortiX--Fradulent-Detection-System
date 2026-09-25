import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Clock, Eye, CheckCircle, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { apiService, Alert } from "@/services/api";
import { TransactionDetailModal } from "@/components/TransactionDetailModal";

export const FraudAlerts = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const fetchAlerts = async () => {
    try {
      const data = await apiService.getActiveAlerts(20);
      setAlerts(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch alerts');
      console.error('Error fetching alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    
    // Refresh every 15 seconds for alerts
    const interval = setInterval(fetchAlerts, 15000);
    return () => clearInterval(interval);
  }, []);

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical":
        return <Badge variant="destructive" className="bg-risk-critical text-white">Critical</Badge>;
      case "high":
        return <Badge variant="destructive" className="bg-risk-high text-white">High</Badge>;
      case "medium":
        return <Badge variant="secondary" className="bg-risk-medium text-white">Medium</Badge>;
      case "low":
        return <Badge variant="default" className="bg-risk-low text-white">Low</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  const handleFeedback = async (alertId: string, feedbackType: string) => {
    try {
      await apiService.submitFeedback({
        alert_id: alertId,
        feedback_type: feedbackType,
        analyst_id: "dashboard_user",
        comments: `Marked as ${feedbackType} via dashboard`
      });
      
      // Refresh alerts after feedback
      fetchAlerts();
    } catch (err) {
      console.error('Error submitting feedback:', err);
    }
  };

  if (loading) {
    return (
      <Card className="border-border shadow-soft">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-risk-high" />
            Active Fraud Alerts
          </CardTitle>
          <CardDescription>
            Recent fraud detection alerts requiring attention
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(4)].map((_, index) => (
              <div key={index} className="flex items-center justify-between p-4 border border-border rounded-lg bg-card">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="h-6 w-16 bg-muted animate-pulse rounded" />
                    <div className="h-4 w-32 bg-muted animate-pulse rounded" />
                  </div>
                  <div className="h-4 w-48 bg-muted animate-pulse rounded mb-2" />
                  <div className="flex items-center gap-4">
                    <div className="h-3 w-20 bg-muted animate-pulse rounded" />
                    <div className="h-3 w-24 bg-muted animate-pulse rounded" />
                    <div className="h-3 w-16 bg-muted animate-pulse rounded" />
                  </div>
                </div>
                <div className="flex gap-2">
                  <div className="h-8 w-8 bg-muted animate-pulse rounded" />
                  <div className="h-8 w-8 bg-muted animate-pulse rounded" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-border shadow-soft">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-risk-high" />
            Active Fraud Alerts
          </CardTitle>
          <CardDescription>
            Recent fraud detection alerts requiring attention
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="text-destructive mb-4">
              <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load alerts</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
            <Button onClick={fetchAlerts} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border shadow-soft">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-risk-high" />
          Active Fraud Alerts
        </CardTitle>
        <CardDescription>
          Recent fraud detection alerts requiring attention
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {alerts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <CheckCircle className="h-8 w-8 mx-auto mb-2 text-risk-low" />
              <p>No active alerts</p>
              <p className="text-sm">All systems operating normally</p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div key={alert.id} className="flex items-center justify-between p-4 border border-border rounded-lg bg-card">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {getSeverityBadge(alert.severity)}
                    <span className="text-sm font-medium text-foreground">{alert.rule_name}</span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">{alert.description}</p>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatTimeAgo(alert.created_at)}
                    </div>
                    <span>TXN: {alert.transaction_id.slice(0, 8)}...</span>
                    {alert.transaction_amount && (
                      <span className="font-medium">₹{alert.transaction_amount.toLocaleString()}</span>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => { setSelectedId(alert.transaction_id); setDetailOpen(true); }}>
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button 
                    size="sm" 
                    variant="default" 
                    className="bg-primary"
                    onClick={() => handleFeedback(alert.id, "False Positive")}
                  >
                    <CheckCircle className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
        <TransactionDetailModal open={detailOpen} onOpenChange={setDetailOpen} transactionId={selectedId} />
      </CardContent>
    </Card>
  );
};