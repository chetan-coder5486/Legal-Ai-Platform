import { useState, useRef } from 'react';
import axios from 'axios';
import { UploadCloud, FileText, CheckCircle } from 'lucide-react';

const UploadForm = ({ onUploadStart, onUploadComplete, onError }) => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [taskType, setTaskType] = useState('analyze_contract');
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
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
    // Basic validation
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.endsWith('.pdf') && !selectedFile.name.endsWith('.docx') && !selectedFile.name.endsWith('.txt')) {
      alert("Please upload a PDF, DOCX, or TXT file.");
      return;
    }
    setFile(selectedFile);
  };

  const onButtonClick = () => {
    inputRef.current.click();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    onUploadStart();
    const formData = new FormData();
    formData.append('file', file);
    formData.append('task_type', taskType);

    try {
      // Connect to local FastAPI backend
      const response = await axios.post('http://localhost:8000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      onUploadComplete(response.data);
    } catch (err) {
      console.error("Upload error:", err);
      onError(err.response?.data?.detail || "Failed to process document. Is the backend running?");
    }
  };

  return (
    <div className="glass-panel" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>Upload Document</h2>
      
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '2rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Select Intelligence Pipeline</label>
          <select 
            value={taskType} 
            onChange={(e) => setTaskType(e.target.value)}
            style={{ padding: '1rem', fontSize: '1.1rem' }}
          >
            <option value="analyze_contract">Standard Contract Analysis (Risk Engine + RAG)</option>
            <option value="summarize_case">Long Document Summarization</option>
          </select>
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
              <h3>Drag & Drop your legal document here</h3>
              <p style={{ color: 'var(--text-secondary)' }}>or click to browse from your computer</p>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '1rem' }}>
                Supports PDF, DOCX, TXT
              </p>
            </>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <FileText size={48} color="var(--accent-color)" />
              <h3>{file.name}</h3>
              <p style={{ color: 'var(--text-secondary)' }}>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--risk-low)' }}>
                <CheckCircle size={20} />
                <span>Ready to analyze</span>
              </div>
            </div>
          )}
        </div>

        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <button 
            type="submit" 
            className="btn-primary" 
            disabled={!file}
            style={{ width: '100%', padding: '1.2rem', fontSize: '1.1rem' }}
          >
            {taskType === 'summarize_case' ? 'Summarize Document' : 'Analyze Contract'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default UploadForm;
