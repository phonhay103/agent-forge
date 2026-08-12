# Agent Guidelines & Design Principles

## 1. Goal: The Parallel Ensemble Pipeline
- **Single Source of Truth**: The primary purpose and value proposition of this package is maintaining a **single parallel execution pipeline** that runs all checkers simultaneously and ensembles their results. 
- **Avoid Complexity**: Do not introduce overly complex sequential pipelines or branching logic unless absolutely necessary. Focus agentic improvements on refining the parallel execution performance and the ensembling logic.

## 2. Best Practice Ensemble
- **Hybrid Approach**: The `AdaptiveHybridEnsembleStrategy` represents the pinnacle of our detection logic. Agents modifying detection rules should prioritize updating this strategy based on empirical evidence.
- **Rule of Thumb**: Deep Learning (`magika`) is superior for unstructured, text, and source code formats, providing high confidence scores based on content structure. Traditional deterministic magic bytes (`libmagic`) are superior for strictly defined binary formats (e.g., PDF, ZIP, PNG). The ensemble logic must respect these domains and prioritize the right tool for the right job.

## 3. Dependency Management
- **Primary AI Dependency**: `magika` is our core, universally compatible detector.
- **Optional Native Dependencies**: `python-magic` requires the C-level `libmagic` library. It must remain in `[project.optional-dependencies]` to prevent breaking environments (like minimal Docker containers) that lack native build tools.
