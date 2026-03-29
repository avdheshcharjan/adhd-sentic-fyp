# FYP Report Outline & Framework
## ADHD Second Brain: An On-Device AI-Powered macOS Application for ADHD Productivity and Wellbeing

**Target: ~55 pages (within NTU 40–65 page limit)**
**Format: Overleaf LaTeX, IEEE numeric citations, NTU CCDS FYP Template**

---

## Framework Principles (Derived from Past NTU FYP Reports)

### From Tjandy Putra (2023) — ASR + Kubernetes
- Strong system architecture diagrams with clear component boundaries
- Dedicated "Design Methodology" section explaining WHY choices were made
- Performance benchmarks presented as tables with clear metrics
- Comparison table of related work (5+ systems compared)

### From Christopher Yong (2023) — Web Speech Recognition
- Clean separation of Literature Review → System Design → Implementation → Testing
- Screenshots of working system embedded throughout Implementation chapter
- Usability evaluation with real metrics (SUS scores, task completion)
- "Challenges and Solutions" subsection in Implementation

### From Joshua Lee (2022) — Docker/K8s ASR Security
- Security-focused justification for architectural decisions
- Deployment architecture diagrams (similar to our on-device privacy argument)
- Performance comparison: before vs after optimization tables
- Clear mapping of objectives → evaluation metrics

### From Tan Hui Zhan (2022) — Web Speech Platform
- Detailed API design documentation within the report
- Data flow diagrams showing request/response lifecycles
- Module-by-module implementation walkthrough
- User study methodology section

### From Lee Yan Zhen (2021) — Sound Event Detection
- ML model comparison tables (accuracy, F1, precision, recall per class)
- Training methodology explanation with hyperparameter details
- Confusion matrix visualization
- Ablation study approach (removing components to measure impact)

### Common patterns across ALL successful reports:
1. **Comparison table** in Literature Review (5–9 existing solutions)
2. **Architecture diagram** as first figure in System Design
3. **Per-class metrics** for any ML component (not just overall accuracy)
4. **Traceability**: Objectives → Design → Implementation → Evaluation
5. **Challenges & Solutions** subsection showing problem-solving ability
6. **Screenshots** of working application
7. **Future Work** that is specific and actionable, not vague

---

## Report Structure

### FRONT MATTER (Roman numeral pages)

- **Title Page**: Project code, full title, student name, "College of Computing and Data Science, Nanyang Technological University", degree, submission date
- **Statement of Originality** (with AI-use disclosure — required since Nov 2025)
- **Supervisor Declaration Statement**
- **Authorship Attribution Statement**
- **Abstract** (~250 words, single-spaced)
  - Key points to include: problem (ADHD + digital distraction), solution (on-device AI macOS app), key technical components (SenticNet, Qwen3-4B/MLX, Mem0, SetFit), key results (86% emotion classification, benchmark numbers), significance (privacy-preserving, first integrated ADHD desktop solution)
- **Acknowledgements**
- **Table of Contents**
- **List of Figures**
- **List of Tables**
- **List of Abbreviations** (ADHD, LLM, NLP, JITAI, XAI, CBM, LoRA, MLX, HRV, SUS, ASRS, PKM, etc.)

---

### CHAPTER 1 — Introduction (5–7 pages)

#### 1.1 Background and Motivation (~2 pages)
- ADHD prevalence: 2.58% persistent to 6.76% symptomatic globally [Faraone 2021, Song 2021]
- Economic burden: $4,336/worker/year in lost productivity [Barkley 2010]
- Digital distraction problem: reciprocal relationship between ADHD and digital media [Thorell 2022]
- Knowledge workers with ADHD: desktop is primary workspace, yet market is mobile-first
- Gap: no integrated solution combining coaching + emotion awareness + screen monitoring + memory

#### 1.2 Problem Statement (~0.5 page)
- Adults with ADHD lack a unified, privacy-preserving desktop tool
- Current solutions require 3–5 separate apps, creating cognitive overhead (itself an ADHD barrier)
- No existing app combines on-device AI, affective computing, and adaptive interventions

