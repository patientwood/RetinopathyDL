
import React, { useState, useRef } from "react";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL || "";

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const dropRef = useRef(null);

  const onFileSelect = (f) => {
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError("");
  };

  const handleFileInput = (e) => {
    const f = e.target.files[0];
    onFileSelect(f);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    dropRef.current.classList.add("drop-active");
  };
  const handleDragLeave = (e) => {
    e.preventDefault();
    dropRef.current.classList.remove("drop-active");
  };
  const handleDrop = (e) => {
    e.preventDefault();
    dropRef.current.classList.remove("drop-active");
    const f = e.dataTransfer.files[0];
    onFileSelect(f);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select an image first.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_URL}/api/predict-image`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        if (res.status === 503) {
          throw new Error("The prediction model is unavailable.");
        }
        const txt = await res.text();
        throw new Error(txt || "Sever error");
      }

      const data = await res.json();
      setResult(data);  
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="header">
        <h1>Retinopathy Screening</h1>
        <p>Upload a fundus/retina image to check for Diabetic Retinopathy</p>
      </header>

      <main className="main">
        <div
          className="dropzone"
          ref={dropRef}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {preview ? (
            <img src={preview} alt="preview" className="preview" />
          ) : (
            <p>
              Drag & drop an image here
              <br /> or <span className="browse">click to browse</span>
            </p>
          )}
          <input 
            type="file"
            accept="image/*"
            onChange={handleFileInput}
            className="file-input"
          />
        </div>

        <button onClick={handleSubmit} disabled={loading} className="submit-btn">
          {loading ? "Predicting..." : "Run Prediction"}
        </button>

        {error && <div className="error">{error}</div>}

        {result && (
          <div className="result-card">
            <h2>Result</h2>
            <p className={`pred ${result.pred_class === "DR" ? "dr" : "no-dr"}`}>
              {result.pred_class === "DR"
                ? "Diabetic Retinopathy Detected"
                : "No Diabetic Retinopathy Detected"}
            </p>
            <p> 
              <strong>Prob (No DR):</strong>{" "}
              {(result.prob_no_dr * 100).toFixed(2)}%
            </p>
            <p>
              <strong>Prob (DR):</strong>{" "}
              {(result.prob_dr * 100).toFixed(2)}%
            </p>
            <small>This result is for educational use only. Please consult a licensed eye-care professional for any medical concerns.</small>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;