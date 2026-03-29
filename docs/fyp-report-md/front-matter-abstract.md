# ADHD Second Brain: An On-Device AI-Powered macOS Application for ADHD Productivity and Wellbeing

**Final Year Project Report**

Nanyang Technological University
College of Computing and Data Science

---

## Abstract

Attention-Deficit/Hyperactivity Disorder (ADHD) affects an estimated 2.58% to 6.76% of the global adult population, imposing a substantial economic burden of approximately USD 4,336 per affected worker per year in lost productivity. The proliferation of digital devices and persistent connectivity has compounded core ADHD symptoms, including attentional dysregulation, working memory deficits, and impaired executive function. Despite the prevalence of productivity applications on the market, no integrated desktop tool existed that combined conversational coaching, real-time emotion awareness, screen activity monitoring, and persistent semantic memory within a single privacy-preserving framework.

This project developed an on-device AI-powered macOS application that addressed these gaps through the integration of several complementary subsystems. A Qwen3-4B large language model, executed locally via the Apple MLX framework, provided conversational coaching at 37.1 tokens per second. A SetFit contrastive learning pipeline achieved 86% emotion classification accuracy across six ADHD-specific affective categories using only 210 training sentences. SenticNet affective computing, accessed through 13 application programming interfaces and grounded in the Hourglass of Emotions model, supplied fine-grained sentiment and sentic features with 100% reliability. Mem0 semantic memory, backed by pgvector, attained 95% top-1 relevance in context retrieval. A five-tier activity classification engine processed screen titles at 549 titles per second, and Just-in-Time Adaptive Interventions, structured around Barkley's executive function domains, delivered context-sensitive behavioural nudges.

Evaluation demonstrated that the system consumed 21,314 millijoules per inference, representing approximately 1.4% battery drain per hour, while maintaining a peak memory footprint below 3 gigabytes. All predefined project objectives were exceeded. The application constituted the first macOS-native ADHD assistant with a fully on-device large language model, addressed eight identified market gaps, and contributed an open-source evaluation framework with reproducible benchmarks.

---

## List of Abbreviations

| Abbreviation | Definition |
|:---|:---|
| ADHD | Attention-Deficit/Hyperactivity Disorder |
| AI | Artificial Intelligence |
| ANE | Apple Neural Engine |
| API | Application Programming Interface |
| ASRS | Adult ADHD Self-Report Scale |
| CBM | Concept Bottleneck Model |
| CBT | Cognitive Behavioural Therapy |
| CLI | Command-Line Interface |
| CPU | Central Processing Unit |
| CV | Coefficient of Variation |
| DRAM | Dynamic Random-Access Memory |
| E2E | End-to-End |
| EF | Executive Function |
| F1 | F1-Score (harmonic mean of precision and recall) |
| GPU | Graphics Processing Unit |
| HRV | Heart Rate Variability |
| IEEE | Institute of Electrical and Electronics Engineers |
| IRB | Institutional Review Board |
| JITAI | Just-in-Time Adaptive Intervention |
| LLM | Large Language Model |
| LoRA | Low-Rank Adaptation |
| MLX | Apple Machine Learning Framework |
| MPS | Metal Performance Shaders |
| NLP | Natural Language Processing |
| NTU | Nanyang Technological University |
| PARA | Projects, Areas, Resources, Archives |
| PKM | Personal Knowledge Management |
| QLoRA | Quantised Low-Rank Adaptation |
| RAG | Retrieval-Augmented Generation |
| RSS | Resident Set Size |
| STS | Semantic Textual Similarity |
| SUS | System Usability Scale |
| XAI | Explainable Artificial Intelligence |

---

## List of Figures

| Figure | Title | Page |
|:---|:---|:---:|
| Figure 3.1 | Three-Layer System Architecture (User Layer, Backend, Data Layer) | |
| Figure 3.2 | On-Device LLM Inference Pipeline | |
| Figure 3.3 | SenticNet Four-Tier Orchestration Pipeline (Safety, Emotion, ADHD Signals, Personality) | |
| Figure 3.4 | Memory System Architecture (Mem0, pgvector, and Semantic Search) | |
| Figure 3.5 | JITAI Intervention Decision Flow | |
| Figure 3.6 | Technology Stack Overview | |
| Figure 4.1 | Chat Interface with Extended Reasoning (/think Mode) | |
| Figure 4.2 | Emotion Classification Pipeline (SetFit Training and Inference) | |
| Figure 4.3 | SenticNet API Orchestration Implementation | |
| Figure 4.4 | Menu Bar Application Screenshot | |
| Figure 4.5 | Intervention Popup with ADHD-Friendly Visual Tokens | |
| Figure 4.6 | React Dashboard Displaying Emotion Timeline and Productivity Metrics | |
| Figure 5.1 | SetFit Confusion Matrix (Six-by-Six, Production Model at 86% Accuracy) | |
| Figure 5.2 | End-to-End Pipeline Latency Waterfall | |
| Figure 5.3 | Energy Consumption Breakdown (GPU 71.8%, DRAM 21.5%, CPU 6.8%) | |

---

## List of Tables

| Table | Title | Page |
|:---|:---|:---:|
| Table 2.1 | Comparison of Existing ADHD Applications | |
| Table 3.1 | Technology Stack Selection and Justification | |
| Table 5.1 | Emotion Classifier Approach Comparison (Nine Approaches) | |
| Table 5.2 | SetFit Per-Class F1 Scores (Six Categories) | |
| Table 5.3 | LLM Inference Performance Metrics | |
| Table 5.4 | SenticNet Benchmark Results | |
| Table 5.5 | End-to-End System Performance Summary | |
| Table 5.6 | Objective-to-Result Traceability Matrix | |

---