#### 1.3 Project Objectives (~1 page)
List 5 specific, measurable objectives:
1. Design and implement an on-device LLM coaching system using Qwen3-4B via Apple MLX
2. Develop an emotion classification pipeline achieving ≥80% accuracy across 6 ADHD-relevant categories
3. Integrate SenticNet affective computing with Concept Bottleneck Models for explainable AI
4. Build a macOS screen monitoring and adaptive intervention system (JITAI)
5. Evaluate the system's performance, accuracy, and resource efficiency on consumer Apple Silicon

#### 1.4 Project Scope and Limitations (~0.5 page)
- Scope: macOS-only (Apple Silicon M-series), single-user, English language
- Not a clinical tool — assistive technology for productivity
- No IRB-approved user study (use persona simulation instead)
- Whoop data requires active subscription

#### 1.5 Contributions and Significance (~1 page)
- First macOS-native ADHD assistant with on-device LLM inference
- Novel integration of SenticNet with ADHD-specific emotion taxonomy
- Privacy-preserving architecture (all AI processing local, <2.5 GB peak RAM)
- Open-source evaluation framework with reproducible benchmarks
- Addresses 8 identified market gaps (reference competitive analysis)

#### 1.6 Report Organization (~0.5 page)
- One paragraph per chapter overview

---

### CHAPTER 2 — Literature Review (10–12 pages)

#### 2.1 ADHD and Executive Function in Digital Environments (~1.5 pages)
- Executive function deficits: inhibition, working memory, cognitive flexibility [Diamond 2013]
- ADHD prevalence and impact statistics [Faraone 2021, Song 2021, Salari 2023]
- Digital media and ADHD: bidirectional relationship [Thorell 2022, Dontre 2021]
- Emotion dysregulation as "fourth core symptom" [Beattie 2025]
- **Key argument**: Desktop environments are the primary workspace but lack ADHD support

#### 2.2 Technology-Based ADHD Interventions (~1.5 pages)
- Meta-analysis findings: digital interventions show small but significant effects (g = −0.32) [García-Peral 2025]
- Umbrella review: 26 systematic reviews, 34,442 participants [García-Peral 2025]
- Effectiveness across modalities: cognitive training, biofeedback, app-based [Shou 2023, Wong 2023]
- Adult ADHD interventions: computerized cognitive approaches [Elbe 2023]
- Digital intervention design principles [Storetvedt 2024]
- **Key argument**: Evidence supports digital interventions, but quality is low and fragmented

#### 2.3 AI and LLM-Powered Mental Health Applications (~1.5 pages)
- Woebot RCT: automated CBT delivery works (F=6.47, P=.01) [Fitzpatrick 2017]
- Current landscape: 50+ mental health chatbots, 22 LLM-based [Yuan 2025]
- Prompt engineering frameworks for safety (MIND-SAFE) [Boit 2025]
- Effectiveness and feasibility review [Amin 2024]
- User experiences with LLM mental health support [Sharma 2024]
- **Key argument**: LLM-based coaching is viable but needs ADHD-specific adaptation

#### 2.4 Affective Computing and SenticNet (~1.5 pages)
- Affective computing foundations [Cambria 2016 IEEE Intelligent Systems]
- SenticNet evolution: versions 1–8 (2010–2024) [Cambria et al. series]
- Neurosymbolic approach: fusing emotion AI and commonsense AI [SenticNet 8, 2024]
- Hourglass of emotions model: pleasantness, attention, sensitivity, aptitude
- **Key argument**: SenticNet provides interpretable affective features ideal for ADHD emotion tracking
- **Institutional connection**: Erik Cambria is NTU faculty

#### 2.5 Second Brain and Personal Knowledge Management (~1 page)
- PARA system and CODE methodology [Forte 2022]
- PKM and self-directed learning [da Silva 2024]
- AI companions in PKM [ACM GROUP 2025]
- How people manage knowledge in "second brains" [Ferreira 2025]
- **Key argument**: PKM frameworks provide conceptual basis for persistent, personalized ADHD support

#### 2.6 On-Device AI and Privacy-Preserving Inference (~1.5 pages)
- Privacy imperative for ADHD apps: monitoring screen activity and emotional state
- Edge LLM deployment surveys [Lin 2025, Xu 2024, Cai 2026]
- Apple MLX framework for efficient Apple Silicon inference [Hannun 2023]
- Apple Intelligence approach [Apple 2024]
- Benchmarking on-device ML on Apple Silicon [Ajayi 2025]
- **Key argument**: On-device inference eliminates data transmission risks entirely

