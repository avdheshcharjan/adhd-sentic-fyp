# Chapter 3: System Design and Architecture

This chapter presents the system design and architecture of the ADHD Second Brain, an on-device intelligent assistant that combines affective computing, local large language model inference, and just-in-time adaptive interventions to support individuals with Attention-Deficit/Hyperactivity Disorder (ADHD). The system is designed around three core principles: (1) privacy-first on-device processing, (2) real-time responsiveness for screen monitoring, and (3) interpretable emotional intelligence grounded in established psychological frameworks. The following sections detail the architectural decisions, module designs, data flows, and technology selections that collectively realise these principles.

---

## 3.1 Overall System Architecture

The ADHD Second Brain adopts a three-layer architecture comprising a User Layer, a Backend Layer, and a Data Layer. This layered decomposition enforces a strict separation of concerns: the User Layer is responsible exclusively for presentation and user interaction; the Backend Layer encapsulates all business logic, machine learning inference, and orchestration; and the Data Layer manages persistent storage and vector-based semantic retrieval. All three layers execute on the user's local machine, with external service calls made only when strictly necessary and never for sensitive screen-capture data. Figure 3.1 provides a high-level overview of this architecture.

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\textwidth]{figures/ch3_system_architecture.pdf}
  \caption{Three-layer system architecture of the ADHD Second Brain. The User Layer comprises a SwiftUI menu bar application, a React dashboard, and the OpenClaw interface. The Backend Layer hosts the FastAPI server with its constituent modules. The Data Layer combines PostgreSQL with pgvector and SQLite for persistent and vector-indexed storage.}
  \label{fig:system_architecture}
\end{figure}
```

**User Layer.** The User Layer consists of three client-facing components. The primary interface is a native macOS menu bar application built in SwiftUI, which operates as a lightweight persistent process consuming approximately 25 MB of RAM. This application leverages the macOS Accessibility API to perform screen captures at a polling interval of two to three seconds, forwarding captured metadata to the Backend Layer over a local HTTP connection. The second component is a React-based dashboard, built with Vite, that provides users with historical analytics, emotional trend visualisations, and intervention history. The third component is OpenClaw, a conversational interface through which users may interact with the system via natural language—including venting, task planning, and reflective journaling.

**Backend Layer.** The Backend Layer is implemented as a FastAPI application bound to `localhost:8420`, ensuring that no data traverses the network boundary unless explicitly routed to an external API. The backend comprises six principal modules: (1) the SenticNet Pipeline, which orchestrates affective analysis across thirteen cloud-hosted SenticNet APIs \cite{cambria2024}; (2) the JITAI Engine, which evaluates real-time behavioural metrics against Barkley's five executive function domains \cite{barkley2010} to determine whether an intervention is warranted; (3) the Whoop Service, which integrates physiological data via the Whoop API v2 over OAuth 2.0; (4) the MLX Inference module, which hosts the Qwen3-4B language model quantized to 4-bit precision on Apple Silicon via the MLX framework; (5) the Memory module, which coordinates Mem0 and PostgreSQL for long-term user memory with semantic retrieval; and (6) the XAI Explainer, which employs a Concept Bottleneck Model to generate human-interpretable explanations for system decisions. At steady state with all models loaded, the backend consumes approximately 500 MB of system RAM in addition to approximately 2.3 GB of GPU memory allocated to the quantized language model.

**Data Layer.** The Data Layer employs PostgreSQL extended with pgvector for combined relational and vector storage. User activity logs, emotional analysis results, intervention records, and conversation histories are stored relationally, while Mem0-generated memory embeddings are indexed via pgvector to enable sub-second semantic similarity search. A lightweight SQLite database serves as a local cache for configuration state and transient metadata that does not require the guarantees of a full relational engine.

**External Services.** The system makes controlled use of four external services. SenticNet Cloud provides thirteen specialised affective computing APIs spanning emotion recognition, polarity detection, personality profiling, and concept extraction \cite{cambria2024}. The Whoop API v2 supplies physiological metrics including heart rate variability, sleep quality, and recovery scores. For complex reasoning tasks that exceed the capacity of the on-device model, the system routes queries to Claude Sonnet (Anthropic); for high-frequency, lower-complexity tasks such as sentence classification and summarisation, GPT-4o-mini (OpenAI) is employed. The selection between external LLM providers is governed by a routing heuristic that considers query complexity, latency requirements, and token budget.

**Data Flows.** The architecture supports two principal data flows, each with distinct latency targets. The Hot Path handles screen monitoring events with a target end-to-end latency of less than 100 milliseconds, encompassing activity classification, metric computation, and intervention evaluation. The Warm Path handles conversational interactions—including chat and venting—with a target latency of less than three seconds, encompassing multi-tier affective analysis, LLM generation, and memory persistence. These flows are detailed in Sections 3.6 and 3.4 respectively. Figure 3.2 illustrates both data flows and their constituent processing stages.

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\textwidth]{figures/ch3_data_flows.pdf}
  \caption{Hot Path and Warm Path data flows. The Hot Path (solid arrows) processes screen monitoring events through activity classification, ADHD metrics computation, and JITAI evaluation within a 100\,ms budget. The Warm Path (dashed arrows) processes conversational input through a four-tier SenticNet pipeline, LLM generation, and memory storage within a 3\,s budget.}
  \label{fig:data_flows}
\end{figure}
```

