import { useState, useRef } from 'react';
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
  Download,
  BookOpen,
  Wand2,
} from 'lucide-react';

/* ─── PDF DOWNLOAD via window.print() ───────────────────────────────────── */
function downloadAsPDF(filename) {
  const styleId = 'legal-ai-print-styles';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.innerHTML = `
      @media print {
        body { background: #fff !important; color: #000 !important; }
        header, .btn-primary, [data-html2canvas-ignore],
        .filter-row, .clause-actions, .precedents-section, .redraft-section { display: none !important; }
        .dashboard { background: #fff !important; padding: 0 !important; }
        .glass-panel { border: 1px solid #ccc !important; background: #fff !important;
                        box-shadow: none !important; break-inside: avoid; margin-bottom: 1rem; padding: 1rem !important; }
        .risk-badge.high   { background: #ffe5e0 !important; color: #c0392b !important; }
        .risk-badge.medium { background: #fff3e0 !important; color: #b7770d !important; }
        .risk-badge.low    { background: #e8f8ee !important; color: #1e7e34 !important; }
        .clause-item { break-inside: avoid; border-left: 3px solid #ccc !important; }
        .clause-item.risk-high   { border-left-color: #c0392b !important; }
        .clause-item.risk-medium { border-left-color: #b7770d !important; }
        .clause-item.risk-low    { border-left-color: #1e7e34 !important; }
        .donut-analytics, .donut-chart, .donut-shell { display: none !important; }
        .explanation-box { background: #f5f5f5 !important; color: #111 !important; }
        @page { margin: 1.5cm; size: A4; }
      }
    `;
    document.head.appendChild(style);
  }
  const prevTitle = document.title;
  document.title = filename ? `${filename}_Report` : 'Legal_AI_Report';
  window.print();
  document.title = prevTitle;
}

/* ─── HELPERS ────────────────────────────────────────────────────────────── */
const RiskBadge = ({ level }) => (
  <span className={`risk-badge ${(level || 'low').toLowerCase()}`}>{level} RISK</span>
);

const RISK_LEVEL_ORDER = ['HIGH', 'MEDIUM', 'LOW'];

const formatClauseType = (value) =>
  (value || 'Unclassified clause').replace(/\bclause\b/gi, '').replace(/\s+/g, ' ').trim();

const getHeatClass = (count) => {
  if (count >= 3) return 'hot';
  if (count === 2) return 'warm';
  if (count === 1) return 'mild';
  return 'none';
};

const DONUT_CONFIG = {
  HIGH:   { color: '#e1533f', softColor: 'rgba(225, 83, 63, 0.14)',  label: 'High Risk',   description: 'These clauses most likely need changes first.' },
  MEDIUM: { color: '#f2a93b', softColor: 'rgba(242, 169, 59, 0.14)', label: 'Medium Risk', description: 'These clauses deserve a closer look before signing.' },
  LOW:    { color: '#4ecb71', softColor: 'rgba(78, 203, 113, 0.14)', label: 'Low Risk',    description: 'These clauses look more standard or already safer.' },
};

/**
 * ROBUST DATA EXTRACTOR
 * Handles every possible shape the backend might return:
 *
 *  Shape A (correct): data.results.contract_analysis.analyzed_clauses
 *  Shape B (old bug): data.content.contract_analysis.analyzed_clauses  
 *  Shape C (direct):  data.contract_analysis.analyzed_clauses
 *  Shape D (flat):    data.analyzed_clauses
 */
function extractAnalysisPayload(data) {
  // Try all known paths in priority order
  const candidates = [
    data?.results?.contract_analysis,
    data?.content?.contract_analysis,
    data?.contract_analysis,
    data?.results,
    data,
  ];

  for (const candidate of candidates) {
    if (candidate && Array.isArray(candidate.analyzed_clauses)) {
      console.log('[Dashboard] Found analyzed_clauses at candidate:', candidate);
      return candidate;
    }
  }

  console.warn('[Dashboard] Could not find analyzed_clauses in data:', data);
  return {};
}

function extractMetadata(data) {
  return (
    data?.results?.metadata ||
    data?.content?.metadata ||
    data?.metadata ||
    {}
  );
}

