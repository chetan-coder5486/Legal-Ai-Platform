import { useState } from 'react';
import axios from 'axios';
import {
  AlertTriangle,
  BadgeCheck,
  CheckCircle2,
  ChevronDown,
  FileSearch,
  FileText,
  Grid2X2,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Target,
} from 'lucide-react';

const RiskBadge = ({ level }) => (
  <span className={`risk-badge ${level.toLowerCase()}`}>{level} RISK</span>
);

const RISK_LEVEL_ORDER = ['HIGH', 'MEDIUM', 'LOW'];

const formatClauseType = (value) =>
  (value || 'Unclassified clause')
    .replace(/\bclause\b/gi, '')
    .replace(/\s+/g, ' ')
    .trim();

const getHeatClass = (count) => {
  if (count >= 3) return 'hot';
  if (count === 2) return 'warm';
  if (count === 1) return 'mild';
  return 'none';
};

const DONUT_CONFIG = {
  HIGH: {
    color: '#e1533f',
    softColor: 'rgba(225, 83, 63, 0.14)',
    label: 'High Risk',
    description: 'These are the clauses most likely to need changes first.',
  },
  MEDIUM: {
    color: '#f2a93b',
    softColor: 'rgba(242, 169, 59, 0.14)',
    label: 'Medium Risk',
    description: 'These clauses deserve a closer look before signing.',
  },
  LOW: {
    color: '#4ecb71',
    softColor: 'rgba(78, 203, 113, 0.14)',
    label: 'Low Risk',
    description: 'These clauses look more standard or already safer.',
  },
};