---

## 3.2 Design Methodology

The development of the ADHD Second Brain followed an agile, iterative methodology structured across nine implementation phases. This approach was selected for two reasons: first, the system's reliance on multiple machine learning models whose performance characteristics could not be fully predicted a priori demanded rapid prototyping and evaluation cycles; second, the interdependencies between affective computing accuracy, intervention timing, and user experience necessitated continuous integration testing across modules.

**Phase Organisation.** The nine phases were organised to establish foundational infrastructure before layering intelligence. Phases 1 and 2 focused on backend scaffolding and database schema design. Phase 3 introduced screen monitoring and the rule-based activity classifier. Phase 4 integrated the SenticNet pipeline and the custom emotion taxonomy. Phase 5 developed the JITAI engine and intervention delivery mechanisms. Phase 6 added on-device LLM inference via MLX. Phase 7 implemented the memory and context system with Mem0 and pgvector. Phase 8 built the React dashboard and refined the SwiftUI menu bar application. Phase 9 conducted end-to-end evaluation, including the benchmarking of the emotion classifier and latency profiling of both data flows.

**Design Principles.** Four design principles governed architectural decisions throughout all phases. The first, *privacy by architecture*, mandates that raw screen captures and conversation transcripts never leave the local machine; only anonymised metadata is transmitted to external APIs when enrichment is required. The second, *fail-fast over fail-safe*, requires that components throw errors immediately upon encountering unexpected states rather than falling back to degraded operation—a deliberate choice for a pre-production system where silent failures would mask integration defects. The third, *interpretability*, requires that every system decision—from emotion classification to intervention triggering—be traceable to named concepts and explainable to the user via the XAI module. The fourth, *resource consciousness*, constrains peak AI memory to 2.5 GB and employs load-on-demand model instantiation to ensure the system remains usable on consumer-grade Apple Silicon hardware.

**Iterative Evaluation.** Each phase concluded with a structured evaluation against predefined acceptance criteria. For machine learning modules, these criteria were expressed as minimum accuracy thresholds on held-out test sets (e.g., 80% weighted F1 for emotion classification). For real-time modules, criteria were expressed as latency percentile targets (e.g., p99 < 100 ms for the Hot Path). Regressions detected during evaluation triggered immediate remediation within the same phase before proceeding to the next.

---

## 3.3 On-Device LLM Module

The On-Device LLM Module provides natural language understanding and generation capabilities without requiring persistent cloud connectivity. This module is central to the system's privacy guarantees: by performing inference locally, the user's conversational data—which frequently contains sensitive emotional disclosures—remains on-device at all times.

