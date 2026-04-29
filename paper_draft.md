# Formalizing Oral Transcripts for Improved Retrieval in Educational Video RAG Systems

> **Status**: Draft framework — April 2026
> **Author**: bruceyxli
> **Target**: arXiv preprint → L@S / EMNLP workshop

---

## Abstract

Video lectures are a primary medium for online education, but raw ASR transcripts are poor inputs for RAG systems due to oral redundancy, disfluency, and low information density. We propose a preprocessing pipeline — **Smart Reading** — that rewrites oral transcripts into timestamped formal academic prose before embedding, preserving all technical content while eliminating oral noise. A strict 1:1 segment-to-section mapping with algorithm-locked timestamps prevents hallucination and enables precise video seeking. Experiments on [dataset] show our approach improves Recall@k by X% and end-to-end QA quality by Y% over raw transcript baselines. The system is deployed in the TAI educational platform serving real students.

---

## 1. Introduction

Video lectures are the dominant content format in online education (Coursera, YouTube, university OCW), yet most RAG-based educational QA systems treat transcripts as plain text — ignoring the structural gap between oral and written language.

**The core problem**: ASR transcripts are systematically poor retrieval documents due to three structural deficiencies:
1. **Lexical mismatch** — student queries use formal language ("what is recursion?"); transcripts use oral phrasing ("okay so um like when a function calls itself right")
2. **Low information density** — 3–4× of content is filler words, repetition, meta-commentary, audience interaction
3. **No semantic boundaries** — ASR segments on silence, not topic changes; chunk boundaries are arbitrary

**Existing approaches** sidestep rather than solve this:
- VideoRAG (2025): multimodal retrieval with video frames — doesn't address transcript quality
- WavRAG / VoxRAG (2025): bypass transcripts entirely, retrieve in audio embedding space
- EduVidQA (2024): educational video QA benchmark — uses raw transcripts without preprocessing

**Our approach**: treat oral-to-formal rewriting as a RAG preprocessing step. Each segment is rewritten into dense academic prose with timestamps preserved, then indexed as an independent chunk.

**Contributions**:
1. A formalization-as-preprocessing framework for educational video RAG
2. A 1:1 timestamp-preserving rewrite design that prevents hallucination and enables video seek
3. Parallel batch processing for production-scale efficiency (5× speedup)
4. Empirical validation that formalization improves retrieval and downstream QA
5. Real deployment in TAI serving students across multiple CS courses

---

## 2. Background & Related Work

### 2.1 Retrieval-Augmented Generation
- Lewis et al. (2020): RAG foundation
- BGE-M3: multilingual dense retrieval used in our system
- Dense retrieval survey (2022)

### 2.2 Video RAG
- VideoRAG (arXiv 2501.05874, 2025): LVLM-based, multimodal, no transcript preprocessing
- VideoRAG (arXiv 2502.01549, 2025): extreme long-context, graph-based grounding
- Neither addresses transcript quality as a variable

### 2.3 Educational Video QA
- EduVidQA (2024): 296 CS lecture videos, 5,252 QA pairs — most relevant benchmark
- Uses raw NPTEL/YouTube transcripts; transcript quality not studied as a factor

### 2.4 Transcription-Free RAG
- WavRAG (arXiv 2502.14727, 2025): audio-native embeddings, bypasses ASR
- VoxRAG (arXiv 2505.17326, 2025): silence-aware segmentation + CLAP embeddings
- Competitive direction; our approach retains text interpretability and existing ASR infrastructure

### 2.5 Text Formalization
- Style transfer literature (GYAFC corpus, LLM-based approaches)
- Text Style Transfer review (arXiv 2407.14822, 2024): LLMs outperform specialized models
- **Gap**: formalization evaluated for style metrics only — retrieval impact unexplored

### 2.6 Preprocessing for RAG
- Anthropic Contextual Retrieval (2024): prepend chunk-level context before embedding → 49–67% retrieval error reduction
- Same motivation as our work (preprocessing improves retrieval); different mechanism (context injection vs. text rewriting)
- **Gap**: no study of oral→formal rewriting as retrieval preprocessing

