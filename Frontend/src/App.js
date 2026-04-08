import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, Sparkles, X, AlertCircle, Wand2 } from 'lucide-react';
import './App.css';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [caption, setCaption] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  
  const fileInputRef = useRef(null);

  const processFile = (file) => {
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setError('');
      setCaption('');
      
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
      };
      reader.readAsDataURL(file);
    } else {
      setError('Please provide a valid image file within drag area.');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    processFile(file);
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      processFile(file);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError('');
    setCaption('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/caption`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate caption from the server.');
      }

      const data = await response.json();
      setCaption(data.caption);
    } catch (err) {
      setError('Error generating caption. Make sure the backend is running. ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setImagePreview(null);
    setCaption('');
    setError('');
    if (fileInputRef.current) {
        fileInputRef.current.value = '';
    }
  };

  return (
    <div className="app-container">
      {/* Animated Background Mesh */}
      <div className="background-mesh">
        <motion.div 
          animate={{ scale: [1, 1.2, 1], rotate: [0, 90, 0] }} 
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="mesh-blob blob-1" 
        />
        <motion.div 
          animate={{ scale: [1, 1.5, 1], x: [0, 100, 0], y: [0, -50, 0] }} 
          transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
          className="mesh-blob blob-2" 
        />
        <motion.div 
          animate={{ scale: [1, 1.3, 1], x: [0, -100, 0], y: [0, 100, 0] }} 
          transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
          className="mesh-blob blob-3" 
        />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="glass-panel"
      >
        <header className="header">
          <motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
            className="logo-icon-wrapper"
          >
            <Sparkles className="logo-sparkle" size={32} />
          </motion.div>
          <h1>Neural<span className="gradient-text">Vision</span></h1>
          <p className="subtitle">AI-Powered Image Analysis</p>
        </header>

        <main className="main-content">
          <AnimatePresence mode="wait">
            {!imagePreview ? (
              <motion.div 
                key="upload-zone"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className={`upload-zone ${isDragOver ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="upload-icon-wrapper">
                  <UploadCloud size={48} className="upload-icon" />
                </div>
                <h3>Upload an Image</h3>
                <p>Drag and drop or click to browse</p>
                <span className="supported-formats">Supports JPG, PNG, WEBP</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  ref={fileInputRef}
                  className="hidden-input"
                />
              </motion.div>
            ) : (
              <motion.div 
                key="preview-section"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="preview-section"
              >
                <div className="image-container group">
                  <img src={imagePreview} alt="Uploaded Preview" />
                  <div className="image-overlay">
                    <motion.button 
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      className="reset-button" 
                      onClick={resetForm} 
                      disabled={loading}
                      title="Remove Image"
                    >
                      <X size={20} />
                    </motion.button>
                  </div>
                </div>

                {!caption && (
                  <motion.button 
                    whileHover={{ scale: 1.02, boxShadow: "0 0 20px rgba(139, 92, 246, 0.4)" }}
                    whileTap={{ scale: 0.98 }}
                    className={`generate-btn ${loading ? 'loading' : ''}`}
                    onClick={handleSubmit} 
                    disabled={loading}
                  >
                    {loading ? (
                      <div className="flex-center">
                        <motion.div 
                          animate={{ rotate: 360 }}
                          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        >
                          <Wand2 size={20} className="mr-2" />
                        </motion.div>
                        <span className="pulse-text">Analyzing deeply...</span>
                      </div>
                    ) : (
                      <div className="flex-center">
                        <Wand2 size={20} className="mr-2" />
                        <span>Generate Intelligence</span>
                      </div>
                    )}
                  </motion.button>
                )}

                <AnimatePresence>
                  {caption && (
                    <motion.div 
                      initial={{ opacity: 0, y: 20, height: 0 }}
                      animate={{ opacity: 1, y: 0, height: 'auto' }}
                      transition={{ duration: 0.5, type: 'spring', bounce: 0.4 }}
                      className="result-card"
                    >
                      <div className="result-header">
                        <div className="status-indicator"></div>
                        <h4>AI Analysis Result</h4>
                      </div>
                      <p className="caption-text">"{caption}"</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {error && (
              <motion.div 
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                className="error-toast"
              >
                <AlertCircle size={20} className="error-icon" />
                <span>{error}</span>
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </motion.div>
    </div>
  );
}

export default App;