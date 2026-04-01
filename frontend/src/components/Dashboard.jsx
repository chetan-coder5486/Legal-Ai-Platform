import { useState } from 'react';
import axios from 'axios';
import { AlertTriangle, ShieldCheck, FileText, CheckCircle2, Loader2, ChevronDown, Download } from 'lucide-react';
import { usePDF } from 'react-to-pdf';

const RiskBadge = ({ level }) => (
  <span className={`risk-badge ${level.toLowerCase()}`}>
    {level} RISK
  </span>
);

const PrecedentMatch = ({ p, i }) => {
  const [expanded, setExpanded] = useState(false);
  const text = p.text || "";
  const shouldTruncate = text.length > 300;
  
  const displayText = shouldTruncate && !expanded ? text.slice(0, 300) + "..." : text;

  return (
    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: '4px', fontSize: '0.85rem' }}>
      <div style={{ fontWeight: 'bold', marginBottom: '0.25rem', color: 'var(--text-secondary)', fontSize: '0.75rem', display: 'flex', justifyContent: 'space-between' }}>
        <span>Document: {p.metadata?.source || 'Unknown'}</span>
        <span>Match #{i + 1}</span>
      </div>
      <div style={{ fontStyle: 'italic', lineHeight: '1.5', opacity: 0.9 }}>
        "{displayText}"
      </div>
      {shouldTruncate && (
        <button 
          onClick={() => setExpanded(!expanded)}
          data-html2canvas-ignore="true"
          style={{ 
            background: 'none', 
            border: 'none', 
            color: 'var(--accent-color)', 
            cursor: 'pointer', 
            fontSize: '0.75rem', 
            padding: 0, 
            marginTop: '0.5rem',
            textDecoration: 'underline'
          }}
        >
          {expanded ? "Show Less" : "Read More"}
        </button>
      )}
    </div>
  );
};

const ClauseCard = ({ clause, idx }) => {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  
  const [precedents, setPrecedents] = useState(null);
  const [loadingPrecedents, setLoadingPrecedents] = useState(false);
  const [precedentsExpanded, setPrecedentsExpanded] = useState(false);
  
  const isHighRisk = clause.risk_level === 'HIGH';

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

  const handleSearchPrecedents = async () => {
    if (precedents) {
      setPrecedentsExpanded(!precedentsExpanded);
      return;
    }

    setLoadingPrecedents(true);
    setPrecedentsExpanded(true);

    try {
      const response = await axios.post('http://localhost:8000/api/find-precedents', {
        clause_text: clause.clause_text
      });
      setPrecedents(response.data.precedents || []);
    } catch (err) {
      setPrecedents([]);
      console.error(err);
    } finally {
      setLoadingPrecedents(false);
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

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        {/* Explain button */}
        <button
          onClick={handleExplain}
          disabled={loading}
          data-html2canvas-ignore="true"
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
              Generating...
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

        {/* Find Precedents Button */}
        {isHighRisk && (
          <button
            onClick={handleSearchPrecedents}
            disabled={loadingPrecedents}
            data-html2canvas-ignore="true"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              fontSize: '0.85rem',
              cursor: loadingPrecedents ? 'not-allowed' : 'pointer',
              background: 'transparent',
              border: '1px solid var(--risk-high)',
              borderRadius: '6px',
              color: 'var(--risk-high)',
              transition: 'all 0.2s'
            }}
          >
            {loadingPrecedents ? (
              <>
                <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                Searching DB...
              </>
            ) : precedents ? (
              <>
                <ChevronDown size={14} style={{ transform: precedentsExpanded ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }} />
                {precedentsExpanded ? 'Hide Past Clauses' : 'Show Past Clauses'}
              </>
            ) : (
              '🔍 Find Similar Past Clauses'
            )}
          </button>
        )}
      </div>

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

      {/* Database Precedents — only shown after button click */}
      {precedentsExpanded && precedents && (
        <div style={{
          marginTop: '0.75rem',
          padding: '1rem',
          background: 'rgba(255, 90, 90, 0.08)',
          border: '1px solid rgba(255, 90, 90, 0.2)',
          borderRadius: '8px',
          color: 'var(--text-primary)'
        }}>
          <h4 style={{ marginBottom: '0.75rem', color: 'var(--risk-high)', fontSize: '0.9rem' }}>Database Matches (Past Similar Clauses)</h4>
          {precedents.length === 0 ? (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>No similar past clauses found in the local database.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {precedents.map((p, i) => (
                <PrecedentMatch key={p.id || i} p={p} i={i} />
              ))}
            </div>
          )}
        </div>
      )}

    </div>
  );
};


const Dashboard = ({ data }) => {
  const { results, task } = data;
  const { toPDF, targetRef } = usePDF({filename: `${data.filename || 'Legal'}_Analysis_Report.pdf`});

  const isContractAnalysis = task === 'analyze_contract';
  const isSummary = task === 'summarize_case';

  const analysisPayload = results.contract_analysis || {};
  const clauses = analysisPayload.analyzed_clauses || [];

  const highRiskCount = clauses.filter(c => c.risk_level === 'HIGH').length;
  const mediumRiskCount = clauses.filter(c => c.risk_level === 'MEDIUM').length;
  const safeCount = clauses.filter(c => c.risk_level === 'LOW').length;

  return (
    <div className="dashboard" ref={targetRef} style={{ backgroundColor: '#0d1117', padding: '2rem', borderRadius: '8px' }}>

      {/* Header */}
      <div className="glass-panel" style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <FileText size={32} color="var(--accent-color)" />
            <h2>Analysis Report: {data.filename}</h2>
          </div>
          <p style={{ color: 'var(--text-secondary)' }}>
            Processed {(results.metadata?.doc_length_chars / 1024).toFixed(2)} KB of text.
          </p>
        </div>
        <button 
          className="btn-primary" 
          onClick={() => toPDF()}
          data-html2canvas-ignore="true"
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <Download size={18} />
          Download PDF
        </button>
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
                <ClauseCard key={idx} clause={clause} idx={idx} />
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