### 2.7 Summary of Gap
```
Formalization (well-studied) ──┐
                               ├── intersection NOT studied
Dense Retrieval (well-studied) ┘
       +
Educational Video (active) ────── no preprocessing evaluation
```

---

## 3. Method

### 3.1 Problem Formulation

Given video $V$, ASR produces segments $S = \{s_i\}$ where each $s_i = (\text{text}_i,\ t^{start}_i,\ t^{end}_i,\ \text{speaker}_i)$.

Goal: construct chunk corpus $C$ such that for query $q$, $\text{Retrieve}(q, C)$ returns segments containing the answer with high recall and ranking quality.

### 3.2 Pipeline Overview

```
Video (mp4)
  │
  ▼
WhisperX ASR
  → segments {text, start_time, end_time, speaker}
  │
  ▼
Pre-merge (timing/speaker rules)
  → max_time_gap = 5s, max_words = 200
  │
  ▼
LLM Formalization  ←── parallel batches (600s/batch)
  → oral → formal academic prose
  → 1:1 strict mapping, timestamp-locked
  → title generated per section
  │
  ▼
Chunk Construction
  → 1 section = 1 chunk
  → content: "## {title}\n[{start}s - {end}s]\n{formal_prose}"
  │
  ▼
BGE-M3 Embedding → SQLite-VSS Index
  │
  ▼
Retrieval + Generation (TAI backend)
```

### 3.3 Oral-to-Formal Rewriting

**Prompt design** (key rules):
- COMPRESS: remove filler words, audience interaction, meta-commentary, repetition
- PRESERVE: all technical terms, code identifiers, worked examples, timestamps
- FORMAT: dense flowing prose, no bullet points
- LANGUAGE: match source language (no translation)

**1:1 strict mapping**: each input segment produces exactly one output section. The LLM cannot merge, split, or reorder. `start_time` and `end_time` are copied exactly from input — algorithm-locked, not LLM-generated. This design:
- Prevents content hallucination (LLM cannot add information not in transcript)
- Preserves temporal alignment for video seek functionality
- Makes output verifiable (section count must match input)

**Multi-speaker support**: speaker labels from WhisperX diarization are injected post-generation, enabling frontend display of speaker transitions.

### 3.4 Parallel Batch Processing

