import { useState } from 'react';
import './index.css';
import UploadForm from './components/UploadForm';
import Dashboard from './components/Dashboard';

function App() {
  const [reportData, setReportData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUploadComplete = (data) => {
    setReportData(data);
    setIsLoading(false);
  };

  const handleUploadStart = () => {
    setIsLoading(true);
    setError(null);
    setReportData(null);
  };

  const handleError = (errMsg) => {
    setError(errMsg);
    setIsLoading(false);
  };

  const resetUpload = () => {
    setReportData(null);
    setError(null);
  };

  return (
    <div className="app-container">
      <header>
        <h1>Legal AI Platform</h1>
        <p>Intelligent Contract Analysis & Precedent Research</p>
      </header>

      <main>
        {error && (
          <div className="glass-panel" style={{ borderColor: 'var(--risk-high)', marginBottom: '2rem' }}>
            <h3 style={{ color: 'var(--risk-high)' }}>Error</h3>
            <p>{error}</p>
            <button className="btn-primary" onClick={resetUpload} style={{ marginTop: '1rem' }}>
              Try Again
            </button>
          </div>
        )}

        {!reportData && !isLoading && (
          <div className="animate-slide-up">
            <UploadForm 
              onUploadStart={handleUploadStart} 
              onUploadComplete={handleUploadComplete} 
              onError={handleError}
            />
          </div>
        )}

        {isLoading && (
          <div className="glass-panel animate-slide-up" style={{ textAlign: 'center', padding: '4rem' }}>
            <div className="loader" style={{ width: '48px', height: '48px', marginBottom: '1rem' }}></div>
            <h2>Processing Document...</h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
              Our AI pipelines are extracting text, classifying clauses, and running the risk engine. This may take a moment.
            </p>
          </div>
        )}

        {reportData && !isLoading && (
          <div className="animate-slide-up">
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
              <button className="btn-primary" onClick={resetUpload}>
                Analyze Another Document
              </button>
            </div>
            <Dashboard data={reportData} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
