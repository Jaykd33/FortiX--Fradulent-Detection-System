// API service for FortiX fraud detection system
const API_BASE_URL = 'http://localhost:8000';

export interface KPIData {
  total_transactions: number;
  fraud_detected: number;
  protection_rate: number;
  false_positives: number;
  avg_risk_score: number;
  high_risk_transactions: number;
}

export interface LiveTransaction {
  id: string;
  created_at: string;
  amount: number;
  currency: string;
  transaction_type: string;
  sender_id: string | null;
  receiver_id: string | null;
  risk_score: number | null;
  status: string;
}

export interface RiskTrendPoint {
  timestamp: string;
  avg_risk_score: number;
  transaction_count: number;
}

export interface RiskTrends {
  trends: RiskTrendPoint[];
  period: string;
}

export interface Alert {
  id: string;
  transaction_id: string;
  created_at: string;
  severity: string;
  rule_name: string;
  description: string | null;
  is_active: boolean;
  transaction_amount: number | null;
  transaction_type: string | null;
}

export interface FeedbackRequest {
  alert_id: string;
  analyst_id?: string;
  feedback_type: string;
  comments?: string | null;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Dashboard APIs
  async getKPIs(): Promise<KPIData> {
    return this.request<KPIData>('/api/dashboard/kpis');
  }

  async getLiveTransactions(limit: number = 10): Promise<LiveTransaction[]> {
    return this.request<LiveTransaction[]>(`/api/dashboard/live_transactions?limit=${limit}`);
  }

  async getRiskScoreTrends(period: string = '24h'): Promise<RiskTrends> {
    return this.request<RiskTrends>(`/api/dashboard/risk_score_trends?period=${period}`);
  }

  async getActiveAlerts(limit: number = 20): Promise<Alert[]> {
    const response = await this.request<
      Alert[] | { alerts?: Alert[]; data?: Alert[] }
    >(`/api/dashboard/active_alerts?limit=${limit}`);

    if (Array.isArray(response)) {
      return response;
    }

    return response.alerts ?? response.data ?? [];
  }

  async submitFeedback(feedback: FeedbackRequest): Promise<any> {
    return this.request('/api/dashboard/feedback', {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
  }

  // Transaction APIs
  async getTransactions(): Promise<LiveTransaction[]> {
    return this.request<LiveTransaction[]>('/api/v1/transactions');
  }

  async createTransaction(transaction: Partial<LiveTransaction>): Promise<LiveTransaction> {
    return this.request<LiveTransaction>('/api/v1/transactions', {
      method: 'POST',
      body: JSON.stringify(transaction),
    });
  }

  async getTransaction(transactionId: string): Promise<LiveTransaction> {
    return this.request<LiveTransaction>(`/api/v1/transactions/${transactionId}`);
  }
}

export const apiService = new ApiService();
export default apiService;
