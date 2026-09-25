import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const GuidePage: React.FC = () => {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">FortiX User Guide</h1>
      
      <div className="space-y-6">
        {/* Key Metrics Section */}
        <Card>
          <CardHeader>
            <CardTitle>Key Metrics Explained</CardTitle>
            <CardDescription>Understanding the fraud detection metrics and scores</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-2">Risk Score</h3>
              <p className="text-gray-600">
                A score from 0 to 100 calculated by our AI model. It represents the probability that a transaction is fraudulent.
              </p>
              <ul className="mt-2 ml-4 list-disc text-gray-600">
                <li><strong>0-30:</strong> Low Risk - Transaction appears legitimate</li>
                <li><strong>30-70:</strong> Medium Risk - Transaction requires review</li>
                <li><strong>70-100:</strong> High Risk - Transaction is likely fraudulent</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Protection Rate</h3>
              <p className="text-gray-600">
                The percentage of all analyzed transactions that were <em>not</em> flagged as high-risk fraud. 
                A higher protection rate indicates better performance of the fraud detection system.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Flagged Transaction</h3>
              <p className="text-gray-600">
                Any transaction that the system's rules or AI model identified as high-risk (typically score &gt; 70). 
                These transactions require immediate attention and investigation.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Alert Severity Levels</h3>
              <ul className="ml-4 list-disc text-gray-600">
                <li><strong>Critical:</strong> Immediate action required - very high fraud probability</li>
                <li><strong>High:</strong> Urgent review needed - high fraud probability</li>
                <li><strong>Medium:</strong> Standard review - moderate fraud probability</li>
                <li><strong>Low:</strong> Routine monitoring - low fraud probability</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Charts Section */}
        <Card>
          <CardHeader>
            <CardTitle>How to Read the Charts</CardTitle>
            <CardDescription>Understanding the visualizations in the Analytics Dashboard</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-2">Risk Distribution (Bar Chart)</h3>
              <p className="text-gray-600">
                This chart shows you the spread of risk scores across all transactions. A healthy fraud detection system 
                should show a large bar on the "0-10" (Low Risk) end and very small bars for higher risks. 
                If you see large bars in the 70-100 range, it may indicate a high-fraud dataset or system calibration issues.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Fraud by Type (Pie Chart)</h3>
              <p className="text-gray-600">
                This shows you which transaction types (e.g., Credit Card, UPI, Net Banking) are responsible for the most fraud. 
                Use this information to understand patterns and focus your fraud prevention efforts on high-risk transaction types.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Fraud Over Time (Line Chart)</h3>
              <p className="text-gray-600">
                This line chart displays fraud trends over the last 30 days. The orange line shows flagged transactions count, 
                while the purple line shows the average risk score. Look for patterns, spikes, or trends that might indicate 
                emerging fraud threats or system performance changes.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Workflow Section */}
        <Card>
          <CardHeader>
            <CardTitle>How to Use FortiX</CardTitle>
            <CardDescription>Step-by-step guide to analyzing transactions</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-2">Step 1: Upload Dataset</h3>
              <p className="text-gray-600">
                Go to the Dashboard page and upload a CSV file containing your transaction data. 
                The file should include columns like amount, transaction_type, sender_id, receiver_id, etc. 
                The system will automatically analyze all transactions using the pre-trained fraud detection model.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Step 2: Review Analytics</h3>
              <p className="text-gray-600">
                After upload, you'll be redirected to the Analytics page where you can see:
              </p>
              <ul className="mt-2 ml-4 list-disc text-gray-600">
                <li>Key Performance Indicators (KPIs)</li>
                <li>Risk score distribution</li>
                <li>Fraud patterns by transaction type</li>
                <li>Fraud trends over time</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Step 3: Investigate Alerts</h3>
              <p className="text-gray-600">
                Navigate to the Alerts page to see all flagged transactions. Review high-risk transactions 
                and take appropriate action based on the risk scores and alert descriptions.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Step 4: Browse All Transactions</h3>
              <p className="text-gray-600">
                Use the Transactions page to search and browse all analyzed transactions. 
                You can search by sender ID, receiver ID, or transaction type to find specific transactions.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Technical Details Section */}
        <Card>
          <CardHeader>
            <CardTitle>Technical Information</CardTitle>
            <CardDescription>Details about the fraud detection system</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-2">Machine Learning Model</h3>
              <p className="text-gray-600">
                FortiX uses a Random Forest Classifier, which is an ensemble machine learning algorithm. 
                This model combines multiple decision trees to make highly accurate fraud predictions. 
                It's particularly effective for tabular data and provides good interpretability.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Features Used</h3>
              <p className="text-gray-600">
                The model analyzes various transaction features including:
              </p>
              <ul className="mt-2 ml-4 list-disc text-gray-600">
                <li>Transaction amount and currency</li>
                <li>Transaction type (Credit Card, UPI, etc.)</li>
                <li>Sender and receiver information</li>
                <li>Device fingerprinting data</li>
                <li>IP address and geolocation</li>
                <li>Time-based features (hour, day of week)</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-2">Model Performance</h3>
              <p className="text-gray-600">
                The pre-trained model has been evaluated on historical data and typically achieves:
              </p>
              <ul className="mt-2 ml-4 list-disc text-gray-600">
                <li>High accuracy in fraud detection</li>
                <li>Low false positive rates</li>
                <li>Good precision and recall for fraud cases</li>
                <li>Fast processing times for real-time analysis</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default GuidePage;
