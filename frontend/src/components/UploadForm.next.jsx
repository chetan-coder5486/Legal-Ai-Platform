import { useRef, useState } from 'react';
import axios from 'axios';
import {
  CheckCircle,
  FileSearch,
  FileText,
  Layers3,
  ScrollText,
  ShieldCheck,
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
      'text/plain'
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

  // ✅ UPDATED FUNCTION (IMPORTANT FIX HERE)
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
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      const data = response.data;

      // 🔥 Normalize response for frontend
      if (taskType === "summarize_case") {
        onUploadComplete({
          type: "summary",
          content: data.results?.summary_data?.final_summary || "No summary generated"
        });
      } else {
        onUploadComplete({
          type: "contract",
          content: data.results
        });
      }

    } catch (err) {
      console.error('Upload error:', err);
      onError(
        err.response?.data?.detail ||
        'Failed to process document. Is the backend running?'
      );
    }
  };

  return (
    <div className="upload-shell animate-slide-up">
      <section className="glass-panel upload-hero-panel">
        <div className="upload-hero-copy">
          <div className="hero-kicker">Legal workflow cockpit</div>
          <h2>Start With The Right Intake Path</h2>
          <p>
            Upload a legal document, choose the analysis mode, and get either a negotiation-grade clause report
            or a fast executive summary.
          </p>

          <div className="upload-guidance-grid">
            <div className="guidance-card">
              <Layers3 size={18} />
              <div>
                <strong>Structured outputs</strong>
                <span>Clause scores, evidence, and recommendations when you run contract review.</span>
              </div>
            </div>

            <div className="guidance-card">
              <FileSearch size={18} />
              <div>
                <strong>Designed for review</strong>
                <span>Built to help you spot risk concentration and prioritize redlines faster.</span>
              </div>
            </div>
          </div>
        </div>

        <div className="upload-side-panel">
          <div className="upload-side-badge">Recommended for first pass</div>
          <div className="upload-side-title">
            <SelectedIcon size={20} />
            <span>{selectedPipeline.title}</span>
          </div>
          <p>{selectedPipeline.subtitle}</p>
          <ul className="upload-side-list">
            {selectedPipeline.features.map((feature) => (
              <li key={feature}>{feature}</li>
            ))}
          </ul>
        </div>
      </section>

      <form onSubmit={handleSubmit} className="upload-layout">
        <section className="glass-panel pipeline-panel">
          <div className="panel-head">
            <Layers3 size={20} />
            <h3>Select Intelligence Pipeline</h3>
          </div>

          <div className="pipeline-option-grid">
            {Object.entries(PIPELINES).map(([value, pipeline]) => {
              const Icon = pipeline.icon;
              const active = value === taskType;

              return (
                <button
                  key={value}
                  type="button"
                  className={`pipeline-option ${active ? 'active' : ''}`}
                  onClick={() => setTaskType(value)}
                >
                  <div className="pipeline-option-top">
                    <Icon size={20} />
                    <span>{pipeline.title}</span>
                  </div>
                  <p>{pipeline.subtitle}</p>
                </button>
              );
            })}
          </div>
        </section>

        <section className="glass-panel upload-panel">
          <div className="panel-head">
            <UploadCloud size={20} />
            <h3>Upload Document</h3>
          </div>

          <div
            className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={onButtonClick}
          >
            <input
              ref={inputRef}
              type="file"
              onChange={handleChange}
              accept=".pdf,.docx,.txt"
              style={{ display: 'none' }}
            />

            {!file ? (
              <>
                <UploadCloud className="upload-icon" />
                <h3>Drop your legal document here</h3>
                <p style={{ color: 'var(--text-secondary)' }}>
                  or click to browse from your computer
                </p>
                <div className="upload-support-row">
                  <span>PDF</span>
                  <span>DOCX</span>
                  <span>TXT</span>
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

          <div className="upload-footer">
            <div className="upload-meta">
              <strong>What happens next</strong>
              <span>
                {taskType === 'summarize_case'
                  ? 'The system will generate an AI-powered summary with fallback support if needed.'
                  : 'The system will segment clauses, classify them, run the risk engine, and build a report.'}
              </span>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={!file}
              style={{ width: '100%', padding: '1.2rem', fontSize: '1.05rem' }}
            >
              {selectedPipeline.cta}
            </button>
          </div>
        </section>
      </form>
    </div>
  );
};

export default UploadForm;