# Analysis Report Page — Design Spec

**Date:** 2026-08-30  
**Status:** Approved  
**Approach:** Single scrollable page (Approach A)

---

## Overview

A comprehensive, forensic-grade analysis report view that presents complete investigation results for a single media file. Combines threat assessment, modality breakdown, evidence chain, provenance tracking, and export options into one authoritative document.

**Primary use case:** Case-level report that contains individual analysis reports as sub-sections.  
**Data source:** Hybrid — real analysis data from `/analyze` endpoint, mock case metadata (timeline, reviewers).

---

## Page Structure

### 1. Report Header

- **Breadcrumb:** `/ Cases / CASE-2026-0847` — links back to cases list
- **Title:** Filename + modality (e.g., "IMG_2024.jpg — Image Analysis")
- **Metadata:** Trace ID + timestamp in mono font
- **Actions:** "Export PDF", "Share Link", "Re-analyze" buttons (right-aligned)

### 2. Threat Assessment Hero (full-width)

- **Gauge:** Semicircular Plotly-style gauge (same as dashboard, larger size)
- **Verdict:** Colored pill badge (HIGH RISK / SUSPICIOUS / LOW RISK)
- **Confidence bar:** Horizontal progress bar below gauge (0-100%)
- **Summary:** Plain English paragraph explaining the result

### 3. Modality Breakdown (4-card grid)

- **Layout:** `grid md:grid-cols-2 lg:grid-cols-4`
- **Each card:** Modality icon + label, confidence bar, threat contribution %
- **States:** Active (green bar), Inactive (grayed out, "N/A")

### 4. Evidence Chain (collapsible, default expanded)

- **Header:** "Evidence Chain (N events)" with expand/collapse chevron
- **Timeline:** Vertical line with colored event markers
- **Each event:** Analyst avatar circle, timestamp, type badge, description, attachments
- **Event types:** Analysis Complete, C2PA Verified, Review Requested, Image Uploaded, Case Created
- **Footer:** "Add Event..." input

### 5. Provenance & Metadata (tabbed, collapsible)

- **Tabs:** C2PA | EXIF | Source | Fingerprints
- **C2PA tab:** Signed status, certificate details, chain of trust visualization
- **EXIF tab:** Camera model, GPS, modification history, tampering indicators
- **Source tab:** URL credibility score, domain age
- **Fingerprints tab:** Perceptual hash, duplicate detection

### 6. Model Details (collapsible, default collapsed)

- **Header:** "Model Details (N models)" with expand/collapse chevron
- **Table:** Model name, version, confidence, processing time

### 7. Actions Bar (sticky bottom)

- **Left:** Report ID in mono font
- **Right:** "Add Comment", "Export PDF", "Close Case" buttons

---

## Components

| Component | File | Purpose |
|-----------|------|---------|
| `ReportPage` | `pages/ReportPage.tsx` | Main page layout |
| `ReportHeader` | `components/report/ReportHeader.tsx` | Breadcrumb, title, actions |
| `ThreatHero` | `components/report/ThreatHero.tsx` | Gauge, verdict, confidence bar |
| `ModalityGrid` | `components/report/ModalityGrid.tsx` | 4 modality cards |
| `EvidenceChain` | `components/report/EvidenceChain.tsx` | Timeline with events |
| `ProvenanceTabs` | `components/report/ProvenanceTabs.tsx` | C2PA/EXIF/Source/Fingerprints |
| `ModelDetails` | `components/report/ModelDetails.tsx` | Model info table |
| `ActionsBar` | `components/report/ActionsBar.tsx` | Sticky bottom actions |

---

## Data Flow

1. User navigates to `/report/:caseId` or `/report/:analysisId`
2. Page fetches analysis data from `GET /analyze/:id` (or uses cached result)
3. Page fetches case metadata from mock data (timeline, reviewers)
4. Components render with real analysis data + mock case metadata

---

## Route

- `/report/:id` — Analysis report page

---

## Design System Compliance

- Void Black background, Carbon cards
- Electric Mint accents for active states
- Sharp corners, no shadows
- Inter + JetBrains Mono typography
- Collapsible sections with smooth height transition
- Accessible: ARIA labels, focus rings, keyboard navigation

---

*This spec is ready for implementation.*
