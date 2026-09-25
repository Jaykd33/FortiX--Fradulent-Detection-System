import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface Profile {
  user_id: string;
  avg_risk_score: number;
  most_common: { location: string | null; merchant_category: string | null; device_type: string | null };
  recent_transactions: Array<{
    id: string; amount: number; risk_score: number | null; status: string; transaction_type: string; location: string | null; merchant_category: string | null; device_type: string | null; created_at: string | null;
  }>;
  total_alerts: number;
}

const EntityExplorerPage = () => {
  const [userId, setUserId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);

  const search = async () => {
    setLoading(true);
    setError(null);
    setProfile(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/entities/user/${encodeURIComponent(userId)}`);
      if (!res.ok) throw new Error("User not found or server error");
      setProfile(await res.json());
    } catch (e: any) {
      setError(e?.message || "Failed to fetch user profile");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Entity Explorer</h1>
          <p className="text-muted-foreground">Search a user to analyze their behavioral baseline and recent activity.</p>
        </div>

        <div className="flex gap-2 mb-6">
          <Input value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="Enter User_ID (e.g., user_123)" />
          <Button onClick={search} disabled={!userId || loading}>Search</Button>
        </div>

        {loading && <div>Loading...</div>}
        {error && <div className="text-destructive">{error}</div>}

        {profile && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>User Profile: {profile.user_id}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Avg Risk Score</div>
                    <div className="text-xl font-semibold">{profile.avg_risk_score}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Common Location</div>
                    <div>{profile.most_common.location || '-'}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Common Device</div>
                    <div>{profile.most_common.device_type || '-'}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Common Merchant Category</div>
                    <div>{profile.most_common.merchant_category || '-'}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Total Alerts</div>
                    <div>{profile.total_alerts}</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  {profile.recent_transactions.map((t) => (
                    <div key={t.id} className="flex items-center justify-between p-3 border rounded">
                      <div className="flex flex-col">
                        <span className="font-mono text-xs">{t.id}</span>
                        <span>{t.transaction_type} · {t.location || '—'} · {t.merchant_category || '—'}</span>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">₹{t.amount.toLocaleString()}</div>
                        <div className="text-xs text-muted-foreground">Risk {t.risk_score ?? 0} · {t.status}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
};

export default EntityExplorerPage;


