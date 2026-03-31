import { AlertTriangle, ShieldCheck, Info, FileText, CheckCircle2 } from 'lucide-react';

const Dashboard = ({ data }) => {
  const { results, task } = data;
  
  // Destructure results based on task type
  const isContractAnalysis = task === 'analyze_contract';
  const isSummary = task === 'summarize_case';
  
  const analysisPayload = results.contract_analysis || {};
  const clauses = analysisPayload.analyzed_clauses || [];
  
  // Calculate metrics
  const highRiskCount = clauses.filter(c => c.risk_level === 'HIGH').length;
  const mediumRiskCount = clauses.filter(c => c.risk_level === 'MEDIUM').length;
  const safeCount = clauses.filter(c => c.risk_level === 'LOW').length;

  return (
    <div className="dashboard">
      {/* Overview Headings */}
      <div className="glass-panel" style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <FileText size={32} color="var(--accent-color)" />
          <h2>Analysis Report: {data.filename}</h2>
        </div>
        <p style={{ color: 'var(--text-secondary)' }}>
          Processed {(results.metadata?.doc_length_chars / 1024).toFixed(2)} KB of text.
        </p>
      </div>

      {isContractAnalysis && (
        <>
          {/* Top Metrics Grid */}
          <div className="dashboard-grid" style={{ marginBottom: '2rem' }}>
            <div className="glass-panel metric-card" style={{ borderLeft: '4px solid var(--risk-high)' }}>
              <h3>High Risk Clauses</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span className="value">{highRiskCount}</span>
                {highRiskCount > 0 && <AlertTriangle color="var(--risk-high)" size={32} />}
              </div>
            </div>
            
            <div className="glass-panel metric-card" style={{ borderLeft: '4px solid var(--risk-low)' }}>
              <h3>Standard Clauses</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span className="value">{safeCount}</span>
                <ShieldCheck color="var(--risk-low)" size={32} />
              </div>
            </div>
            
             <div className="glass-panel metric-card" style={{ borderLeft: '4px solid var(--accent-color)', gridColumn: 'span 2' }}>
              <h3>Total Clauses Analyzed</h3>
              <div className="value">{analysisPayload.total_clauses_analyzed ?? analysisPayload.total_clauses_detected ?? clauses.length}</div>
            </div>
          </div>

          {/* Clause Detail Breakdown */}
          <div className="glass-panel">
            <h2>Clause Breakdown & Risk Engine Explanations</h2>
            
            <div className="clause-list">
              {clauses.map((clause, idx) => (
                <div key={idx} className={`clause-item risk-${clause.risk_level.toLowerCase()}`}>
                  <div className="clause-header">
                    <span className="clause-type">{clause.type}</span>
                    <span className={`risk-badge ${clause.risk_level.toLowerCase()}`}>
                      {clause.risk_level} RISK
                    </span>
                  </div>
                  
                  <div style={{ margin: '1rem 0', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '4px', fontStyle: 'italic' }}>
                    "{clause.clause_text}"
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', color: 'var(--text-secondary)' }}>
                    <Info size={20} color="var(--accent-color)" style={{ minWidth: '20px' }} />
                    <div style={{ whiteSpace: 'pre-line' }}>
                      {clause.explanation}
                    </div>
                  </div>
                </div>
              ))}
              
              {clauses.length === 0 && (
                <p>No clauses could be parsed from the document.</p>
              )}
            </div>
          </div>
        </>
      )}

      {isSummary && (
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
             <CheckCircle2 color="var(--risk-low)" size={32} />
             <h2>AI Summary Generated</h2>
          </div>
          
          <div style={{ 
            background: 'rgba(0,0,0,0.3)', 
            padding: '2rem', 
            borderRadius: '8px',
            fontSize: '1.1rem',
            lineHeight: '1.8',
            whiteSpace: 'pre-line'
          }}>
            {results.summary_data?.final_summary || "Summarization failed or returned empty."}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
