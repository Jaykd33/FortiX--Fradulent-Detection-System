import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Transaction {
  id: string;
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
}

interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

interface TransactionsResponse {
  transactions: Transaction[];
  pagination: Pagination;
}

const TransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchTransactions();
  }, [currentPage]);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://127.0.0.1:8000/api/tables/transactions?page=${currentPage}&page_size=50`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch transactions');
      }

      const data: TransactionsResponse = await response.json();
      setTransactions(data.transactions);
      setPagination(data.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchTransactions();
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`http://127.0.0.1:8000/api/tables/transactions/search?query=${encodeURIComponent(searchQuery)}&page=${currentPage}&page_size=50`);
      
      if (!response.ok) {
        throw new Error('Failed to search transactions');
      }

      const data: TransactionsResponse = await response.json();
      setTransactions(data.transactions);
      setPagination(data.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'flagged':
        return 'text-red-600 bg-red-100';
      case 'review':
        return 'text-yellow-600 bg-yellow-100';
      case 'processed':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskScoreColor = (score: number | null) => {
    if (score === null) return 'text-gray-600';
    if (score >= 70) return 'text-red-600';
    if (score >= 30) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading && transactions.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">Loading transactions...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">All Transactions Log</h1>
      
      {/* Search Bar */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Search Transactions</CardTitle>
          <CardDescription>Search by sender ID, receiver ID, or transaction type</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Input
              type="text"
              placeholder="Enter search term..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button onClick={handleSearch}>Search</Button>
            <Button variant="outline" onClick={() => {
              setSearchQuery('');
              fetchTransactions();
            }}>Clear</Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="text-center text-red-600">
              <p>{error}</p>
              <Button onClick={fetchTransactions} className="mt-2">Retry</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transactions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Transactions</CardTitle>
          <CardDescription>
            {pagination && `Showing ${transactions.length} of ${pagination.total} transactions`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-300">
              <thead>
                <tr className="bg-gray-50">
                  <th className="border border-gray-300 px-4 py-2 text-left">ID</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Amount</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Type</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Sender</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Receiver</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Risk Score</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Status</th>
                  <th className="border border-gray-300 px-4 py-2 text-left">Created At</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((transaction) => (
                  <tr key={transaction.id} className="hover:bg-gray-50">
                    <td className="border border-gray-300 px-4 py-2 font-mono text-sm">
                      {transaction.id.substring(0, 8)}...
                    </td>
                    <td className="border border-gray-300 px-4 py-2">
                      {transaction.currency} {transaction.amount.toLocaleString()}
                    </td>
                    <td className="border border-gray-300 px-4 py-2">{transaction.transaction_type}</td>
                    <td className="border border-gray-300 px-4 py-2">{transaction.sender_id}</td>
                    <td className="border border-gray-300 px-4 py-2">{transaction.receiver_id}</td>
                    <td className={`border border-gray-300 px-4 py-2 font-semibold ${getRiskScoreColor(transaction.risk_score)}`}>
                      {transaction.risk_score !== null ? transaction.risk_score.toFixed(1) : 'N/A'}
                    </td>
                    <td className="border border-gray-300 px-4 py-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(transaction.status)}`}>
                        {transaction.status}
                      </span>
                    </td>
                    <td className="border border-gray-300 px-4 py-2 text-sm">
                      {transaction.created_at ? new Date(transaction.created_at).toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

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

export default TransactionsPage;
