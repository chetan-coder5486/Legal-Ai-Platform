# Legal AI Platform

A full-stack Legal AI Platform that automates contract analysis, risk assessment, and legal research using Natural Language Processing (NLP), Large Language Models (LLMs), and Retrieval-Augmented Generation (RAG).

## Implemented Features

### 1. Document Upload & Intelligent Parsing
* **Multi-Format Support:** Upload and parse `.pdf`, `.docx`, and `.txt` files.
* **Multi-Strategy PDF Extraction:** 
  * Layout-aware extraction using **PyMuPDF** to preserve natural reading order.
  * Fallback to **pdfplumber** for complex layouts and tables.
  * Fallback to **OCR (Tesseract)** for scanned and image-only PDFs.

### 2. AI-Powered Contract Analysis
* **Clause Segmentation & Classification:** Intelligently chunks the contract and classifies clauses into 15+ legal categories (e.g., Governing Law, Termination, Limitation of Liability) using **Sentence Transformers** (`nlpaueb/legal-bert-base-uncased`), with a robust rule-based fallback.
* **Risk Assessment Engine:** Evaluates each clause to determine its risk level (HIGH, MEDIUM, LOW) based on an extensive rule engine. It highlights risky language (e.g., "unlimited liability", "without cause") and identifies protective signals.

### 3. Generative AI Capabilities (via Groq)
* **Clause Redrafting:** Suggests safer, negotiated rewrites for risky clauses using `llama-3.1-8b-instant`.
* **Clause Explanation:** Breaks down complex, high-legalese clauses into simpler, easy-to-understand explanations.

### 4. Continuous Learning & RAG (Retrieval-Augmented Generation)
* **Local Vector Database:** Automatically chunks, embeds (`all-MiniLM-L6-v2`), and ingests analyzed documents into a local **ChromaDB**.
* **Precedents Search:** Search for similar legal clauses from previously uploaded documents to maintain consistency across contracts.
* **Ask Document (Q&A):** Chat with the uploaded document to find specific information or query clauses based on their risk level.

### 5. Frontend Dashboard
* **React SPA:** A modern React frontend built with Vite.
* **Interactive Risk Review:** Visualizes high/medium/low-risk clauses, providing explanations and AI-suggested redrafts at the click of a button.
* **PDF Export:** Generate and export the complete risk assessment report to a PDF.

## Tech Stack
* **Backend:** FastAPI, Sentence Transformers, ChromaDB, PyMuPDF, pdfplumber, pytesseract, Groq API.
* **Frontend:** React, Vite, Tailwind/Vanilla CSS, Axios, html2pdf.js.