**Model Selection.** The module employs Qwen3-4B \cite{yang2025}, a 4-billion-parameter causal language model from the Qwen family, selected after a structured evaluation of candidate models against four criteria: (1) parameter count compatible with consumer Apple Silicon memory constraints, (2) availability of high-quality 4-bit quantised weights, (3) strong performance on instruction-following and conversational benchmarks relative to model size, and (4) support for the Apple MLX inference framework. Qwen3-4B was found to offer the best trade-off among these criteria, outperforming similarly-sized alternatives including Phi-3-mini and Llama-3.2-3B on the system's internal evaluation suite of ADHD-relevant conversational tasks.

**Quantisation and Inference.** The model is quantised to 4-bit precision using the GPTQ method as implemented in the MLX ecosystem, reducing its memory footprint from approximately 8 GB (FP16) to approximately 2.3 GB while preserving over 95% of full-precision task accuracy on the system's evaluation suite. Inference is executed via Apple's MLX framework \cite{hannun2023}, which provides first-class support for Apple Silicon's unified memory architecture, enabling zero-copy data sharing between CPU and GPU. On an M-series chip, the quantised model achieves a measured throughput of 37.1 tokens per second, which is sufficient for interactive conversational use. Table 3.1 summarises the model's performance characteristics.

```latex
\begin{table}[htbp]
  \centering
  \caption{On-device LLM performance characteristics for Qwen3-4B (4-bit quantised) on Apple Silicon via MLX.}
  \label{tab:llm_performance}
  \begin{tabular}{ll}
    \toprule
    \textbf{Metric} & \textbf{Value} \\
    \midrule
    Parameter count & 4 billion \\
    Quantisation & 4-bit (GPTQ) \\
    GPU memory footprint & $\sim$2.3\,GB \\
    Inference throughput & 37.1 tokens/s \\
    Time to first token & $\sim$180\,ms \\
    Framework & Apple MLX \\
    \bottomrule
  \end{tabular}
\end{table}
```

**Load-on-Demand Strategy.** To minimise idle resource consumption, the LLM is not loaded into memory at system startup. Instead, the module employs a load-on-demand strategy: the model weights are memory-mapped upon the first conversational request and remain resident for a configurable idle timeout period (default: 15 minutes), after which they are evicted. This ensures that the system's peak AI memory footprint of approximately 2.5 GB is incurred only during active conversational sessions. During screen-monitoring-only operation, the backend operates at approximately 500 MB total, leaving ample headroom for the user's primary applications.

**Context Injection.** Prior to each LLM invocation, the module constructs a structured prompt that incorporates three sources of contextual information: (1) the user's current emotional state as determined by the SenticNet pipeline (Section 3.4), including the classified emotion, polarity score, and any detected sarcasm; (2) relevant long-term memories retrieved from the Mem0 system via semantic search (Section 3.5); and (3) the user's current screen activity context, including active application, focus score, and distraction ratio. This context injection transforms the general-purpose language model into an ADHD-aware conversational agent capable of referencing the user's historical patterns, current emotional state, and ongoing task context.

**External LLM Routing.** For queries that exceed the on-device model's capabilities—such as those requiring extensive world knowledge, multi-step reasoning over long documents, or generation of structured analytical reports—the module routes requests to external LLM providers. A routing heuristic classifies incoming queries into three tiers: Tier 1 (simple, frequent) queries are handled by the on-device Qwen3-4B; Tier 2 (moderate complexity, high frequency) queries are routed to GPT-4o-mini for cost efficiency; and Tier 3 (complex, infrequent) queries are routed to Claude Sonnet for maximum reasoning quality. The routing decision is made prior to inference and is logged for subsequent analysis.

---

## 3.4 Affective Computing Module

The Affective Computing Module is responsible for understanding the user's emotional state from textual input, combining the interpretability of lexicon-based sentiment analysis with the accuracy of modern contrastive learning. The module operates along two axes: a multi-tier SenticNet orchestration pipeline for comprehensive affective feature extraction, and a custom SetFit-based emotion classifier for ADHD-specific emotion categorisation.

