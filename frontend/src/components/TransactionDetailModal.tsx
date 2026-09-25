import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { MapPin, ShieldAlert, Route as RouteIcon, Lock } from "lucide-react";
import { apiService, LiveTransaction } from "@/services/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  transactionId: string | null;
}

export const TransactionDetailModal = ({ open, onOpenChange, transactionId }: Props) => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!transactionId) return;
      setLoading(true);
      setError(null);
      try {
        const res = await apiService.getTransaction(transactionId);
        setData(res);
      } catch (e: any) {
        setError(e?.message || "Failed to load transaction");
      } finally {
        setLoading(false);
      }
    };
    if (open) fetchData();
  }, [open, transactionId]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Transaction Details</DialogTitle>
        </DialogHeader>
        {loading && <div className="py-6">Loading...</div>}
        {error && <div className="py-6 text-destructive">{error}</div>}
        {data && (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">ID</div>
              <div className="font-mono break-all">{data.id}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Timestamp</div>
              <div>{new Date(data.created_at).toLocaleString()}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Amount</div>
              <div>₹{data.amount.toLocaleString()} {data.currency}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Type</div>
              <div>{data.transaction_type}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Sender</div>
              <div>{data.sender_id || '-'}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Receiver</div>
              <div>{data.receiver_id || '-'}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Risk Score</div>
              <div>{data.risk_score ?? 0}%</div>
            </div>
            <div>
              <div className="text-muted-foreground">Status</div>
              <div>{data.status}</div>
            </div>
          </div>
        )}
        {data?.risk_factors && data.risk_factors.length > 0 && (
          <div className="mt-6">
            <div className="font-semibold mb-2 text-foreground">AI Risk Analysis</div>
            <div className="space-y-2">
              {data.risk_factors.map((rf: string, idx: number) => {
                const icon = rf.toLowerCase().includes("location") ? <MapPin className="h-4 w-4 text-red-400" />
                  : rf.toLowerCase().includes("auth") ? <Lock className="h-4 w-4 text-yellow-400" />
                  : rf.toLowerCase().includes("distance") ? <RouteIcon className="h-4 w-4 text-orange-400" />
                  : <ShieldAlert className="h-4 w-4 text-red-400" />;
                return (
                  <div key={idx} className="flex items-start gap-2 p-2 rounded bg-muted/40">
                    {icon}
                    <span className="text-sm text-foreground">{rf}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};


