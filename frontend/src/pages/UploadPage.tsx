import { DatasetUpload } from "@/components/DatasetUpload";

const UploadPage = () => {
  return (
    <div className="min-h-screen bg-background">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Upload & Analyze</h1>
          <p className="text-muted-foreground">Upload a CSV to run offline analysis using the pre-trained model.</p>
        </div>
        <DatasetUpload />
      </main>
    </div>
  );
};

export default UploadPage;