#### 2.7 Review of Existing ADHD Applications (~2 pages)
- **COMPARISON TABLE** (critical — all past reports include this)

| App | Category | Platform | AI | Emotion | Privacy | Memory | Evidence |
|-----|----------|----------|----|---------|---------|--------|----------|
| Focusmate | Body doubling | Web | No | No | Cloud | No | None |
| Freedom | Blocker | Multi | No | No | Cloud | No | None |
| Cold Turkey | Blocker | Desktop | No | No | Local | No | None |
| Brain.fm | Focus music | Multi | No | No | Cloud | No | **Yes** |
| Inflow | Coaching | Mobile | Cloud AI | No | Cloud | No | None |
| Tiimo | Planner | Mobile | Cloud AI | No | Cloud | No | None |
| Goblin Tools | Task AI | Multi | Cloud AI | No | Cloud | No | None |
| Routinery | Routines | Mobile | No | No | Cloud | No | None |
| **Ours** | **Integrated** | **macOS** | **On-device** | **Yes** | **Local** | **Yes** | **Built-in** |

- Discussion of Brain.fm as only peer-reviewed ADHD app [Woods 2024]
- Analysis of 8 market gaps (detailed in research brief)

#### 2.8 Research Gap and Positioning (~0.5 page)
- Synthesize gaps: no integrated desktop solution, no on-device AI, no emotion awareness, no personalized memory
- Position this project as addressing all 8 identified gaps
- Connect each gap back to a project objective

---

### CHAPTER 3 — System Design and Architecture (8–10 pages)

#### 3.1 Overall System Architecture (~2 pages)
- **ARCHITECTURE DIAGRAM** (Figure 1 — most important figure in the report)
  - Three-layer architecture: User Layer → Backend → Data Layer
  - Swift Menu Bar App + React Dashboard + OpenClaw (Telegram/WhatsApp)
  - FastAPI backend (port 8420) with 6 core modules
  - PostgreSQL + pgvector + Docker
- Design philosophy: local-first, modular, load-on-demand
- Data flow overview: screen event → classification → emotion analysis → intervention decision → response

#### 3.2 Design Methodology (~1 page)
- Agile/iterative: 9 implementation phases
- Component-based architecture for independent testing
- Privacy-by-design: all AI inference on-device
- Resource-aware: peak AI memory <2.5 GB for MacBook Pro M4 base (16 GB RAM)

#### 3.3 On-Device LLM Module (~1.5 pages)
- Model selection: Qwen3-4B via Apple MLX (justify over alternatives)
- Quantization strategy for Apple Silicon
- LoRA/QLoRA fine-tuning design [Hu 2022, Dettmers 2023]
- Fallback architecture: GPT-4o-mini for complex queries
- **Design diagram**: LLM inference pipeline

#### 3.4 Affective Computing Module (~1.5 pages)
- 4-tier SenticNet orchestration: Safety → Emotion → ADHD Signals → Personality
- 13 SenticNet API integration architecture
- Emotion taxonomy: 6 ADHD-specific categories (joyful, focused, frustrated, anxious, disengaged, overwhelmed)
- Concept Bottleneck Model for explainability [Koh 2020]
- Hourglass dimension mapping
- **Design diagram**: Emotion analysis pipeline

#### 3.5 Memory and Context Module (~1 page)
- Mem0 integration for conversational memory [Chhikara 2025]
- Sentence embeddings via all-MiniLM-L6-v2 [Reimers 2019, Wang 2020]
- PostgreSQL + pgvector for semantic search
- Pattern recognition: longitudinal tracking of user behaviors and effective strategies

#### 3.6 Screen Monitoring Module (~1 page)
- macOS Accessibility API integration
- 2–3 second polling architecture
- Activity classification: 4-layer cascade
- Browser monitoring, transition detection, idle monitoring
- Privacy consideration: data never leaves device

