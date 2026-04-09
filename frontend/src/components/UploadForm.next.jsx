import { useRef, useState } from 'react';
import axios from 'axios';
import {
  BrainCircuit,
  CheckCircle,
  FileBadge2,
  FileText,
  Gavel,
  Scale,
  ShieldCheck,
  ScrollText,
  Sparkles,
  UploadCloud,
} from 'lucide-react';

const PIPELINES = {
  analyze_contract: {
    icon: ShieldCheck,
    title: 'Contract Risk Review',
    subtitle: 'Best for NDAs, commercial agreements, and clause-level negotiation prep.',
    features: [
      'Classifies clauses and scores legal exposure',
      'Shows triggered rules and protective signals',
      'Produces negotiation-ready recommendations',
    ],
    cta: 'Analyze Contract',
  },
  summarize_case: {
    icon: ScrollText,
    title: 'Long Document Summary',
    subtitle: 'Best for judgments, pleadings, and lengthy legal records.',
    features: [
      'Condenses long documents into clear summaries',
      'Highlights the core narrative and issues',
      'Useful when you need fast orientation first',
    ],
    cta: 'Summarize Document',
  },
};

const UploadForm = ({ onUploadStart, onUploadComplete, onError }) => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [taskType, setTaskType] = useState('analyze_contract');
  const inputRef = useRef(null);

  const selectedPipeline = PIPELINES[taskType];
  const SelectedIcon = selectedPipeline.icon;

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = (selectedFile) => {
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ];
    const validExtension =
      selectedFile.name.endsWith('.pdf') ||
      selectedFile.name.endsWith('.docx') ||
      selectedFile.name.endsWith('.txt');

    if (!validTypes.includes(selectedFile.type) && !validExtension) {
      onError('Please upload a PDF, DOCX, or TXT file.');
      return;
    }
    setFile(selectedFile);
  };

  const onButtonClick = () => {
    inputRef.current?.click();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    onUploadStart();

    const formData = new FormData();
    formData.append('file', file);
    formData.append('task_type', taskType);

    try {
      const response = await axios.post(
        'http://localhost:8000/api/upload',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      const resultPayload = response.data?.results;

      if (taskType === 'analyze_contract' && !Array.isArray(resultPayload?.contract_analysis?.analyzed_clauses)) {
        throw new Error(
          resultPayload?.error ||
          resultPayload?.message ||
          'The backend did not return contract analysis data.'
        );
      }

      if (taskType === 'summarize_case' && !resultPayload?.summary_data?.final_summary) {
        throw new Error(
          resultPayload?.error ||
          resultPayload?.message ||
          'The backend did not return a summary.'
        );
      }

      onUploadComplete({
        type: taskType === 'summarize_case' ? 'summary' : 'contract',
        filename: file.name,
        content: resultPayload,
      });
    } catch (err) {
      console.error('Upload error:', err);
      onError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to process document. Is the backend running?'
      );
    }
  };

  return (
    <div className="upload-shell animate-slide-up">
      <form onSubmit={handleSubmit} className="glass-panel upload-command-center">
        <section className="legal-ai-hero">
          <div className="hero-kicker">Legal AI Chamber</div>
          <h2>Brownstone intelligence for contracts, clauses, and case files.</h2>
          <p>
            A single-screen legal workspace built for fast review. Upload once, choose the analysis path, and get an
            AI-assisted legal reading without leaving the page.
          </p>

          <div className="hero-symbol-row">
            <div className="hero-symbol-card"><Scale size={18} /><span>Legal reasoning</span></div>
            <div className="hero-symbol-card"><BrainCircuit size={18} /><span>AI assistance</span></div>
            <div className="hero-symbol-card"><ShieldCheck size={18} /><span>Risk review</span></div>
          </div>

          <div className="hero-insight-grid">
            <article className="hero-insight-card">
              <div className="hero-insight-icon"><Gavel size={18} /></div>
              <div>
                <strong>Contract risk review</strong>
                <span>Clause classification, legal exposure scoring, and negotiation-ready recommendations.</span>
              </div>
            </article>
            <article className="hero-insight-card">
              <div className="hero-insight-icon"><ScrollText size={18} /></div>
              <div>
                <strong>Long document summary</strong>
                <span>Fast orientation for judgments, pleadings, and lengthy legal records.</span>
              </div>
            </article>
            <article className="hero-insight-card">
              <div className="hero-insight-icon"><FileBadge2 size={18} /></div>
              <div>
                <strong>Accepted formats</strong>
                <span>PDF, DOCX, and TXT supported in the same intake flow.</span>
              </div>
            </article>
          </div>
        </section>

        <section className="upload-intake-panel">
          <div className="intake-panel-top">
            <div className="upload-side-badge">Intake Console</div>
            <div className="upload-side-title">
              <SelectedIcon size={20} />
              <span>{selectedPipeline.title}</span>
            </div>
            <p>{selectedPipeline.subtitle}</p>
          </div>

          <div className="intake-section-head">
            <Sparkles size={18} />
            <h3>Choose Analysis Mode</h3>
          </div>

          <div className="pipeline-stack">
            {Object.entries(PIPELINES).map(([value, pipeline]) => {
              const Icon = pipeline.icon;
              const active = value === taskType;
              return (
                <button key={value} type="button"
                  className={`pipeline-option ${active ? 'active' : ''}`}
                  onClick={() => setTaskType(value)}>
                  <div className="pipeline-option-top">
                    <Icon size={20} />
                    <div>
                      <span>{pipeline.title}</span>
                      <small>{pipeline.cta}</small>
                    </div>
                  </div>
                  <p>{pipeline.subtitle}</p>
                </button>
              );
            })}
          </div>

          <div className="intake-section-head">
            <UploadCloud size={18} />
            <h3>Upload Document</h3>
          </div>

          <div
            className={`upload-zone upload-zone-primary ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={onButtonClick}
          >
            <input ref={inputRef} type="file" onChange={handleChange}
              accept=".pdf,.docx,.txt" style={{ display: 'none' }} />

            {!file ? (
              <>
                <UploadCloud className="upload-icon" />
                <h3>Drop your legal document here</h3>
                <p style={{ color: 'var(--text-secondary)' }}>or click to browse from your computer</p>
                <div className="upload-support-row">
                  <span>PDF</span><span>DOCX</span><span>TXT</span>
                </div>
              </>
            ) : (
              <div className="file-ready-state">
                <FileText size={44} color="var(--accent-color)" />
                <h3>{file.name}</h3>
                <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                <div className="ready-chip">
                  <CheckCircle size={18} />
                  <span>Ready for {selectedPipeline.title.toLowerCase()}</span>
                </div>
              </div>
            )}
          </div>

          <div className="upload-footer compact intake-footer">
            <div className="upload-meta upload-meta-compact">
              <strong>What happens next</strong>
              <span>
                {taskType === 'summarize_case'
                  ? 'The system will generate an AI-powered summary with fallback support if needed.'
                  : 'The system will segment clauses, classify them, run the risk engine, and build a report.'}
              </span>
            </div>

            <button type="submit" className="btn-primary btn-legal" disabled={!file}
              style={{ width: '100%', padding: '1rem 1.15rem', fontSize: '1rem' }}>
              {selectedPipeline.cta}
            </button>

            <div className="intake-trust-row">
              {selectedPipeline.features.map((feature) => (
                <div key={feature} className="trust-chip">
                  <CheckCircle size={14} />
                  <span>{feature}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      </form>
    </div>
  );
};

export default UploadForm;