const DonutChart = ({ clauses, highRiskCount, mediumRiskCount, safeCount, riskPosture }) => {
  const [activeSegment, setActiveSegment] = useState('HIGH');
  const total = clauses.length || 1;
  const chartData = [
    { key: 'HIGH', value: highRiskCount, score: clauses.filter((c) => c.risk_level === 'HIGH').reduce((sum, c) => sum + (c.risk_score || 0), 0) },
    { key: 'MEDIUM', value: mediumRiskCount, score: clauses.filter((c) => c.risk_level === 'MEDIUM').reduce((sum, c) => sum + (c.risk_score || 0), 0) },
    { key: 'LOW', value: safeCount, score: clauses.filter((c) => c.risk_level === 'LOW').reduce((sum, c) => sum + (c.risk_score || 0), 0) },
  ];

  const activeData =
    chartData.find((item) => item.key === activeSegment && item.value > 0) ||
    chartData.find((item) => item.value > 0) ||
    chartData[0];

  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  let cumulativeOffset = 0;

  return (
    <div className="donut-analytics">
      <div className="donut-shell">
        <svg viewBox="0 0 200 200" className="donut-chart" role="img" aria-label="Contract risk distribution">
          <circle className="donut-track" cx="100" cy="100" r={radius} />
          {chartData.map((item) => {
            const fraction = item.value / total;
            const dash = circumference * fraction;
            const gap = circumference - dash;
            const strokeDasharray = `${dash} ${gap}`;
            const strokeDashoffset = -cumulativeOffset;
            cumulativeOffset += dash;
            const config = DONUT_CONFIG[item.key];
            const isActive = activeData.key === item.key;

            return (
              <circle
                key={item.key}
                cx="100"
                cy="100"
                r={radius}
                fill="transparent"
                stroke={config.color}
                strokeWidth={20}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap={dash > 0 ? 'round' : 'butt'}
                transform="rotate(-90 100 100)"
                className={`donut-segment ${isActive ? 'active' : ''}`}
                onMouseEnter={() => setActiveSegment(item.key)}
              />
            );
          })}
        </svg>

        <div className="donut-center">
          <span>Overall risk</span>
          <strong>{riskPosture}%</strong>
          <small>{clauses.length} clauses analyzed</small>
        </div>
      </div>

      <div className="donut-sidepanel">
        <div
          className="donut-tooltip-card"
          style={{
            background: `linear-gradient(180deg, ${DONUT_CONFIG[activeData.key].softColor}, rgba(255,255,255,0.03))`,
            borderColor: DONUT_CONFIG[activeData.key].softColor,
          }}
        >
          <div className="donut-tooltip-top">
            <span
              className="legend-dot"
              style={{ '--dot-color': DONUT_CONFIG[activeData.key].color }}
            />
            <strong>{DONUT_CONFIG[activeData.key].label}</strong>
          </div>
          <div className="donut-tooltip-metrics">
            <div>
              <span>Clauses</span>
              <strong>{activeData.value}</strong>
            </div>
            <div>
              <span>Part of document</span>
              <strong>{Math.round((activeData.value / total) * 100)}%</strong>
            </div>
            <div>
              <span>Risk points</span>
              <strong>{activeData.score}</strong>
            </div>
          </div>
          <p>{DONUT_CONFIG[activeData.key].description}</p>
        </div>

        <div className="donut-legend">
          {chartData.map((item) => {
            const config = DONUT_CONFIG[item.key];
            const percent = Math.round((item.value / total) * 100);
            const isActive = activeData.key === item.key;

            return (
              <button
                key={item.key}
                type="button"
                className={`donut-legend-item ${isActive ? 'active' : ''}`}
                onMouseEnter={() => setActiveSegment(item.key)}
                onFocus={() => setActiveSegment(item.key)}
              >
                <span className="legend-dot" style={{ '--dot-color': config.color }} />
                <div className="donut-legend-copy">
                  <strong>{config.label}</strong>
                  <span>{item.value} clauses</span>
                </div>
                <span className="donut-legend-value">{percent}%</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

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
          >
            <ChevronDown size={14} style={{ transform: detailsOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }} />
            {detailsOpen ? 'Hide details' : 'View details'}
          </button>
        )}

        <button type="button" onClick={handleExplain} disabled={loading} className="explain-btn">
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
  const riskWeightedExposure = clauses.reduce((sum, clause) => sum + (clause.risk_score || 0), 0);
  const riskPosture = clauses.length ? Math.round((riskWeightedExposure / (clauses.length * 6)) * 100) : 0;
  const analyticsByTypeMap = clauses.reduce((acc, clause) => {
    const typeKey = clause.type || 'Unclassified clause';

    if (!acc[typeKey]) {
      acc[typeKey] = {
        type: typeKey,
        displayType: formatClauseType(typeKey),
        total: 0,
        high: 0,
        medium: 0,
        low: 0,
        totalScore: 0,
        totalConfidence: 0,
      };
    }

    acc[typeKey].total += 1;
    acc[typeKey].totalScore += clause.risk_score || 0;
    acc[typeKey].totalConfidence += clause.confidence || 0;

    if (clause.risk_level === 'HIGH') acc[typeKey].high += 1;
    if (clause.risk_level === 'MEDIUM') acc[typeKey].medium += 1;
    if (clause.risk_level === 'LOW') acc[typeKey].low += 1;

    return acc;
  }, {});

  const analyticsByType = Object.values(analyticsByTypeMap)
    .map((entry) => ({
      ...entry,
      averageScore: entry.total ? Number((entry.totalScore / entry.total).toFixed(1)) : 0,
      averageConfidence: entry.total ? Math.round((entry.totalConfidence / entry.total) * 100) : 0,
      highestLevel:
        entry.high > 0 ? 'HIGH' : entry.medium > 0 ? 'MEDIUM' : 'LOW',
    }))
    .sort((a, b) => {
      if (b.high !== a.high) return b.high - a.high;
      if (b.averageScore !== a.averageScore) return b.averageScore - a.averageScore;
      return b.total - a.total;
    });

  const heatmapRows = analyticsByType.slice(0, 8);

  return (
    <div className="dashboard">
      <div className="report-hero glass-panel compact-hero">
        <div className="report-hero-copy">
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

          <div className="analytics-grid">
            <section className="glass-panel analytics-panel">
              <div className="panel-head">
                <Grid2X2 size={18} />
                <h3>Risk Map</h3>
              </div>
              <p className="analytics-copy">
                This shows which clause types have more high, medium, or low risk items.
              </p>

              {heatmapRows.length > 0 ? (
                <div className="heatmap-table">
                  <div className="heatmap-header heatmap-cell type-cell">Clause type</div>
                  {RISK_LEVEL_ORDER.map((level) => (
                    <div key={level} className="heatmap-header heatmap-cell">
                      {level === 'HIGH' ? 'High' : level === 'MEDIUM' ? 'Medium' : 'Low'}
                    </div>
                  ))}
                  <div className="heatmap-header heatmap-cell total-cell">Count</div>

                  {heatmapRows.flatMap((row) => ([
                    <div key={`${row.type}-label`} className="heatmap-cell type-cell heatmap-type-label">
                      <strong>{row.displayType}</strong>
                      <span>Avg risk {row.averageScore}</span>
                    </div>,
                    ...RISK_LEVEL_ORDER.map((level) => {
                      const count = row[level.toLowerCase()];
                      return (
                        <div
                          key={`${row.type}-${level}`}
                          className={`heatmap-cell heatmap-value ${getHeatClass(count)} risk-${level.toLowerCase()}`}
                        >
                          <strong>{count}</strong>
                        </div>
                      );
                    }),
                    <div key={`${row.type}-total`} className="heatmap-cell total-cell heatmap-total">
                      <strong>{row.total}</strong>
                      <span>{row.averageConfidence}% AI confidence</span>
                    </div>,
                  ]))}
                </div>
              ) : (
                <p className="detail-empty">Upload a contract to populate the heatmap.</p>
              )}
            </section>

            <section className="glass-panel analytics-panel">
              <div className="panel-head">
                <ShieldAlert size={18} />
                <h3>Risk Split</h3>
              </div>
              <p className="analytics-copy">
                Hover over the chart to see how much of the document falls into each risk level.
              </p>

              <DonutChart
                clauses={clauses}
                highRiskCount={highRiskCount}
                mediumRiskCount={mediumRiskCount}
                safeCount={safeCount}
                riskPosture={riskPosture}
              />
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