**SenticNet Pipeline.** SenticNet \cite{cambria2024} provides a semantics-aware framework for sentiment analysis grounded in the Hourglass of Emotions model, which decomposes affective states along four dimensions: pleasantness (introspection), attention (temper), sensitivity, and aptitude (attitude). The system orchestrates thirteen SenticNet Cloud APIs in a four-tier cascade designed to balance comprehensiveness with latency. Tier 1 (Safety) invokes depression detection, toxicity classification, and emotional intensity estimation; if any safety threshold is exceeded, the system immediately triggers an emergency response pathway, bypassing subsequent tiers. Tier 2 (Core Emotional) performs emotion recognition, polarity detection, subjectivity analysis, and sarcasm detection. Tier 3 (ADHD Signals) extracts engagement levels, wellbeing indicators, conceptual associations, and aspect-level sentiment. Tier 4 (Deep Analysis) performs personality profiling and ensemble aggregation, and is invoked only when the preceding tiers yield ambiguous or conflicting signals. Figure 3.3 illustrates this tiered cascade.

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.85\textwidth]{figures/ch3_senticnet_pipeline.pdf}
  \caption{Four-tier SenticNet orchestration pipeline. Each tier is evaluated sequentially; Tier~1 may short-circuit to an emergency pathway. Tier~4 is invoked conditionally based on signal ambiguity in Tiers~2 and~3.}
  \label{fig:senticnet_pipeline}
\end{figure}
```

**Emotion Taxonomy.** Rather than adopting a general-purpose emotion taxonomy such as Ekman's six basic emotions, the system defines six ADHD-specific emotional categories: *joyful*, *focused*, *frustrated*, *anxious*, *disengaged*, and *overwhelmed*. This taxonomy was developed in consultation with ADHD literature \cite{barkley2010, diamond2013} and reflects the emotional states most salient to executive function regulation. Notably, *focused* and *disengaged* are not standard emotional categories but are included because they directly correspond to attentional states central to ADHD symptomatology. *Overwhelmed* captures the executive overload state that frequently precedes task abandonment in individuals with ADHD.

**SetFit Emotion Classifier.** The emotion classifier employs a contrastive learning framework inspired by SetFit (Sentence Transformer Fine-Tuning) \cite{reimers2019}, implemented manually rather than through the SetFit library, due to incompatibilities between the library and the project's transformer dependency versions. The base encoder is `all-mpnet-base-v2`, a 110-million-parameter sentence transformer pre-trained on over one billion sentence pairs, selected for its strong performance on semantic textual similarity benchmarks.

Training employs CoSENT loss over all unique positive and negative pairs, including hard negatives mined from semantically adjacent categories (e.g., *anxious*–*overwhelmed*, *frustrated*–*disengaged*). The training corpus comprises 210 manually curated sentences distributed across the six categories. A key empirical finding during development was that a single training epoch yields superior generalisation (86% weighted F1) compared to two epochs (84% weighted F1), indicating that additional training induces overfitting on this small dataset. Furthermore, an attempt to augment the training set with 288 LLM-generated boundary sentences degraded performance to 82% weighted F1, with the *anxious* class F1 dropping from 0.80 to 0.62. This regression was attributed to distributional shift introduced by the generated data and class imbalance in the augmented set. Table 3.2 summarises classifier performance across approaches.

```latex
\begin{table}[htbp]
  \centering
  \caption{Emotion classifier accuracy comparison across approaches. Weighted F1 scores are reported on a held-out test set of 50 manually labelled sentences.}
  \label{tab:emotion_classifiers}
  \begin{tabular}{lcc}
    \toprule
    \textbf{Approach} & \textbf{Training Data} & \textbf{Weighted F1} \\
    \midrule
    Baseline SenticNet & --- & 0.28 \\
    Hybrid (Embedding + SenticNet) & 210 sentences & 0.74 \\
    DistilBERT fine-tuned & 210 sentences & 0.62 \\
    DistilBERT fine-tuned & 1,200 augmented & 0.72 \\
    SetFit (CoSENT, 1 epoch) & 210 sentences & \textbf{0.86} \\
    SetFit (CoSENT, 1 epoch) & 498 sentences & 0.82 \\
    \bottomrule
  \end{tabular}
