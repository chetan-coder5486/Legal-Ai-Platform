import { useState } from 'react';
import axios from 'axios';
import { AlertTriangle, ShieldCheck, FileText, CheckCircle2, Loader2, ChevronDown } from 'lucide-react';

const RiskBadge = ({ level }) => (
  <span className={`risk-badge ${level.toLowerCase()}`}>
    {level} RISK
  </span>
);

const ClauseCard = ({ clause, idx }) => {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleExplain = async () => {
    if (explanation) {
      setExpanded(!expanded);
      return;
    }

    setLoading(true);
    setExpanded(true);

    try {
      const response = await axios.post('http://localhost:8000/api/explain-clause', {
        clause_text: clause.clause_text,
        clause_type: clause.type,
        risk_level: clause.risk_level,
        risk_reason: clause.risk_reason
      });
      setExplanation(response.data.explanation);
    } catch (err) {
      setExplanation('Failed to generate explanation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`clause-item risk-${clause.risk_level.toLowerCase()}`}>
      
      {/* Clause header */}
      <div className="clause-header">
        <span className="clause-type">{clause.type}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Confidence: {(clause.confidence * 100).toFixed(0)}%
          </span>
          <RiskBadge level={clause.risk_level} />
        </div>
      </div>

      {/* Clause text */}
      <div style={{
        margin: '1rem 0',
        padding: '1rem',
        background: 'rgba(0,0,0,0.2)',
        borderRadius: '4px',
        fontStyle: 'italic',
        fontSize: '0.9rem',
        lineHeight: '1.6'
      }}>
        "{clause.clause_text}"
      </div>

      {/* Risk reason */}
      <div style={{
        fontSize: '0.85rem',
        color: 'var(--text-secondary)',
        marginBottom: '0.75rem'
      }}>
        {clause.risk_reason}
      </div>

      {/* Explain button */}
      <button
        onClick={handleExplain}
        disabled={loading}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.5rem 1rem',
          fontSize: '0.85rem',
          cursor: loading ? 'not-allowed' : 'pointer',
          background: 'transparent',
          border: '1px solid var(--accent-color)',
          borderRadius: '6px',
          color: 'var(--accent-color)',
          transition: 'all 0.2s'
        }}
      >
        {loading ? (
          <>
            <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
            Generating explanation...
          </>
        ) : explanation ? (
          <>
            <ChevronDown size={14} style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }} />
            {expanded ? 'Hide explanation' : 'Show explanation'}
          </>
        ) : (
          '✦ Explain this clause'
        )}
      </button>

      {/* AI Explanation — only shown after button click */}
      {expanded && explanation && (
        <div style={{
          marginTop: '0.75rem',
          padding: '1rem',
          background: 'rgba(99, 179, 237, 0.08)',
          border: '1px solid rgba(99, 179, 237, 0.2)',
          borderRadius: '8px',
          fontSize: '0.9rem',
          lineHeight: '1.7',
          color: 'var(--text-primary)',
          whiteSpace: 'pre-line'
        }}>
          {explanation}
        </div>
      )}

    </div>
  );
};


const Dashboard = ({ data }) => {
  const { results, task } = data;

  const isContractAnalysis = task === 'analyze_contract';
  const isSummary = task === 'summarize_case';

  const analysisPayload = results.contract_analysis || {};
  const clauses = analysisPayload.analyzed_clauses || [];

  const highRiskCount = clauses.filter(c => c.risk_level === 'HIGH').length;
  const mediumRiskCount = clauses.filter(c => c.risk_level === 'MEDIUM').length;
  const safeCount = clauses.filter(c => c.risk_level === 'LOW').length;

  return (
    <div className="dashboard">

      {/* Header */}
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
          {/* Metrics */}
          <div className="dashboard-grid" style={{ marginBottom: '2rem' }}>
            <div className="glass-panel metric-card" style={{ borderLeft: '4px solid var(--risk-high)' }}>
              <h3>High Risk Clauses</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span className="value">{highRiskCount}</span>
                {highRiskCount > 0 && <AlertTriangle color="var(--risk-high)" size={32} />}
              </div>
            </div>

            <div className="glass-panel metric-card" style={{ borderLeft: '4px solid var(--risk-medium)' }}>
              <h3>Medium Risk Clauses</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span className="value">{mediumRiskCount}</span>
              </div>
            </div>

            <div className="glass-panel metric-card" style={{ borderLeft: '4px solid var(--risk-low)' }}>
              <h3>Standard Clauses</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span className="value">{safeCount}</span>
                <ShieldCheck color="var(--risk-low)" size={32} />
              </div>
            </div>

            <div className="glass-panel metric-card" style={{ borderLeft: '4px solid var(--accent-color)' }}>
              <h3>Total Clauses Analyzed</h3>
              <div className="value">
                {analysisPayload.total_clauses_analyzed ?? clauses.length}
              </div>
            </div>
          </div>

          {/* Clause breakdown */}
          <div className="glass-panel">
            <h2 style={{ marginBottom: '0.5rem' }}>Clause Breakdown & Risk Analysis</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
              Click "Explain this clause" on any clause to get an AI-generated plain-English explanation.
            </p>

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