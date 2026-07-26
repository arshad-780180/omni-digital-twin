import { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadResume } from '../services/profile';

export default function ResumeUpload({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, uploading, success, error
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      handleFileSelection(droppedFile);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleFileSelection = (selectedFile) => {
    if (selectedFile.type !== 'application/pdf') {
      setStatus('error');
      setErrorMessage('Please upload a PDF file.');
      return;
    }
    setFile(selectedFile);
    setStatus('idle');
    setErrorMessage('');
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await uploadResume(formData);
      setStatus('success');
      if (onUploadSuccess) {
        onUploadSuccess(response.extracted_skills);
      }
    } catch (error) {
      setStatus('error');
      setErrorMessage(error.response?.data?.detail || 'An error occurred during upload.');
    }
  };

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 backdrop-blur-sm">
      <h3 className="text-xl font-bold text-slate-100 mb-4">Resume Upload</h3>
      
      {!file ? (
        <div 
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
            isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800'
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <UploadCloud className="w-12 h-12 text-blue-400 mx-auto mb-4" />
          <p className="text-slate-300 font-medium mb-1">Click or drag and drop to upload</p>
          <p className="text-slate-500 text-sm">PDF (max. 10MB)</p>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept="application/pdf"
            className="hidden" 
          />
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-slate-900/50 border border-slate-700 rounded-xl">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-blue-400" />
              <div>
                <p className="text-sm font-medium text-slate-200">{file.name}</p>
                <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
            </div>
            
            {status === 'idle' && (
              <button 
                onClick={() => setFile(null)}
                className="text-slate-400 hover:text-slate-300 text-sm"
              >
                Remove
              </button>
            )}
            {status === 'success' && <CheckCircle className="w-6 h-6 text-emerald-400" />}
            {status === 'error' && <AlertCircle className="w-6 h-6 text-red-400" />}
          </div>

          {status === 'error' && (
            <div className="text-red-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {errorMessage}
            </div>
          )}

          {status === 'idle' && (
            <button
              onClick={handleUpload}
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-blue-600/20"
            >
              Analyze Resume
            </button>
          )}

          {status === 'uploading' && (
            <button
              disabled
              className="w-full py-3 bg-slate-700 text-slate-300 font-semibold rounded-xl flex items-center justify-center gap-2 cursor-not-allowed"
            >
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing & Extracting Skills...
            </button>
          )}

          {status === 'success' && (
            <button
              onClick={() => {
                setFile(null);
                setStatus('idle');
              }}
              className="w-full py-3 bg-slate-700 hover:bg-slate-600 text-slate-200 font-semibold rounded-xl transition-all"
            >
              Upload Another
            </button>
          )}
        </div>
      )}
    </div>
  );
}