\end{table}
```

**Concept Bottleneck Model for Explainability.** To satisfy the interpretability design principle, the system wraps the emotion classifier within a Concept Bottleneck Model (CBM) \cite{koh2020}. Rather than presenting the user with an opaque classification, the CBM first predicts a set of intermediate human-interpretable concepts—such as "frustration with task switching," "anxiety about deadlines," or "low engagement with current content"—and then derives the final emotion label from these concepts. This two-stage architecture enables the XAI Explainer module to generate natural-language explanations of the form: "You appear to be feeling *overwhelmed* because the system detected high task-switching frequency, negative polarity toward the current assignment, and elevated emotional intensity." Such explanations support the user's metacognitive awareness, a known protective factor in ADHD self-regulation \cite{diamond2013}.

---

## 3.5 Memory and Context Module

The Memory and Context Module provides the system with longitudinal awareness of the user's behavioural patterns, emotional history, and conversational context, transforming the ADHD Second Brain from a stateless reactive system into a personalised, context-aware assistant.

**Mem0 Integration.** The module employs Mem0 \cite{chhikara2025} as its primary memory abstraction layer. Mem0 automatically extracts salient facts from conversational exchanges and stores them as structured memory entries with associated metadata (timestamp, source, confidence score). In comparative evaluation, Mem0 demonstrated a 26% improvement in memory retrieval relevance over the baseline OpenAI memory implementation, as measured by Mean Reciprocal Rank on a curated set of ADHD-specific conversational recall queries. This advantage is attributed to Mem0's graph-based memory organisation, which captures relational structure between memories.

**PostgreSQL + pgvector.** Memory embeddings generated by Mem0 are persisted in PostgreSQL using the pgvector extension, which provides efficient approximate nearest-neighbour search over high-dimensional vector spaces. The embedding model used for vectorisation is `all-mpnet-base-v2`—the same model employed by the emotion classifier—ensuring representational consistency across the memory and affective computing modules. At query time, the module performs a cosine similarity search over the vector index to retrieve the top-k most relevant memories, which are then injected into the LLM prompt as described in Section 3.3.

**Semantic Retrieval Pipeline.** When the user initiates a conversational interaction, the Memory module executes a retrieval pipeline comprising three stages. First, the user's input is encoded into a dense vector using the shared sentence transformer. Second, a pgvector similarity search retrieves candidate memories ranked by cosine similarity. Third, a re-ranking step filters candidates by temporal recency and contextual relevance to the user's current activity. This three-stage pipeline ensures that the LLM receives memories that are both semantically relevant and temporally appropriate.

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.75\textwidth]{figures/ch3_memory_pipeline.pdf}
  \caption{Semantic memory retrieval pipeline. User input is encoded, matched against the pgvector index, and re-ranked by temporal recency and activity context before injection into the LLM prompt.}
  \label{fig:memory_pipeline}
\end{figure}
```

---

## 3.6 Screen Monitoring Module

The Screen Monitoring Module implements the Hot Path data flow, continuously observing the user's desktop activity and computing real-time ADHD-relevant behavioural metrics. This module is the system's primary sensor for detecting attentional state and triggering just-in-time interventions.

**Screen Capture.** The SwiftUI menu bar application uses the macOS Accessibility API to poll the active window metadata every two to three seconds. Each poll captures the active application name, window title, and—where available—the URL of the frontmost browser tab. Notably, the system captures only metadata, not pixel-level screenshots, preserving user privacy while providing sufficient signal for activity classification.

**Activity Classifier.** The Activity Classifier employs a four-level hierarchical rule-based system designed to resolve activity categories with minimal computational cost, resorting to more expensive methods only when simpler levels are insufficient. Level 1 (L1) matches the application name against a curated dictionary of known applications. Level 2 (L2), invoked only for browser applications, matches the URL domain against a domain classification dictionary. Level 3 (L3) applies keyword matching to the window title, capturing cases where the domain alone is ambiguous. Level 4 (L4), invoked only when Levels 1–3 fail to produce a confident classification, routes the metadata to the on-device embedding model for semantic classification. Levels 1–3 execute in under 5 milliseconds; Level 4 incurs approximately 8 milliseconds but is invoked for only 22% of events.

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.7\textwidth]{figures/ch3_activity_classifier.pdf}
  \caption{Four-level hierarchical activity classifier. Each level is attempted in sequence; classification terminates at the first level that produces a confident result. L4 (embedding fallback) is invoked only when rule-based levels are insufficient.}
  \label{fig:activity_classifier}