#### 3.7 Intervention System Design (~1 page)
- JITAI framework [based on Barkley's 5 executive function domains]
- Multi-tier intervention: gentle nudge → active notification → calm overlay → blocking
- Thompson Sampling for adaptive intervention frequency
- XAI explainability: counterfactual explanations for intervention decisions

#### 3.8 UI/UX Design (~0.5 page)
- Menu bar presence: non-intrusive, always accessible
- Intervention popup design with ADHD-friendly visual tokens
- Dashboard wireframes
- Design system: ADHDDesignTokens, animations, spacing

#### 3.9 Technology Stack Selection and Justification (~0.5 page)
- Table summarizing: Component → Technology → Justification

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Backend | FastAPI (Python 3.11) | Async, ML ecosystem |
| Database | PostgreSQL + pgvector | Vector search + relational |
| LLM | Qwen3-4B via MLX | On-device, Apple-optimized |
| Emotions | SenticNet + SetFit | Interpretable + accurate |
| Memory | Mem0 | Production-ready, 26% better than OpenAI memory |
| Desktop | SwiftUI | Native macOS, Accessibility API |
| Dashboard | React + Vite | Fast, component-based |

---

### CHAPTER 4 — Implementation (10–12 pages)

#### 4.1 Development Environment and Tools (~1 page)
- Hardware: MacBook Pro M4 (16 GB)
- Languages: Python 3.11, Swift 5.9, TypeScript
- Key libraries: transformers, sentence-transformers, torch, scikit-learn
- Database: PostgreSQL 16 + pgvector in Docker
- Version control, CI/CD, Makefile automation

#### 4.2 LLM Inference Pipeline (~2 pages)
- MLX integration: model loading, tokenization, generation
- Quantization implementation details
- LoRA adapter training and loading
- System prompt engineering for ADHD coaching
- Context injection: SenticNet results → LLM prompt
- Code snippets showing key implementation patterns
- **Screenshots**: Chat interface, response examples

#### 4.3 Emotion Classification Pipeline (~2 pages)
- **Three approaches explored** (this shows depth of work):
  - Approach A: Hybrid (embedding + SenticNet features) — 74% accuracy
  - Approach B: SetFit/Contrastive learning — **86% accuracy** (production choice)
  - Approach C: DistilBERT fine-tuning — 62–72% accuracy
- SetFit implementation details: CoSENTLoss, all-mpnet-base-v2, unique-pair generation, hard negatives
- Training data: 210 original sentences, 6 ADHD categories
- Key finding: 1 epoch beats 2 epochs (86% vs 84% — overfitting)
- Key finding: LLM-generated bulk data hurt accuracy (82% — anxious class collapsed)
- **Table**: Per-class F1 scores for all three approaches

#### 4.4 SenticNet Affective Computing Pipeline (~1.5 pages)
- 13-API orchestration implementation
- 4-tier processing: Safety → Emotion → ADHD Signals → Personality
- HTTP client implementation
- Hourglass dimension extraction
- Depression, toxicity, engagement, wellbeing scoring
- Error handling and timeout management

#### 4.5 Memory System Implementation (~1 page)
- Mem0 service integration
- Store/retrieve operations
- Semantic search with pgvector
- Profile management for longitudinal tracking

#### 4.6 Screen Monitoring and Activity Classification (~1 page)
- Swift ScreenMonitor: NSWorkspace polling, AppleScript for browser URLs
- TransitionDetector: context switch detection
- Activity classifier: 4-layer cascade (productive → neutral → distraction → unknown)
- Backend endpoint: POST /api/screen with activity data

#### 4.7 Intervention Engine (~1 page)
- JITAI engine: executive function domain mapping
- Thompson Sampling implementation for intervention timing
- XAI explainer: Concept Bottleneck feature extraction
- Multi-tier notification system: nudge → popup → overlay → block

#### 4.8 macOS Application and Web Dashboard (~1 page)
- SwiftUI menu bar app architecture
- React dashboard: emotion timeline, productivity metrics, insights
- API integration between Swift app ↔ FastAPI ↔ React dashboard
- **Screenshots**: Menu bar, intervention popup, dashboard views

#### 4.9 Implementation Challenges and Solutions (~1 page)
**IMPORTANT: This section demonstrates problem-solving ability**
- Challenge: SetFit library incompatible with transformers 5.x → Solution: Manual contrastive learning implementation
- Challenge: LLM-generated training data hurt accuracy → Solution: Curated original data only, quality over quantity
- Challenge: SenticNet API latency → Solution: 4-tier cascade with early termination
- Challenge: Memory constraints on 16 GB MacBook → Solution: Load-on-demand architecture, <2.5 GB peak
- Challenge: Python 3.14 incompatibility → Solution: Pin to Python 3.11 for package compatibility

---

### CHAPTER 5 — Testing and Evaluation (8–10 pages)

#### 5.1 Testing Strategy (~1 page)
- Unit testing: 200+ tests across 24 test files (pytest)
- Integration testing: end-to-end pipeline validation
- Benchmark testing: latency, throughput, memory, energy
- Accuracy evaluation: per-class metrics with held-out test set
- Persona simulation: 5 diverse ADHD personas
- Makefile automation: `make test`, `make bench`, `make eval`, `make all-eval`

#### 5.2 Emotion Classification Evaluation (~2 pages)
- **Comparison table**: 3 approaches side-by-side

| Approach | Overall Accuracy | Best Class F1 | Worst Class F1 | Training Sentences |
|----------|-----------------|--------------|----------------|-------------------|
| A: Hybrid | 74% | — | — | 210 |
| B: SetFit | **86%** | — | — | 210 |
| C: DistilBERT | 62% | — | — | 210 |
| C: DistilBERT (aug) | 72% | — | — | 1,200 |

- **Confusion matrix** for SetFit (production model)
- Per-class precision, recall, F1 for all 6 categories
- Ablation: effect of training data size (210 vs 498 sentences)
- Ablation: effect of epoch count (1 vs 2)
- Discussion: why SenticNet features hurt hybrid approach
- Discussion: why LLM-generated data degraded anxious class

#### 5.3 LLM Performance Evaluation (~1.5 pages)
- Qwen3-4B on Apple MLX benchmarks:
  - Cold start time
  - Time to first token (TTFT)
  - Tokens per second (throughput)
  - Peak memory usage
- Coaching quality evaluation via persona simulation
- Response relevance and ADHD-awareness scoring
- **Table**: LLM performance metrics

#### 5.4 SenticNet Pipeline Evaluation (~1 page)
- API latency per tier (Safety, Emotion, ADHD, Personality)
- Reliability metrics: success rate, timeout frequency
- Hourglass dimension correlation analysis
- End-to-end pipeline waterfall analysis
- **Table**: SenticNet benchmark results

#### 5.5 Memory System Evaluation (~0.5 page)
- Store/retrieve latency at different scales
- Semantic search relevance
- Token cost comparison (reference: Mem0 achieves 90% token savings [Chhikara 2025])

#### 5.6 System Integration and Performance (~1 page)
- Full pipeline benchmarks: screen event → response latency
- Classification throughput
- Energy consumption metrics
- Peak memory across all components running simultaneously
- **Table**: End-to-end system performance

#### 5.7 Persona Simulation Study (~1 page)
- 5 ADHD personas with diverse profiles
- Simulated interaction scenarios
- Diversity scores across persona responses
- ASRS-v1.1 scoring methodology [standardized ADHD assessment]
- SUS-based usability estimation
- **Discussion**: What the simulation reveals about system adaptability

#### 5.8 Comparison with Existing Solutions (~0.5 page)
- Feature comparison table (revisit Chapter 2 table with evaluation data)
- Privacy comparison: on-device vs cloud
- Integration level comparison
- Evidence basis comparison

#### 5.9 Results Discussion and Evaluation Against Objectives (~1 page)
- **Map each result back to a project objective** (traceability)
- Objective 1 → LLM benchmarks show X
- Objective 2 → 86% emotion classification accuracy exceeds 80% target
- Objective 3 → SenticNet + CBM provides interpretable decisions
- Objective 4 → JITAI interventions trigger within Y seconds
- Objective 5 → All metrics demonstrate feasibility on consumer hardware

---

### CHAPTER 6 — Conclusion and Future Work (3–4 pages)

#### 6.1 Summary of Achievements (~1 page)
- Recap of what was built (brief — don't repeat earlier chapters)
- Highlight key technical achievements:
  - 86% emotion classification with only 210 training sentences
  - Full on-device LLM inference on consumer MacBook
  - 13-API SenticNet orchestration pipeline
  - Adaptive JITAI intervention system
  - 200+ automated tests, reproducible benchmarks

#### 6.2 Limitations (~1 page)
- macOS-only (no Windows/Linux/mobile)
- No IRB-approved user study with real ADHD participants
- Emotion classifier trained on generated data, not clinical annotations
- SenticNet API dependency (external service)
- Limited to English language
- Whoop integration requires paid subscription

#### 6.3 Future Work (~1.5 pages)
**Be specific and actionable (not vague)**:
1. Conduct IRB-approved user study with ADHD-diagnosed participants (n=20–30)
2. Cross-platform expansion: iOS companion app, potential Linux port
3. DistilBERT fine-tuning with 30K augmented dataset (training in progress)
4. Federated learning for collaborative model improvement without data sharing
5. Integration with Apple HealthKit for broader physiological signals
6. Multi-language emotion classification
7. Clinical validation: partner with ADHD researchers for longitudinal study
8. App Store deployment and public beta testing

#### 6.4 Lessons Learned (~0.5 page)
- Quality over quantity in ML training data
- On-device constraints drive creative engineering solutions
- Modular architecture enables independent testing and iteration
- Early benchmarking prevents late-stage performance surprises

---

### BACK MATTER

#### References
- IEEE numeric style, aim for **30–50 references**
- All 28+ references from research brief + additional as needed
- Use `\cite{key}` commands matching BibTeX entries

#### Appendix A: User Guide and Screenshots
- Installation steps
- Full screenshot walkthrough of all UI components
- Menu bar, dashboard, intervention popup, calm overlay, settings

#### Appendix B: Additional Test Results
- Complete benchmark JSON outputs
- Full confusion matrices
- Extended persona simulation results
- Energy consumption detailed measurements

#### Appendix C: API Documentation
- Key endpoint specifications
- Request/response examples
- Data model schemas

---

## Page Budget Summary

| Section | Target Pages |
|---------|-------------|
| Front matter | 5–6 (unnumbered/roman) |
| Chapter 1: Introduction | 5–7 |
| Chapter 2: Literature Review | 10–12 |
| Chapter 3: System Design | 8–10 |
| Chapter 4: Implementation | 10–12 |
| Chapter 5: Testing & Evaluation | 8–10 |
| Chapter 6: Conclusion & Future Work | 3–4 |
| References | 2–3 |
| Appendices | 5–8 |
| **TOTAL (main body)** | **44–55** |

---

## Key Figures to Prepare

1. **System Architecture Diagram** (3-layer: User → Backend → Data)
2. **Emotion Classification Pipeline** (SetFit training + inference flow)
3. **SenticNet 4-Tier Orchestration** (Safety → Emotion → ADHD → Personality)
4. **JITAI Intervention Flow** (screen event → classification → decision → response)
5. **LLM Inference Pipeline** (input → MLX → context injection → response)
6. **Memory System Architecture** (Mem0 + pgvector + semantic search)
7. **Confusion Matrix** (6×6 for SetFit emotion classifier)
8. **Screenshot: Menu Bar App**
9. **Screenshot: Intervention Popup**
10. **Screenshot: React Dashboard**
11. **Screenshot: Chat Interface**
12. **Competitive Analysis Table** (9 apps compared)
13. **Technology Stack Diagram**
14. **Benchmark Results Charts** (latency, throughput, memory)

---

## Key Tables to Prepare

1. Existing ADHD App Comparison (Ch. 2)
2. Technology Stack Justification (Ch. 3)
3. Emotion Classifier 3-Way Comparison (Ch. 5)
4. Per-Class F1 Scores (Ch. 5)
5. LLM Performance Metrics (Ch. 5)
6. SenticNet Benchmark Results (Ch. 5)
7. End-to-End System Performance (Ch. 5)
8. Objective → Result Traceability Matrix (Ch. 5)

---

## Writing Priority Order

If time is limited, write chapters in this order:
1. **Chapter 3** (System Design) — anchors the whole report
2. **Chapter 4** (Implementation) — shows you did the work
3. **Chapter 5** (Testing & Evaluation) — demonstrates rigor
4. **Chapter 2** (Literature Review) — establishes knowledge
5. **Chapter 1** (Introduction) — frames everything (easier after other chapters)
6. **Chapter 6** (Conclusion) — summarizes (write last)
7. **Abstract** (write very last — distill the whole report)
