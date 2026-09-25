import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Eye, Clock, CreditCard, User, Activity, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { apiService, LiveTransaction } from "@/services/api";
import { TransactionDetailModal } from "@/components/TransactionDetailModal";

export const TransactionMonitor = () => {
  const [transactions, setTransactions] = useState<LiveTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const fetchTransactions = async () => {
    try {
      const data = await apiService.getLiveTransactions(10);
      setTransactions(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch transactions');
      console.error('Error fetching transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
    
    // Refresh every 10 seconds for live monitoring
    const interval = setInterval(fetchTransactions, 10000);
    return () => clearInterval(interval);
  }, []);

  const getRiskBadge = (score: number | null, status: string) => {
    const riskScore = score ?? 0;

    if (status === "flagged" || status === "blocked") {
      return (
        <Badge className="bg-red-600 text-white hover:bg-red-600">
          High Risk
        </Badge>
      );
    }

    if (riskScore >= 70) {
      return (
        <Badge className="bg-red-600 text-white hover:bg-red-600">
          High Risk
        </Badge>
      );
    }

    if (riskScore >= 30) {
      return (
        <Badge className="bg-yellow-400 text-black hover:bg-yellow-400">
          Medium Risk
        </Badge>
      );
    }

    return (
      <Badge className="bg-green-600 text-white hover:bg-green-600">
        Low Risk
      </Badge>
    );
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case "CREDIT_CARD":
        return <CreditCard className="h-4 w-4" />;
      case "UPI":
        return <User className="h-4 w-4" />;
      default:
        return <CreditCard className="h-4 w-4" />;
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

  if (loading) {
    return (
      <Card className="border-border shadow-soft">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Live Transaction Monitor
          </CardTitle>
          <CardDescription>
            Real-time fraud detection and risk scoring
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(5)].map((_, index) => (
              <div key={index} className="flex items-center justify-between p-4 border border-border rounded-lg bg-card">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    {getChannelIcon("CREDIT_CARD")}
                    <div>
                      <p className="font-medium text-foreground">{index}</p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {formatTimeAgo("2024-01-01T00:00:00Z")}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-foreground">₹{index.toLocaleString()}</p>
                    <p className="text-sm text-muted-foreground">{index}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {getRiskBadge(index, "flagged")}
                  <span className="text-sm font-medium text-foreground">
                    {index}%
                  </span>
                  <Button size="sm" variant="outline" onClick={() => { setSelectedId(index); setDetailOpen(true); }}>
                    <Eye className="h-4 w-4" />
                  </Button>
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
            <Activity className="h-5 w-5 text-primary" />
            Live Transaction Monitor
          </CardTitle>
          <CardDescription>
            Real-time fraud detection and risk scoring
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="text-destructive mb-4">
              <Activity className="h-8 w-8 mx-auto mb-2" />
              <p>Failed to load transactions</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
            <Button onClick={fetchTransactions} variant="outline" size="sm">
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
          <Activity className="h-5 w-5 text-primary" />
          Live Transaction Monitor
        </CardTitle>
        <CardDescription>
          Real-time fraud detection and risk scoring
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {transactions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No recent transactions found
            </div>
          ) : (
            transactions.map((txn) => (
              <div key={txn.id} className="flex items-center justify-between p-4 border border-border rounded-lg bg-card">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    {getChannelIcon(txn.transaction_type)}
                    <div>
                      <p className="font-medium text-foreground">{txn.id}</p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        {formatTimeAgo(txn.created_at)}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-foreground">₹{txn.amount.toLocaleString()}</p>
                    <p className="text-sm text-muted-foreground">{txn.transaction_type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {getRiskBadge(txn.risk_score, txn.status)}
                  <span className="text-sm font-medium text-foreground">
                    {txn.risk_score || 0}%
                  </span>
                  <Button size="sm" variant="outline" onClick={() => { setSelectedId(txn.id); setDetailOpen(true); }}>
                    <Eye className="h-4 w-4" />
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