Long videos exceed LLM context limits. Transcript split into 600s batches (≈4,000 input tokens, leaving budget for 4,096 output tokens within vLLM's 12,000 token limit).

Batches sent concurrently via `ThreadPoolExecutor` — vLLM's continuous batching processes all requests in parallel on GPU.

**Speedup**: L01 CS61A (51 min, 5 batches): 72.6s → **23.1s** (68% reduction).

### 3.5 Timestamp-Aligned Chunking

Each formalized section becomes one independent chunk. Chunk boundaries align with semantic/topic transitions rather than arbitrary word counts. Chunks carry `[start-end]` timestamps enabling:
- Precise video navigation in frontend
- Citation of source timestamp in generated answers

---

## 4. Experiments

### 4.1 Dataset

| Dataset | Videos | Duration | QA pairs | Source |
|---------|--------|----------|----------|--------|
| CS61A lectures (ours) | ~30 | ~25h | TBD | UC Berkeley OCW |
| EduVidQA | 296 | — | 5,252 | NPTEL / YouTube |

**QA pair construction** (CS61A):
- Primary: CS61A past exam questions (publicly available) as queries
- Secondary: LLM-generated questions from formalized content, human-filtered

### 4.2 Baselines

| ID | Chunking Strategy | Text Quality |
|----|------------------|--------------|
| B1 | Fixed-size (200 words) | Raw ASR transcript |
| B2 | Time-boundary (ours) | Raw ASR transcript |
| B3 | Time-boundary (ours) | Extractive summary |
| **Ours** | Time-boundary (ours) | Formalized prose |

B1→B2 isolates chunking contribution.
B2→Ours isolates formalization contribution.

### 4.3 Metrics

**Retrieval quality**:
- Recall@1, Recall@5, Recall@10
- NDCG@10

**End-to-end QA quality**:
- BERTScore (F1)
- ROUGE-L
- Human evaluation (relevance, completeness) — subset

**Content analysis**:
- Compression ratio (input words / output words)
- Type-Token Ratio (information density proxy)

### 4.4 Main Results

*(placeholder — to be filled)*

| Method | R@1 | R@5 | NDCG@10 | BERTScore |
|--------|-----|-----|---------|-----------|
| B1: Fixed + Raw | | | | |
| B2: Time + Raw | | | | |
| B3: Time + Extractive | | | | |
| **Ours** | | | | |

### 4.5 Ablation Studies

| Variable | Settings |
|----------|---------|
| Compression aggressiveness | aggressive / moderate / conservative prompt |
| Batch duration | 300s / 600s / 900s |
| Video type | lecture monologue vs. interview/dialogue |
| Embedding model | BGE-M3 vs. OpenAI text-embedding-3 |

---

## 5. Analysis

### 5.1 Case Study
Side-by-side comparison: same query, retrieval results from B2 (raw) vs. Ours (formalized). Show concrete example of lexical mismatch corrected by formalization.

### 5.2 Embedding Space Visualization
t-SNE of raw vs. formalized chunk embeddings — hypothesis: formalized chunks cluster more tightly by topic.

### 5.3 Compression–Quality Trade-off
Curve: compression ratio vs. Recall@5 — does more aggressive compression hurt retrieval?

### 5.4 Failure Cases
When does formalization not help?
- Very short segments (< 15 words) — LLM returns near-empty content
- Highly technical segments already dense (minimal oral noise)
- Non-English videos with English-only model

---

## 6. Deployment: TAI Platform

- Real students, multiple CS courses (CS61A, ...)
- Processing: WhisperX on GPU → parallel vLLM batches → SQLite-VSS
- Latency: ~23s smart reading for 51-min lecture (background processing, not real-time)
- Cost: vLLM local deployment, no per-token API cost

---

## 7. Conclusion

We presented Smart Reading, a preprocessing pipeline that formalizes oral video transcripts before RAG indexing. Key design choices — 1:1 timestamp-preserving rewriting, time-boundary chunking, parallel batch processing — together yield significant retrieval improvements with no hallucination risk.

**Limitations**:
- Adds preprocessing latency (amortized; runs once per video)
- Quality depends on LLM capability
- Non-English videos require language-appropriate models
- Does not handle visual content (equations on blackboard, code demos)

**Future work**:
- Combine formalization + contextual retrieval (Anthropic approach) for additive gains
- Fine-tune embedding model on formalized educational text
- Extend to visual content via multimodal ASR

---

## What We Have / What We Need

### ✅ Already Have
- Complete pipeline code (WhisperX → formalization → chunking → embedding)
- Smart reading output for 3 videos (CS61A OOP, CS61A L01, Jensen Huang interview)
- Compression ratio data: 3.0–3.7× across videos
- Parallel batching implementation (23s for 51-min video)
- Multi-speaker annotation support
- TAI platform deployment

### ❌ Still Needed
- QA evaluation set (CS61A past exams + LLM-generated)
- Retrieval metric numbers (Recall@k, NDCG@k) for all 4 baselines
- Baseline implementations (B1: fixed chunking, B3: extractive)
- BERTScore / ROUGE-L end-to-end numbers
- Embedding space visualization
- Human evaluation (small-scale)

### 📅 Rough Timeline
| Milestone | Target |
|-----------|--------|
| QA set construction | 2 weeks |
| Baseline + retrieval experiments | 3 weeks |
| Writing first draft | 2 weeks |
| arXiv preprint | ~7 weeks from now |
| Revise + submit to venue | after feedback |