function extractSummary(data) {
  return (
    data?.results?.summary_data?.final_summary ||
    data?.content?.summary_data?.final_summary ||
    data?.summary_data?.final_summary ||
    ''
  );
}

/* ─── DONUT CHART ────────────────────────────────────────────────────────── */
const DonutChart = ({ clauses, highRiskCount, mediumRiskCount, safeCount, riskPosture }) => {
  const [activeSegment, setActiveSegment] = useState('HIGH');
  const total = clauses.length || 1;
  const chartData = [
    { key: 'HIGH',   value: highRiskCount,   score: clauses.filter(c => c.risk_level === 'HIGH').reduce((s,c) => s+(c.risk_score||0), 0) },
    { key: 'MEDIUM', value: mediumRiskCount,  score: clauses.filter(c => c.risk_level === 'MEDIUM').reduce((s,c) => s+(c.risk_score||0), 0) },
    { key: 'LOW',    value: safeCount,        score: clauses.filter(c => c.risk_level === 'LOW').reduce((s,c) => s+(c.risk_score||0), 0) },
  ];
  const activeData = chartData.find(i => i.key === activeSegment && i.value > 0) || chartData.find(i => i.value > 0) || chartData[0];
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  let cumulativeOffset = 0;

  return (
    <div className="donut-analytics">
      <div className="donut-shell">
        <svg viewBox="0 0 200 200" className="donut-chart">
          <circle className="donut-track" cx="100" cy="100" r={radius} />
          {chartData.map(item => {
            const dash = circumference * (item.value / total);
            const strokeDashoffset = -cumulativeOffset;
            cumulativeOffset += dash;
            const config = DONUT_CONFIG[item.key];
            return (
              <circle key={item.key} cx="100" cy="100" r={radius} fill="transparent"
                stroke={config.color} strokeWidth={20}
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap={dash > 0 ? 'round' : 'butt'}
                transform="rotate(-90 100 100)"
                className={`donut-segment ${activeData.key === item.key ? 'active' : ''}`}
                onMouseEnter={() => setActiveSegment(item.key)} />
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
        <div className="donut-tooltip-card" style={{
          background: `linear-gradient(180deg, ${DONUT_CONFIG[activeData.key].softColor}, rgba(255,255,255,0.03))`,
          borderColor: DONUT_CONFIG[activeData.key].softColor,
        }}>
          <div className="donut-tooltip-top">
            <span className="legend-dot" style={{ '--dot-color': DONUT_CONFIG[activeData.key].color }} />
            <strong>{DONUT_CONFIG[activeData.key].label}</strong>
          </div>
          <div className="donut-tooltip-metrics">
            <div><span>Clauses</span><strong>{activeData.value}</strong></div>
            <div><span>Part of document</span><strong>{Math.round((activeData.value/total)*100)}%</strong></div>
            <div><span>Risk points</span><strong>{activeData.score}</strong></div>
          </div>
          <p>{DONUT_CONFIG[activeData.key].description}</p>
        </div>
        <div className="donut-legend">
          {chartData.map(item => {
            const config = DONUT_CONFIG[item.key];
            return (
              <button key={item.key} type="button"
                className={`donut-legend-item ${activeData.key === item.key ? 'active' : ''}`}
                onMouseEnter={() => setActiveSegment(item.key)}
                onFocus={() => setActiveSegment(item.key)}>
                <span className="legend-dot" style={{ '--dot-color': config.color }} />
                <div className="donut-legend-copy">
                  <strong>{config.label}</strong>
                  <span>{item.value} clauses</span>
                </div>
                <span className="donut-legend-value">{Math.round((item.value/total)*100)}%</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

/* ─── PRECEDENTS PANEL ───────────────────────────────────────────────────── */
const PrecedentsPanel = ({ clauseText }) => {
  const [precedents, setPrecedents] = useState(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const handleSearch = async () => {
    if (open && precedents) { setOpen(false); return; }
    setOpen(true);
    if (precedents) return;
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/api/find-precedents', { clause_text: clauseText });
      setPrecedents(res.data.precedents || []);
    } catch { setPrecedents([]); }
    finally { setLoading(false); }
  };

  return (
    <div className="precedents-section">
      <button type="button" onClick={handleSearch} className="explain-btn secondary" data-html2canvas-ignore="true">
        {loading ? <Loader2 size={14} className="spin-icon" /> : <BookOpen size={14} />}
        {open ? 'Hide precedents' : 'Find similar clauses'}
      </button>
      {open && (
        <div className="precedents-panel">
          <div className="detail-title" style={{ marginBottom: '0.5rem' }}>
            <BookOpen size={16} /> Similar clauses in past documents
          </div>
          {loading && <p className="detail-empty">Searching vector database...</p>}
          {!loading && precedents?.length === 0 && (
            <p className="detail-empty">No similar clauses found yet. Upload more documents to build the knowledge base.</p>
          )}
          {!loading && precedents?.length > 0 && (
            <div className="chip-list">
              {precedents.map((p, i) => (
                <div key={i} className="detail-chip precedent-chip compact">
                  <strong>{p.metadata?.source || 'Past document'}</strong>
                  <em>{(p.text || '').slice(0, 120)}...</em>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/* ─── REDRAFT PANEL ──────────────────────────────────────────────────────── */
const RedraftPanel = ({ clause }) => {
  const [redraft, setRedraft] = useState(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  if (clause.risk_level === 'LOW') return null;

  const handleRedraft = async () => {
    if (open && redraft) { setOpen(false); return; }
    setOpen(true);
    if (redraft) return;
    setLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/api/redraft-clause', {
        clause_text: clause.clause_text,
        clause_type: clause.type,
        risk_level: clause.risk_level,
        risk_reason: clause.risk_reason,
        recommendations: clause.recommendations || [],
      });
      setRedraft(res.data.redraft || 'No redraft generated.');
    } catch { setRedraft('Redraft service unavailable. Ensure the backend is running.'); }
    finally { setLoading(false); }
  };

  return (
    <div className="redraft-section">
      <button type="button" onClick={handleRedraft} className="explain-btn redraft-btn" data-html2canvas-ignore="true">
        {loading ? <Loader2 size={14} className="spin-icon" /> : <Wand2 size={14} />}
        {open ? 'Hide redraft' : 'Suggest safer redraft'}
      </button>
      {open && (
        <div className="redraft-panel">
          <div className="detail-title" style={{ marginBottom: '0.5rem', color: 'var(--accent-color)' }}>
            <Wand2 size={16} /> AI-suggested safer version
          </div>
          {loading && <p className="detail-empty">Generating safer clause language...</p>}
          {!loading && redraft && <div className="redraft-text">{redraft}</div>}
        </div>
      )}
    </div>
  );
};

/* ─── CLAUSE CARD ────────────────────────────────────────────────────────── */
const ClauseCard = ({ clause, idx }) => {
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [explanationOpen, setExplanationOpen] = useState(false);

  const matchedRules    = clause.matched_rules    || [];
  const positiveSignals = clause.positive_signals || [];
  const recommendations = clause.recommendations  || [];
  const topRule             = matchedRules[0]?.label    || 'No major trigger';
  const topPositive         = positiveSignals[0]?.label || 'No clear protection';
  const topRecommendation   = recommendations[0]        || 'No immediate redraft priority';
  const hasExtraDetails = matchedRules.length > 1 || positiveSignals.length > 0 || recommendations.length > 1 || matchedRules[0]?.evidence;

  const handleExplain = async () => {
    if (explanation) { setExplanationOpen(!explanationOpen); return; }
    setLoading(true);
    setExplanationOpen(true);
    try {
      const res = await axios.post('http://localhost:8000/api/explain-clause', {
        clause_text: clause.clause_text,
        clause_type: clause.type,
        risk_level:  clause.risk_level,
        risk_reason: clause.risk_reason,
      });
      setExplanation(res.data.explanation);
    } catch { setExplanation('Failed to generate explanation. Please try again.'); }
    finally { setLoading(false); }
  };

  const riskLevel = clause.risk_level || 'LOW';

  return (
    <article className={`clause-item risk-${riskLevel.toLowerCase()}`}>
      <div className="clause-header compact">
        <div>
          <div className="clause-eyebrow">Clause {idx + 1}</div>
          <span className="clause-type">{clause.type}</span>
        </div>
        <div className="clause-header-meta">
          <span className="confidence-pill">Confidence {((clause.confidence || 0) * 100).toFixed(0)}%</span>
          <RiskBadge level={riskLevel} />
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
        <div className="mini-stat"><span className="mini-label">Trigger</span><strong>{topRule}</strong></div>
        <div className="mini-stat"><span className="mini-label">Protection</span><strong>{topPositive}</strong></div>
        <div className="mini-stat"><span className="mini-label">Next step</span><strong>{topRecommendation}</strong></div>
      </div>

      <div className="clause-actions">
        {hasExtraDetails && (
          <button type="button" onClick={() => setDetailsOpen(!detailsOpen)}
            className="explain-btn secondary" data-html2canvas-ignore="true">
            <ChevronDown size={14} style={{ transform: detailsOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s ease' }} />
            {detailsOpen ? 'Hide details' : 'View details'}
          </button>
        )}
        <button type="button" onClick={handleExplain} disabled={loading} className="explain-btn" data-html2canvas-ignore="true">
          {loading ? <><Loader2 size={14} className="spin-icon" /> Generating...</> : <><Sparkles size={14} />{explanation ? (explanationOpen ? 'Hide explanation' : 'Show explanation') : 'Explain clause'}</>}
        </button>
        <RedraftPanel clause={clause} />
        <PrecedentsPanel clauseText={clause.clause_text} />
      </div>

      {detailsOpen && (
        <div className="details-stack">
          <div className="detail-grid">
            <section className="detail-panel">
              <div className="detail-title"><AlertTriangle size={16} />Why this was flagged</div>
              {matchedRules.length > 0 ? (
                <div className="chip-list">
                  {matchedRules.slice(0,3).map(rule => (
                    <div key={rule.rule_id} className="detail-chip risk-chip compact">
                      <strong>{rule.label}</strong>
                      {rule.evidence && <em>Evidence: {rule.evidence}</em>}
                    </div>
                  ))}
                </div>
              ) : <p className="detail-empty">No major risk triggers fired for this clause.</p>}
            </section>
            <section className="detail-panel">
              <div className="detail-title"><BadgeCheck size={16} />Helpful protections</div>
              {positiveSignals.length > 0 ? (
                <div className="chip-list">
                  {positiveSignals.slice(0,3).map((sig,i) => (
                    <div key={`${sig.label}-${i}`} className="detail-chip positive-chip compact">
                      <strong>{sig.label}</strong>
                      {sig.evidence && <em>Evidence: {sig.evidence}</em>}
                    </div>
                  ))}
                </div>
              ) : <p className="detail-empty">No protective drafting signals detected.</p>}
            </section>
          </div>
          <section className="recommendation-panel">
            <div className="detail-title"><Target size={16} />Additional recommendations</div>
            {recommendations.length > 1 ? (
              <ul className="recommendation-list compact">
                {recommendations.slice(1).map((rec,i) => <li key={`${rec}-${i}`}>{rec}</li>)}
              </ul>
            ) : <p className="detail-empty">No further recommendations beyond the main action shown above.</p>}
          </section>
        </div>
      )}
      {explanationOpen && explanation && <div className="explanation-box">{explanation}</div>}
    </article>
  );
};

/* ─── DASHBOARD ──────────────────────────────────────────────────────────── */
const Dashboard = ({ data }) => {
  const [riskFilter, setRiskFilter] = useState('ALL');

  // Debug log — see in browser console what shape arrives
  console.log('[Dashboard] Received data prop:', data);

  // ROBUST extraction — handles all possible backend response shapes
  const analysisPayload   = extractAnalysisPayload(data);
  const metadata          = extractMetadata(data);
  const task              = data?.task || 'analyze_contract';
  const isContractAnalysis = task === 'analyze_contract';
  const isSummary          = task === 'summarize_case';

  const clauses            = analysisPayload.analyzed_clauses || [];
  const riskSummary        = analysisPayload.risk_summary     || {};
  const topRecommendations = riskSummary.top_recommendations  || [];

  console.log('[Dashboard] Extracted clauses count:', clauses.length);

  const highRiskCount   = clauses.filter(c => c.risk_level === 'HIGH').length;
  const mediumRiskCount = clauses.filter(c => c.risk_level === 'MEDIUM').length;
  const safeCount       = clauses.filter(c => c.risk_level === 'LOW').length;
  const filteredClauses = riskFilter === 'ALL' ? clauses : clauses.filter(c => c.risk_level === riskFilter);

  const averageConfidence = clauses.length
    ? `${Math.round((clauses.reduce((s,c) => s+(c.confidence||0), 0) / clauses.length) * 100)}%`
    : '0%';

  const highestClause = clauses.reduce((cur,c) => (!cur || (c.risk_score||0) > (cur.risk_score||0)) ? c : cur, null);
  const riskWeightedExposure = clauses.reduce((s,c) => s+(c.risk_score||0), 0);
  const riskPosture = clauses.length ? Math.round((riskWeightedExposure / (clauses.length * 6)) * 100) : 0;

  const analyticsByTypeMap = clauses.reduce((acc, clause) => {
    const key = clause.type || 'Unclassified clause';
    if (!acc[key]) acc[key] = { type: key, displayType: formatClauseType(key), total:0, high:0, medium:0, low:0, totalScore:0, totalConfidence:0 };
    acc[key].total++;
    acc[key].totalScore += clause.risk_score || 0;
    acc[key].totalConfidence += clause.confidence || 0;
    if (clause.risk_level === 'HIGH')   acc[key].high++;
    if (clause.risk_level === 'MEDIUM') acc[key].medium++;
    if (clause.risk_level === 'LOW')    acc[key].low++;
    return acc;
  }, {});

  const heatmapRows = Object.values(analyticsByTypeMap)
    .map(e => ({
      ...e,
      averageScore:      e.total ? Number((e.totalScore/e.total).toFixed(1)) : 0,
      averageConfidence: e.total ? Math.round((e.totalConfidence/e.total)*100) : 0,
    }))
    .sort((a,b) => b.high - a.high || b.averageScore - a.averageScore || b.total - a.total)
    .slice(0, 8);

  return (
    <div className="dashboard" id="dashboard-pdf-root"
      style={{ backgroundColor: '#0d1117', padding: '1rem', borderRadius: '8px' }}>

      {/* HERO */}
      <div className="report-hero glass-panel compact-hero" style={{ position: 'relative' }}>
        <button onClick={() => downloadAsPDF(data?.filename)} data-html2canvas-ignore="true"
          style={{ position:'absolute', top:'1.5rem', right:'1.5rem', zIndex:50, display:'flex', alignItems:'center', gap:'0.5rem', background:'var(--accent-color)', color:'white', border:'none', padding:'0.5rem 1rem', borderRadius:'6px', cursor:'pointer', fontWeight:600 }}>
          <Download size={16} /> Download PDF
        </button>
        <div className="report-hero-copy" style={{ paddingRight: '160px' }}>
          <div className="hero-kicker">Contract intelligence report</div>
          <h2>Analysis Report: {data?.filename || 'Uploaded Document'}</h2>
          <p>Compact review with confidence, negotiation priorities, and optional clause-level detail.</p>
        </div>
        <div className="hero-meta compact">
          <div className="hero-meta-card">
            <span>Document Size</span>
            <strong>{((metadata.doc_length_chars || 0) / 1024).toFixed(2)} KB</strong>
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
          {/* EXECUTIVE STRIP */}
          <div className="executive-strip compact">
            <div className="glass-panel executive-card executive-card-high">
              <h3>High Risk</h3>
              <div className="executive-value-row"><span className="value">{highRiskCount}</span><AlertTriangle color="var(--risk-high)" size={24}/></div>
            </div>
            <div className="glass-panel executive-card executive-card-medium">
              <h3>Medium Risk</h3>
              <div className="executive-value-row"><span className="value">{mediumRiskCount}</span><FileSearch color="var(--risk-medium)" size={24}/></div>
            </div>
            <div className="glass-panel executive-card executive-card-low">
              <h3>Standard</h3>
              <div className="executive-value-row"><span className="value">{safeCount}</span><ShieldCheck color="var(--risk-low)" size={24}/></div>
            </div>
            <div className="glass-panel executive-card executive-card-neutral">
              <h3>Total Clauses</h3>
              <div className="executive-value-row"><span className="value">{analysisPayload.total_clauses_analyzed ?? clauses.length}</span><FileText color="var(--accent-color)" size={24}/></div>
            </div>
          </div>

          {/* INSIGHT GRID */}
          <div className="insight-grid compact">
            <section className="glass-panel priority-panel">
              <div className="panel-head"><Target size={18}/><h3>Top Priorities</h3></div>
              {topRecommendations.length > 0
                ? <ul className="priority-list compact">{topRecommendations.slice(0,5).map((item,i) => <li key={i}>{item}</li>)}</ul>
                : <p className="detail-empty">No urgent negotiation themes surfaced at the document level.</p>}
            </section>
            <section className="glass-panel spotlight-panel">
              <div className="panel-head"><Sparkles size={18}/><h3>Clause Spotlight</h3></div>
              {highestClause
                ? <div className="spotlight-body compact">
                    <div className="spotlight-topline"><span>{highestClause.type}</span><RiskBadge level={highestClause.risk_level}/></div>
                    <p>{highestClause.risk_summary || highestClause.risk_reason}</p>
                  </div>
                : <p className="detail-empty">Upload a contract to generate a clause spotlight.</p>}
            </section>
          </div>

          {/* ANALYTICS GRID */}
          <div className="analytics-grid">
            <section className="glass-panel analytics-panel">
              <div className="panel-head"><Grid2X2 size={18}/><h3>Risk Map</h3></div>
              <p className="analytics-copy">This shows which clause types have more high, medium, or low risk items.</p>
              {heatmapRows.length > 0 ? (
                <div className="heatmap-table">
                  <div className="heatmap-header heatmap-cell type-cell">Clause type</div>
                  {RISK_LEVEL_ORDER.map(l => <div key={l} className="heatmap-header heatmap-cell">{l[0]+l.slice(1).toLowerCase()}</div>)}
                  <div className="heatmap-header heatmap-cell total-cell">Count</div>
                  {heatmapRows.flatMap(row => [
                    <div key={`${row.type}-label`} className="heatmap-cell type-cell heatmap-type-label">
                      <strong>{row.displayType}</strong><span>Avg risk {row.averageScore}</span>
                    </div>,
                    ...RISK_LEVEL_ORDER.map(level => {
                      const count = row[level.toLowerCase()];
                      return <div key={`${row.type}-${level}`} className={`heatmap-cell heatmap-value ${getHeatClass(count)} risk-${level.toLowerCase()}`}><strong>{count}</strong></div>;
                    }),
                    <div key={`${row.type}-total`} className="heatmap-cell total-cell heatmap-total">
                      <strong>{row.total}</strong><span>{row.averageConfidence}% AI confidence</span>
                    </div>,
                  ])}
                </div>
              ) : <p className="detail-empty">Upload a contract to populate the heatmap.</p>}
            </section>
            <section className="glass-panel analytics-panel">
              <div className="panel-head"><ShieldAlert size={18}/><h3>Risk Split</h3></div>
              <p className="analytics-copy">Hover over the chart to see how much of the document falls into each risk level.</p>
              <DonutChart clauses={clauses} highRiskCount={highRiskCount} mediumRiskCount={mediumRiskCount} safeCount={safeCount} riskPosture={riskPosture}/>
            </section>
          </div>

          {/* CLAUSE BREAKDOWN */}
          <div className="glass-panel compact-panel">
            <div className="section-head">
              <div><h2>Clause Breakdown</h2><p>Confidence is shown up front. Open details only when you want extra evidence.</p></div>
            </div>
            <div className="filter-row">
              {['ALL','HIGH','MEDIUM','LOW'].map(level => (
                <button key={level} type="button"
                  className={`filter-chip ${riskFilter === level ? 'active' : ''}`}
                  onClick={() => setRiskFilter(level)} data-html2canvas-ignore="true">
                  {level === 'ALL' ? 'All clauses' : `${level} risk`}
                </button>
              ))}
            </div>
            <div className="clause-list compact">
              {filteredClauses.map((clause,idx) => <ClauseCard key={idx} clause={clause} idx={idx}/>)}
              {filteredClauses.length === 0 && <p>No clauses match the selected filter.</p>}
            </div>
          </div>
        </>
      )}

      {isSummary && (
        <div className="glass-panel compact-panel">
          <div style={{ display:'flex', alignItems:'center', gap:'1rem', marginBottom:'1.5rem' }}>
            <CheckCircle2 color="var(--risk-low)" size={32}/>
            <h2>AI Summary Generated</h2>
          </div>
          <div className="summary-box">{extractSummary(data) || 'Summarization failed or returned empty.'}</div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
