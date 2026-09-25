// src/components/DatasetUpload.tsx
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, Database, FileText } from "lucide-react";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export const DatasetUpload: React.FC = () => {
  const [testFile, setTestFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [datasetInfo, setDatasetInfo] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDatasetInfo();
  }, []);

  const handleFileChange = (file: File | null) => {
    setTestFile(file);
  };

  const handleUpload = async () => {
    setUploadStatus(null);

    if (!testFile) {
      setUploadStatus("Please select a CSV file to analyze");
      return;
    }

    try {
      setUploading(true);
      setUploadStatus("Analyzing dataset…");

      // Send the test file to the analyze endpoint
      const form = new FormData();
      form.append("file", testFile, testFile.name);

      const res = await fetch("http://127.0.0.1:8000/api/dataset/analyze", {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        // Try to surface backend error details
        let detail = "";
        try {
          const data = await res.json();
          detail = data?.detail || JSON.stringify(data);
        } catch {
          detail = await res.text();
        }
        throw new Error(`${res.status} ${res.statusText}${detail ? " - " + detail : ""}`);
      }

      const data = await res.json();

      setUploadStatus(`✅ Analysis complete! ${data.message}`);
      
      // Redirect to analytics page after successful upload
      setTimeout(() => {
        navigate('/analytics');
      }, 2000);
      
    } catch (err: any) {
      setUploadStatus(`❌ Analysis failed: ${err?.message || "Unknown error"}`);
      console.error("Analysis failed:", err);
    } finally {
      setUploading(false);
    }
  };

  const fetchDatasetInfo = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/dataset/dataset-info");
      if (!res.ok) return;
      const info = await res.json();
      setDatasetInfo(info);
    } catch (e) {
      console.error("Error fetching dataset info:", e);
    }
  };

  return (
    <Card className="border-border shadow-soft">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5 text-primary" />
          Transaction Analysis
        </CardTitle>
        <CardDescription>
          Upload a test dataset to analyze transactions using our pre-trained fraud detection model
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Current Dataset Info */}
        {datasetInfo && (
          <div className="p-4 bg-muted rounded-lg">
            <h4 className="font-medium mb-2">Current Dataset</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Total Transactions:</span>
                <span className="ml-2 font-medium">
                  {datasetInfo.total_transactions?.toLocaleString?.() ?? datasetInfo.total_transactions}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Flagged Transactions:</span>
                <span className="ml-2 font-medium text-risk-high">
                  {datasetInfo.flagged_transactions?.toLocaleString?.() ?? datasetInfo.flagged_transactions}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Total Alerts:</span>
                <span className="ml-2 font-medium">
                  {datasetInfo.total_alerts?.toLocaleString?.() ?? datasetInfo.total_alerts}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Fraud Rate:</span>
                <span className="ml-2 font-medium">
                  {datasetInfo.fraud_rate?.toFixed?.(2) ?? datasetInfo.fraud_rate}%
                </span>
              </div>
            </div>
          </div>
        )}

        {/* File Upload Form */}
        <div className="space-y-4">
          {/* Test Dataset */}
          <div className="space-y-2">
            <Label htmlFor="test-file" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Test Dataset (CSV file)
            </Label>
            <Input
              id="test-file"
              type="file"
              accept=".csv"
              onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
              disabled={uploading}
            />
            {testFile && (
              <p className="text-sm text-muted-foreground">
                Selected: {testFile.name} ({(testFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>
        </div>

        {/* Upload Button */}
        <Button
          onClick={handleUpload}
          disabled={uploading || !testFile}
          className="w-full"
        >
          {uploading ? (
            <>
              <Upload className="h-4 w-4 mr-2 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Upload className="h-4 w-4 mr-2" />
              Upload & Analyze
            </>
          )}
        </Button>

        {/* Upload Status */}
        {uploadStatus && (
          <div
            className={`p-3 rounded-lg text-sm ${
              uploadStatus.startsWith("✅")
                ? "bg-green-50 text-green-700 border border-green-200"
                : uploadStatus.startsWith("❌")
                ? "bg-red-50 text-red-700 border border-red-200"
                : "bg-blue-50 text-blue-700 border border-blue-200"
            }`}
          >
            {uploadStatus}
          </div>
        )}

        {/* Instructions */}
        <div className="text-sm text-muted-foreground space-y-2">
          <p><strong>Instructions:</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Upload a CSV file containing transaction data to analyze</li>
            <li>The system will clear existing data and perform fresh analysis</li>
            <li>CSV columns should include: amount, transaction_type, sender_id, receiver_id, etc.</li>
            <li>After analysis, you'll be redirected to the Analytics page</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};
