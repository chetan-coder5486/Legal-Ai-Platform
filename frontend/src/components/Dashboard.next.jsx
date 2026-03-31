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
} from 'lucide-react';

const RiskBadge = ({ level }) => (
  <span className={`risk-badge ${level.toLowerCase()}`}>
    {level} RISK
  </span>
);

const scoreTone = (score = 0) => {
  if (score >= 6) return 'high';
  if (score >= 3) return 'medium';
  return 'low';
};

const ClauseCard = ({ clause, idx }) => {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const matchedRules = clause.matched_rules || [];
  const positiveSignals = clause.positive_signals || [];
  const recommendations = clause.recommendations || [];

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
        risk_reason: clause.risk_reason,
      });
      setExplanation(response.data.explanation);
    } catch (err) {
      setExplanation('Failed to generate explanation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <article className={`clause-item risk-${clause.risk_level.toLowerCase()}`}>
      <div className="clause-header">
        <div>
          <div className="clause-eyebrow">Clause {idx + 1}</div>
          <span className="clause-type">{clause.type}</span>
        </div>

        <div className="clause-header-meta">
          <div className={`score-pill ${scoreTone(clause.risk_score)}`}>
            Score {clause.risk_score ?? 0}
          </div>
          <span className="confidence-pill">
            Confidence {(clause.confidence * 100).toFixed(0)}%
          </span>
          <RiskBadge level={clause.risk_level} />
        </div>
      </div>

      <div className="clause-summary-row">
        <p className="clause-summary">{clause.risk_summary || clause.risk_reason}</p>
        {clause.risk_category && clause.risk_category !== 'unknown' && (
          <span className="category-tag">{clause.risk_category.replaceAll('_', ' ')}</span>
        )}
      </div>

      <div className="clause-quote">"{clause.clause_text}"</div>

      <div className="reason-line">{clause.risk_reason}</div>

      <div className="detail-grid">
        <section className="detail-panel">
          <div className="detail-title">
            <AlertTriangle size={16} />
            Triggered Rules
          </div>
          {matchedRules.length > 0 ? (
            <div className="chip-list">
              {matchedRules.map((rule) => (
                <div key={rule.rule_id} className="detail-chip risk-chip">
                  <strong>{rule.label}</strong>
                  <span>Impact +{rule.impact}</span>
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
            Protective Signals
          </div>
          {positiveSignals.length > 0 ? (
            <div className="chip-list">
              {positiveSignals.map((signal, signalIdx) => (
                <div key={`${signal.label}-${signalIdx}`} className="detail-chip positive-chip">
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
          Negotiation Focus
        </div>
        {recommendations.length > 0 ? (
          <ul className="recommendation-list">
            {recommendations.map((recommendation, recommendationIdx) => (
              <li key={`${recommendation}-${recommendationIdx}`}>{recommendation}</li>
            ))}
          </ul>
        ) : (
          <p className="detail-empty">No immediate redraft priority for this clause.</p>
        )}
      </section>

      <button onClick={handleExplain} disabled={loading} className="explain-btn">
        {loading ? (
          <>
            <Loader2 size={14} className="spin-icon" />
            Generating explanation...
          </>
        ) : explanation ? (
          <>
            <ChevronDown size={14} style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }} />
            {expanded ? 'Hide explanation' : 'Show explanation'}
          </>
        ) : (
          <>
            <Sparkles size={14} />
            Explain this clause
          </>
        )}
      </button>

      {expanded && explanation && <div className="explanation-box">{explanation}</div>}
    </article>
  );
};

const Dashboard = ({ data }) => {
  const { results, task } = data;

  const isContractAnalysis = task === 'analyze_contract';
  const isSummary = task === 'summarize_case';

  const analysisPayload = results.contract_analysis || {};
  const clauses = analysisPayload.analyzed_clauses || [];
  const summary = analysisPayload.risk_summary || {};
  const topRecommendations = summary.top_recommendations || [];

  const highRiskCount = clauses.filter((c) => c.risk_level === 'HIGH').length;
  const mediumRiskCount = clauses.filter((c) => c.risk_level === 'MEDIUM').length;
  const safeCount = clauses.filter((c) => c.risk_level === 'LOW').length;
  const averageScore = clauses.length
    ? (clauses.reduce((sum, clause) => sum + (clause.risk_score || 0), 0) / clauses.length).toFixed(1)
    : '0.0';
  const highestClause = clauses.reduce((current, clause) => {
    if (!current) return clause;
    return (clause.risk_score || 0) > (current.risk_score || 0) ? clause : current;
  }, null);

  return (
    <div className="dashboard">
      <div className="report-hero glass-panel">
        <div className="report-hero-copy">
          <div className="hero-kicker">Contract intelligence report</div>
          <h2>Analysis Report: {data.filename}</h2>
          <p>
            Clause-by-clause review with risk scoring, drafting evidence, and negotiation guidance.
          </p>
        </div>
        <div className="hero-meta">
          <div className="hero-meta-card">
            <span>Document Size</span>
            <strong>{((results.metadata?.doc_length_chars || 0) / 1024).toFixed(2)} KB</strong>
          </div>
          <div className="hero-meta-card">
            <span>Average Clause Score</span>
            <strong>{averageScore}</strong>
          </div>
          <div className="hero-meta-card">
            <span>Most Exposed Area</span>
            <strong>{highestClause?.type || 'No clause detected'}</strong>
          </div>
        </div>
      </div>

      {isContractAnalysis && (
        <>
          <div className="executive-strip">
            <div className="glass-panel executive-card executive-card-high">
              <h3>High Risk Clauses</h3>
              <div className="executive-value-row">
                <span className="value">{highRiskCount}</span>
                <AlertTriangle color="var(--risk-high)" size={30} />
              </div>
              <p>Requires review before signature.</p>
            </div>

            <div className="glass-panel executive-card executive-card-medium">
              <h3>Medium Risk Clauses</h3>
              <div className="executive-value-row">
                <span className="value">{mediumRiskCount}</span>
                <FileSearch color="var(--risk-medium)" size={30} />
              </div>
              <p>Worth tightening if leverage allows.</p>
            </div>

            <div className="glass-panel executive-card executive-card-low">
              <h3>Standard Clauses</h3>
              <div className="executive-value-row">
                <span className="value">{safeCount}</span>
                <ShieldCheck color="var(--risk-low)" size={30} />
              </div>
              <p>No major issues detected by the engine.</p>
            </div>

            <div className="glass-panel executive-card executive-card-neutral">
              <h3>Total Clauses</h3>
              <div className="executive-value-row">
                <span className="value">{analysisPayload.total_clauses_analyzed ?? clauses.length}</span>
                <FileText color="var(--accent-color)" size={30} />
              </div>
              <p>All parsed clauses included in this report.</p>
            </div>
          </div>

          <div className="insight-grid">
            <section className="glass-panel priority-panel">
              <div className="panel-head">
                <Target size={20} />
                <h3>Top Negotiation Priorities</h3>
              </div>
              {topRecommendations.length > 0 ? (
                <ul className="priority-list">
                  {topRecommendations.map((item, idx) => (
                    <li key={`${item}-${idx}`}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="detail-empty">No urgent negotiation themes surfaced at the document level.</p>
              )}
            </section>

            <section className="glass-panel spotlight-panel">
              <div className="panel-head">
                <Sparkles size={20} />
                <h3>Clause Spotlight</h3>
              </div>
              {highestClause ? (
                <div className="spotlight-body">
                  <div className="spotlight-topline">
                    <span>{highestClause.type}</span>
                    <RiskBadge level={highestClause.risk_level} />
                  </div>
                  <p>{highestClause.risk_summary || highestClause.risk_reason}</p>
                  <div className="spotlight-score">Score {highestClause.risk_score || 0}</div>
                </div>
              ) : (
                <p className="detail-empty">Upload a contract to generate a clause spotlight.</p>
              )}
            </section>
          </div>

          <div className="glass-panel">
            <div className="section-head">
              <div>
                <h2>Clause Breakdown & Risk Analysis</h2>
                <p>
                  Each card shows the score, why it triggered, what protections are already present, and what to negotiate next.
                </p>
              </div>
            </div>

            <div className="clause-list">
              {clauses.map((clause, idx) => (
                <ClauseCard key={idx} clause={clause} idx={idx} />
              ))}

              {clauses.length === 0 && <p>No clauses could be parsed from the document.</p>}
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
          <div className="summary-box">
            {results.summary_data?.final_summary || 'Summarization failed or returned empty.'}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
