import { useState } from 'react';
import axios from 'axios';
import {
  AlertTriangle,
  BadgeCheck,
  CheckCircle2,
  ChevronDown,
  FileSearch,
  FileText,
  Loader2,
  ShieldCheck,
  Sparkles,
  Target,
  Download,
} from 'lucide-react';
import generatePDF from 'react-to-pdf';
const RiskBadge = ({ level }) => (
  <span className={`risk-badge ${level.toLowerCase()}`}>{level} RISK</span>
);

const ClauseCard = ({ clause, idx }) => {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [explanationOpen, setExplanationOpen] = useState(false);

  const matchedRules = clause.matched_rules || [];
  const positiveSignals = clause.positive_signals || [];
  const recommendations = clause.recommendations || [];
  const topRule = matchedRules[0]?.label || 'No major trigger';
  const topPositive = positiveSignals[0]?.label || 'No clear protection';
  const topRecommendation = recommendations[0] || 'No immediate redraft priority';
  const hasExtraDetails =
    matchedRules.length > 1 ||
    positiveSignals.length > 0 ||
    recommendations.length > 1 ||
    (matchedRules[0] && matchedRules[0].evidence);

  const handleExplain = async () => {
    if (explanation) {
      setExplanationOpen(!explanationOpen);
      return;
    }

    setLoading(true);
    setExplanationOpen(true);

    try {
      const response = await axios.post('http://localhost:8000/api/explain-clause', {
        clause_text: clause.clause_text,
        clause_type: clause.type,
        risk_level: clause.risk_level,
        risk_reason: clause.risk_reason,
      });
      setExplanation(response.data.explanation);
    } catch {
      setExplanation('Failed to generate explanation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <article className={`clause-item risk-${clause.risk_level.toLowerCase()}`}>
      <div className="clause-header compact">
        <div>
          <div className="clause-eyebrow">Clause {idx + 1}</div>
          <span className="clause-type">{clause.type}</span>
        </div>

        <div className="clause-header-meta">
          <span className="confidence-pill">
            Confidence {(clause.confidence * 100).toFixed(0)}%
          </span>
          <RiskBadge level={clause.risk_level} />
        </div>
      </div>

      <div className="clause-summary-row compact">
        <p className="clause-summary">{clause.risk_summary || clause.risk_reason}</p>
      </div>

      <div className="clause-preview">
        <span className="preview-label">Preview</span>
        <p>{clause.clause_text}</p>
      </div>

      <div className="clause-mini-grid">
        <div className="mini-stat">
          <span className="mini-label">Trigger</span>
          <strong>{topRule}</strong>
        </div>
        <div className="mini-stat">
          <span className="mini-label">Protection</span>
          <strong>{topPositive}</strong>
        </div>
        <div className="mini-stat">
          <span className="mini-label">Next step</span>
          <strong>{topRecommendation}</strong>
        </div>
      </div>

      <div className="clause-actions">
        {hasExtraDetails && (
          <button
            type="button"
            onClick={() => setDetailsOpen(!detailsOpen)}
            className="explain-btn secondary"
            data-html2canvas-ignore="true"
          >
            <ChevronDown size={14} style={{ transform: detailsOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }} />
            {detailsOpen ? 'Hide details' : 'View details'}
          </button>
        )}

        <button type="button" onClick={handleExplain} disabled={loading} className="explain-btn" data-html2canvas-ignore="true">
          {loading ? (
            <>
              <Loader2 size={14} className="spin-icon" />
              Generating explanation...
            </>
          ) : (
            <>
              <Sparkles size={14} />
              {explanation ? (explanationOpen ? 'Hide explanation' : 'Show explanation') : 'Explain clause'}
            </>
          )}
        </button>
      </div>

      {detailsOpen && (
        <div className="details-stack">
          <div className="detail-grid">
            <section className="detail-panel">
              <div className="detail-title">
                <AlertTriangle size={16} />
                Why this was flagged
              </div>
              {matchedRules.length > 0 ? (
                <div className="chip-list">
                  {matchedRules.slice(0, 3).map((rule) => (
                    <div key={rule.rule_id} className="detail-chip risk-chip compact">
                      <strong>{rule.label}</strong>
                      {rule.evidence && <em>Evidence: {rule.evidence}</em>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="detail-empty">No major risk triggers fired for this clause.</p>
              )}
            </section>

            <section className="detail-panel">
              <div className="detail-title">
                <BadgeCheck size={16} />
                Helpful protections
              </div>
              {positiveSignals.length > 0 ? (
                <div className="chip-list">
                  {positiveSignals.slice(0, 3).map((signal, signalIdx) => (
                    <div key={`${signal.label}-${signalIdx}`} className="detail-chip positive-chip compact">
                      <strong>{signal.label}</strong>
                      {signal.evidence && <em>Evidence: {signal.evidence}</em>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="detail-empty">No protective drafting signals detected here.</p>
              )}
            </section>
          </div>

          <section className="recommendation-panel">
            <div className="detail-title">
              <Target size={16} />
              Additional recommendations
            </div>
            {recommendations.length > 1 ? (
              <ul className="recommendation-list compact">
                {recommendations.slice(1).map((recommendation, recommendationIdx) => (
                  <li key={`${recommendation}-${recommendationIdx}`}>{recommendation}</li>
                ))}
              </ul>
            ) : (
              <p className="detail-empty">No further recommendations beyond the main action shown above.</p>
            )}
          </section>
        </div>
      )}

      {explanationOpen && explanation && <div className="explanation-box">{explanation}</div>}
    </article>
  );
};

const Dashboard = ({ data }) => {
  const [riskFilter, setRiskFilter] = useState('ALL');
  
  const handleDownloadPDF = () => {
    const element = document.getElementById('dashboard-pdf-root');
    if (!element) return;
    
    generatePDF(() => element, {
      filename: `${data.filename || 'Analysis'}_Report.pdf`,
      page: { margin: 10 }
    });
  };

  let results = data.results;
  let task = data.task;

  if (data.type === "contract") {
  results = data.content;
  task = "analyze_contract";
  }

  const isContractAnalysis = task === 'analyze_contract';
  const isSummary = task === 'summarize_case';
  const analysisPayload = results.contract_analysis || {};
  const clauses = analysisPayload.analyzed_clauses || [];
  const summary = analysisPayload.risk_summary || {};
  const topRecommendations = summary.top_recommendations || [];

  const highRiskCount = clauses.filter((c) => c.risk_level === 'HIGH').length;
  const mediumRiskCount = clauses.filter((c) => c.risk_level === 'MEDIUM').length;
  const safeCount = clauses.filter((c) => c.risk_level === 'LOW').length;
  const filteredClauses = riskFilter === 'ALL' ? clauses : clauses.filter((clause) => clause.risk_level === riskFilter);
  const averageConfidence = clauses.length
    ? `${Math.round((clauses.reduce((sum, clause) => sum + (clause.confidence || 0), 0) / clauses.length) * 100)}%`
    : '0%';
  const highestClause = clauses.reduce((current, clause) => {
    if (!current) return clause;
    return (clause.risk_score || 0) > (current.risk_score || 0) ? clause : current;
  }, null);

  return (
    <div className="dashboard" id="dashboard-pdf-root" style={{ backgroundColor: '#0d1117', padding: '1rem', borderRadius: '8px' }}>
      <div className="report-hero glass-panel compact-hero" style={{ position: 'relative' }}>
        <button 
          onClick={handleDownloadPDF} 
          data-html2canvas-ignore="true"
          style={{ position: 'absolute', top: '1.5rem', right: '1.5rem', zIndex: 50, display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--accent-color)', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}
        >
          <Download size={16} /> Download PDF
        </button>
        <div className="report-hero-copy" style={{ paddingRight: '120px' }}>
          <div className="hero-kicker">Contract intelligence report</div>
          <h2>Analysis Report: {data.filename || "Uploaded Document"}</h2>
          <p>Compact review with confidence, negotiation priorities, and optional clause-level detail.</p>
        </div>
        <div className="hero-meta compact">
          <div className="hero-meta-card">
            <span>Document Size</span>
            <strong>{((results.metadata?.doc_length_chars || 0) / 1024).toFixed(2)} KB</strong>
          </div>
          <div className="hero-meta-card">
            <span>Average Classification Confidence</span>
            <strong>{averageConfidence}</strong>
            <small>How sure the system is about clause labels.</small>
          </div>
          <div className="hero-meta-card">
            <span>Most Exposed Area</span>
            <strong>{highestClause?.type || 'No clause detected'}</strong>
          </div>
        </div>
      </div>

      {isContractAnalysis && (
        <>
          <div className="executive-strip compact">
            <div className="glass-panel executive-card executive-card-high">
              <h3>High Risk</h3>
              <div className="executive-value-row">
                <span className="value">{highRiskCount}</span>
                <AlertTriangle color="var(--risk-high)" size={24} />
              </div>
            </div>
            <div className="glass-panel executive-card executive-card-medium">
              <h3>Medium Risk</h3>
              <div className="executive-value-row">
                <span className="value">{mediumRiskCount}</span>
                <FileSearch color="var(--risk-medium)" size={24} />
              </div>
            </div>
            <div className="glass-panel executive-card executive-card-low">
              <h3>Standard</h3>
              <div className="executive-value-row">
                <span className="value">{safeCount}</span>
                <ShieldCheck color="var(--risk-low)" size={24} />
              </div>
            </div>
            <div className="glass-panel executive-card executive-card-neutral">
              <h3>Total Clauses</h3>
              <div className="executive-value-row">
                <span className="value">{analysisPayload.total_clauses_analyzed ?? clauses.length}</span>
                <FileText color="var(--accent-color)" size={24} />
              </div>
            </div>
          </div>

          <div className="insight-grid compact">
            <section className="glass-panel priority-panel">
              <div className="panel-head">
                <Target size={18} />
                <h3>Top Priorities</h3>
              </div>
              {topRecommendations.length > 0 ? (
                <ul className="priority-list compact">
                  {topRecommendations.slice(0, 5).map((item, idx) => (
                    <li key={`${item}-${idx}`}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="detail-empty">No urgent negotiation themes surfaced at the document level.</p>
              )}
            </section>

            <section className="glass-panel spotlight-panel">
              <div className="panel-head">
                <Sparkles size={18} />
                <h3>Clause Spotlight</h3>
              </div>
              {highestClause ? (
                <div className="spotlight-body compact">
                  <div className="spotlight-topline">
                    <span>{highestClause.type}</span>
                    <RiskBadge level={highestClause.risk_level} />
                  </div>
                  <p>{highestClause.risk_summary || highestClause.risk_reason}</p>
                </div>
              ) : (
                <p className="detail-empty">Upload a contract to generate a clause spotlight.</p>
              )}
            </section>
          </div>

          <div className="glass-panel compact-panel">
            <div className="section-head">
              <div>
                <h2>Clause Breakdown</h2>
                <p>Confidence is shown up front. Open details only when you want extra evidence.</p>
              </div>
            </div>

            <div className="filter-row">
              {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((level) => (
                <button
                  key={level}
                  type="button"
                  className={`filter-chip ${riskFilter === level ? 'active' : ''}`}
                  onClick={() => setRiskFilter(level)}
                  data-html2canvas-ignore="true"
                >
                  {level === 'ALL' ? 'All clauses' : `${level} risk`}
                </button>
              ))}
            </div>

            <div className="clause-list compact">
              {filteredClauses.map((clause, idx) => (
                <ClauseCard key={idx} clause={clause} idx={idx} />
              ))}
              {filteredClauses.length === 0 && <p>No clauses match the selected filter.</p>}
            </div>
          </div>
        </>
      )}

      {isSummary && (
        <div className="glass-panel compact-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
            <CheckCircle2 color="var(--risk-low)" size={32} />
            <h2>AI Summary Generated</h2>
          </div>
          <div className="summary-box">{results.summary_data?.final_summary || 'Summarization failed or returned empty.'}</div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