\end{figure}
```

**ADHD Metrics Engine.** The classified activity events feed into an in-memory metrics engine that computes four real-time behavioural indicators: (1) *context switch rate*, defined as the number of distinct application transitions per unit time; (2) *focus score*, a composite metric reflecting sustained engagement with a single task-relevant application; (3) *distraction ratio*, the proportion of time spent in non-task-relevant applications within a sliding window; and (4) *streak*, the duration of uninterrupted focus on a single activity category. These metrics are computed incrementally with each new event, requiring less than 1 millisecond per update.

---

## 3.7 Intervention System Design

The Intervention System implements a Just-In-Time Adaptive Intervention (JITAI) framework grounded in Barkley's model of five executive function (EF) domains: inhibition, working memory, emotional self-regulation, self-motivation, and planning/problem-solving \cite{barkley2010}. The system's core hypothesis, informed by Diamond's framework for EF development \cite{diamond2013}, is that targeted micro-interventions delivered at moments of detected executive dysfunction can support self-regulation without requiring conscious user initiation.

**JITAI Engine.** The JITAI Engine is a rule-based evaluation engine that consumes the real-time metrics produced by the ADHD Metrics Engine (Section 3.6) and the emotional state produced by the Affective Computing Module (Section 3.4). For each incoming event, the engine evaluates a set of intervention rules, each associated with one of Barkley's five EF domains. The engine processes all rules in under 2 milliseconds, well within the Hot Path latency budget.

**Thompson Sampling for Personalisation.** Because individuals with ADHD exhibit heterogeneous symptom profiles, the system must learn which intervention types are most effective for each user. The JITAI Engine employs Thompson Sampling, a Bayesian bandit algorithm, to balance exploration of untested intervention types with exploitation of those known to be effective. Each intervention type maintains a Beta distribution parameterised by observed successes and failures. Over time, the posterior distributions converge, and the system preferentially selects interventions with the highest expected efficacy for each user.

**Multi-Tier Intervention Delivery.** Interventions are delivered along a four-tier escalation ladder: (1) *nudge*, a subtle visual indicator in the menu bar; (2) *popup*, a brief notification containing a specific actionable suggestion; (3) *overlay*, a semi-transparent screen overlay that gently interrupts the user's current activity; and (4) *block*, a temporary restriction on access to identified distraction sources. Escalation proceeds only if lower tiers fail to elicit a return to focus.

```latex
\begin{table}[htbp]
  \centering
  \caption{Multi-tier intervention escalation ladder with approximate triggering conditions and delivery mechanisms.}
  \label{tab:intervention_tiers}
  \begin{tabular}{llll}
    \toprule
    \textbf{Tier} & \textbf{Type} & \textbf{Trigger Condition} & \textbf{Delivery} \\
    \midrule
    1 & Nudge & Mild metric deviation & Menu bar indicator \\
    2 & Popup & Sustained metric deviation & macOS notification \\
    3 & Overlay & Escalation from Tier~2 & Semi-transparent overlay \\
    4 & Block & Escalation from Tier~3 & Application restriction \\
    \bottomrule
  \end{tabular}
\end{table}
```

---

## 3.8 UI/UX Design

The user interface comprises two complementary surfaces designed for distinct interaction modalities. The SwiftUI menu bar application provides an always-available, minimal-footprint entry point for real-time status awareness and conversational interaction. It displays the user's current focus score, emotional state, and streak duration in a compact popover, and provides access to the OpenClaw conversational interface. The design follows macOS Human Interface Guidelines to ensure visual consistency with the host operating system and minimise cognitive overhead—a critical consideration for users with ADHD, who are disproportionately affected by interface complexity.

The React dashboard, served locally via Vite, provides a richer analytical interface for reviewing historical trends, emotional trajectories, and intervention efficacy over configurable time windows. Both interfaces are designed with ADHD-informed principles: minimal visual clutter, high-contrast colour coding for metric states (green for focused, amber for drifting, red for distracted), and progressive disclosure of detail to avoid information overload. Intervention notifications are designed to be non-punitive and action-oriented, framing suggestions positively.

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=\textwidth]{figures/ch3_ui_wireframes.pdf}
  \caption{UI wireframes. Left: SwiftUI menu bar popover showing real-time metrics and conversational entry point. Right: React dashboard showing historical focus analytics and emotional trend visualisation.}
  \label{fig:ui_wireframes}
\end{figure}
```

---

## 3.9 Technology Stack Selection and Justification

Table 3.4 presents the complete technology stack with justifications for each selection. Technology choices were governed by three constraints: compatibility with the on-device deployment model, integration with the Python machine learning ecosystem, and suitability for real-time processing on consumer Apple Silicon hardware.

```latex
\begin{table}[htbp]
  \centering
  \caption{Technology stack selection with justifications.}
  \label{tab:tech_stack}
  \begin{tabular}{p{3cm}p{4cm}p{7cm}}
    \toprule
    \textbf{Component} & \textbf{Technology} & \textbf{Justification} \\
    \midrule
    Backend framework & FastAPI (Python~3.11) & Native async support; direct access to the Python ML ecosystem (PyTorch, Transformers, scikit-learn); automatic OpenAPI documentation generation \\
    Database & PostgreSQL + pgvector & Combined relational and vector storage eliminates the need for a separate vector database; mature ACID guarantees for activity logs; pgvector supports IVFFlat and HNSW indexing for sub-millisecond ANN search \\
    On-device LLM & Qwen3-4B via MLX & 4-bit quantisation fits within 2.5\,GB GPU budget; MLX exploits Apple Silicon unified memory for zero-copy inference; 37.1\,tok/s throughput enables interactive conversation \\
    Affective computing & SenticNet + SetFit & SenticNet provides interpretable, multi-dimensional affective features grounded in the Hourglass of Emotions; SetFit achieves 86\% F1 with only 210 training sentences via contrastive learning \\
    Sentence encoder & all-mpnet-base-v2 & State-of-the-art sentence embeddings; shared across emotion classification and memory retrieval for representational consistency \\
    Memory & Mem0 & 26\% retrieval relevance improvement over OpenAI memory baseline; graph-based memory organisation captures relational structure between memories \\
    Desktop client & SwiftUI & Native macOS integration; direct access to Accessibility API for screen metadata capture; minimal resource footprint ($\sim$25\,MB RAM) \\
    Dashboard & React + Vite & Component-based architecture suits modular analytics views; Vite provides sub-second hot module replacement during development \\
    \bottomrule
  \end{tabular}
\end{table}
```

FastAPI was selected over alternatives such as Flask and Django due to its native asynchronous request handling, which is essential for managing concurrent screen monitoring events and conversational requests without blocking. Python 3.11 was chosen as the runtime version for its compatibility with the required machine learning packages (Transformers 5.3.0, sentence-transformers 5.2.3, PyTorch 2.10.0, scikit-learn 1.7.2) and its significant performance improvements over earlier Python versions. The LoRA fine-tuning framework \cite{hu2022} was evaluated for potential future model adaptation but was not employed in the current implementation, as the Qwen3-4B base model with prompt engineering proved sufficient for the system's conversational requirements.

---

This concludes the system design and architecture chapter. The three-layer architecture, dual data-flow model, and modular decomposition described herein provide the structural foundation upon which the implementation (Chapter 4) and evaluation (Chapter 5) build. The key architectural contribution is the integration of on-device LLM inference, multi-dimensional affective computing, and adaptive intervention delivery within a privacy-preserving, resource-conscious framework specifically tailored to the executive function challenges characteristic of ADHD.
