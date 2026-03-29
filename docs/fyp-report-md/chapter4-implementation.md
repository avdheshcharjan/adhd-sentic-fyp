# Chapter 4: Implementation

This chapter presents the implementation details of the ADHD Second Brain system, a multimodal intelligent assistant designed to support individuals with Attention-Deficit/Hyperactivity Disorder (ADHD) through real-time emotion classification, adaptive interventions, and personalised coaching. The system integrates on-device large language model inference, contrastive learning-based emotion classification, affective computing via SenticNet, semantic memory retrieval, screen monitoring, and explainable just-in-time adaptive interventions (JITAIs). Each subsection describes the architectural decisions, algorithms, and engineering trade-offs that guided the implementation.

---

## 4.1 Development Environment and Tools

### 4.1.1 Hardware and Runtime Environment

All development and experimentation were conducted on a MacBook Pro equipped with an Apple M4 system-on-chip and 16 GB of unified memory. The unified memory architecture of Apple Silicon was a critical constraint that shaped several implementation decisions, particularly the selection of quantised models and load-on-demand strategies discussed in subsequent sections. The development environment was standardised on Python 3.11, as Python 3.14 introduced breaking changes in several core dependencies, most notably in the `transformers` and `scikit-learn` packages. Swift 5.9 was used for the native macOS application layer, and TypeScript was employed for the web dashboard frontend.

### 4.1.2 Core Libraries and Frameworks

The machine learning stack comprised `transformers` 5.3.0, `sentence-transformers` 5.2.3, `torch` 2.10.0, and `scikit-learn` 1.7.2. The `transformers` library served dual purposes: tokenisation for the on-device LLM pipeline and model loading for the DistilBERT fine-tuning experiments. The `sentence-transformers` library provided the pre-trained embedding models used in both the hybrid classifier (Approach A) and the contrastive learning classifier (Approach B). PyTorch 2.10.0 was compiled with Metal Performance Shaders (MPS) backend support, enabling GPU-accelerated training and inference on the Apple M4. For affective computing, the SenticNet client was implemented as a standalone HTTP service with `httpx` for asynchronous API orchestration.

### 4.1.3 Data Infrastructure and Build Automation

PostgreSQL 16 with the `pgvector` extension was deployed via Docker to support the semantic memory system. The `pgvector` extension enabled efficient approximate nearest-neighbour search over high-dimensional embedding vectors, which was essential for the memory retrieval pipeline described in Section 4.5. A `Makefile` was used to standardise all build, test, and evaluation workflows. The commands `make test`, `make bench`, `make eval`, and `make all-eval` encapsulated the full lifecycle from unit testing through benchmark execution to classifier evaluation, ensuring reproducibility across development sessions.

### 4.1.4 Version Control and Dependency Management

The project utilised Git for version control with a structured branching model. Dependency pinning was enforced through a `requirements.txt` file locked to specific versions, a necessity given the incompatibility between `setfit` and `transformers` 5.x, which is discussed in Section 4.9. The Docker Compose configuration defined the PostgreSQL and pgvector services, ensuring that the data layer could be reproduced identically across machines.

---

## 4.2 LLM Inference Pipeline

### 4.2.1 On-Device Model Selection and Quantisation

A central design requirement of the ADHD Second Brain was that all LLM inference should execute locally on-device, both to preserve user privacy given the sensitive nature of ADHD-related data and to eliminate dependency on external API services that introduce latency and cost. The system employs the Qwen3-4B model \cite{yang2025} in a 4-bit quantised configuration, loaded through the MLX framework \cite{hannun2023}, Apple's machine learning library optimised for Apple Silicon. MLX was selected over alternatives such as `llama.cpp` and ONNX Runtime because of its native integration with the Metal compute stack and its first-class support for quantised weight formats on unified memory architectures.

The 4-bit quantisation reduces the model's memory footprint to approximately 2.3 GB of GPU memory, well within the 16 GB unified memory budget of the development machine. This quantisation level was chosen after empirical comparison: 8-bit quantisation consumed approximately 4.5 GB and offered negligible improvement in generation quality for the coaching domain, while 2-bit quantisation produced noticeably degraded output coherence. The model loading procedure follows a load-on-demand pattern wherein the model weights are not resident in memory during idle periods. When a user interaction requires LLM generation, the model is loaded from disk, inference is performed, and the model reference is retained in a weak cache that allows the operating system to reclaim memory under pressure.

```python
# [Code Snippet 4.2: MLX model loading with load-on-demand pattern]
# Source: services/mlx_inference.py
```

### 4.2.2 Dual-Mode Generation: Extended Reasoning vs. Direct Response

The inference pipeline supports two distinct generation modes, selectable per request. The `/think` mode activates extended chain-of-thought reasoning, producing approximately 212 tokens at a throughput of 37.1 tokens per second, with a wall-clock latency of approximately 4.7 seconds. The `/no_think` mode bypasses the reasoning chain and produces direct responses of approximately 77 tokens in 2.0 seconds. The mode selection is governed by the intervention engine (Section 4.7): when the system detects that a user is in a state of high frustration or overwhelm, the `/no_think` mode is preferred to deliver immediate, concise guidance; when the user is in a focused or reflective state, the `/think` mode provides richer, more deliberative coaching.

The throughput of 37.1 tokens per second was measured as the median across 100 inference runs on the M4 chip with no competing GPU workloads. This throughput is sufficient for interactive use, as the typical coaching response of 100–200 tokens completes in under 6 seconds.

### 4.2.3 System Prompt Engineering for ADHD Coaching

The LLM's behaviour is shaped by a carefully engineered system prompt that encodes domain knowledge about ADHD executive function deficits, evidence-based coaching strategies, and tone guidelines. The system prompt instructs the model to use Barkley's five executive function domains — time management, self-organisation, self-restraint, self-motivation, and self-regulation of emotion \cite{barkley2010} — as the conceptual framework for all coaching responses. The prompt further specifies that responses should be concise, actionable, and structured with explicit next steps, reflecting the needs of users who may struggle with working memory and task initiation.

### 4.2.4 Context Injection from Affective Analysis

A critical integration point is the injection of SenticNet analysis results into the LLM prompt. When the emotion classification pipeline (Section 4.3) and the SenticNet pipeline (Section 4.4) produce their respective outputs, these are serialised into a structured context block that is prepended to the user's message in the LLM prompt. This context block includes the predicted emotion category, the confidence score, the SenticNet hourglass dimensions (introspection, temper, attitude, sensitivity), and any detected safety signals. The LLM is thus conditioned on both the semantic content of the user's message and its affective properties, enabling responses that are emotionally attuned rather than purely informational.

```python
# [Code Snippet 4.3: Context injection — SenticNet results formatted into LLM prompt]
# Source: services/mlx_inference.py
```

```
[Screenshot 4.1: Example interaction showing /think mode response with injected emotion context]
```

---

## 4.3 Emotion Classification Pipeline

### 4.3.1 Problem Formulation and Category Taxonomy

The emotion classification task is formulated as a six-class single-label classification problem over the categories: *joyful*, *focused*, *frustrated*, *anxious*, *disengaged*, and *overwhelmed*. This taxonomy was designed specifically for the ADHD context, diverging from standard emotion taxonomies which lack categories relevant to executive function monitoring such as *disengaged* and *overwhelmed*. The *focused* category is particularly important as it represents the target state that the intervention engine seeks to maintain.

### 4.3.2 Approach A: Hybrid Embedding Classifier

The first approach implemented a hybrid architecture combining dense sentence embeddings with affective features from SenticNet. Sentence embeddings were generated using `all-MiniLM-L6-v2`, a lightweight transformer model producing 384-dimensional vectors. These embeddings were concatenated with SenticNet hourglass features (a 4-dimensional vector of introspection, temper, attitude, and sensitivity values) to form a 388-dimensional input vector, which was then classified by a Logistic Regression model trained with L2 regularisation.

The hybrid approach achieved 74% accuracy using embeddings alone and 70% accuracy when the SenticNet features were included. This counterintuitive result — that affective features degraded performance — is attributed to the noise introduced by the SenticNet API on short, informal text. SenticNet's concept-level analysis is optimised for well-formed sentences with clear affective vocabulary, whereas ADHD self-report text often contains fragmented, colloquial expressions that yield unreliable hourglass values. This finding informed the decision to decouple the SenticNet pipeline from the classification pipeline in the production system, using SenticNet outputs only for context injection into the LLM (Section 4.2.4).

```python
# [Code Snippet 4.4: Hybrid classifier — embedding extraction and feature concatenation]
# Source: services/emotion_classifier_hybrid.py
```

### 4.3.3 Approach B: Contrastive Learning Classifier (Production)

The production emotion classifier employs a contrastive learning approach inspired by the SetFit framework, implemented manually rather than through the `setfit` library, which was found to be incompatible with `transformers` 5.x due to a missing `default_logdir` import. The architecture consists of two stages: (1) contrastive fine-tuning of a pre-trained sentence transformer to produce emotion-discriminative embeddings, and (2) classification of the fine-tuned embeddings using a Logistic Regression head.

**Embedding Model.** The base model is `all-mpnet-base-v2`, a 110-million parameter sentence transformer producing 768-dimensional embeddings. This model was selected over `all-MiniLM-L6-v2` (used in Approach A) based on systematic evaluation: the higher-dimensional embeddings from `all-mpnet-base-v2` provided substantially better separation of semantically similar categories (e.g., *anxious* vs. *overwhelmed*) in the contrastive embedding space.

**Loss Function.** The contrastive fine-tuning uses CoSENTLoss, a ranking-based loss function that optimises the cosine similarity ordering between positive and negative pairs rather than enforcing absolute distance thresholds. CoSENTLoss was selected over alternatives including MultipleNegativesRankingLoss and standard contrastive loss after empirical comparison showed a 4-percentage-point improvement in accuracy. The ranking-based formulation is particularly well-suited to emotion classification because it does not require that all instances of a given emotion category cluster at a fixed distance, allowing for the natural within-class variance observed in ADHD self-report text.

**Pair Generation Strategy.** Training pairs are generated exhaustively from the 210-sentence training corpus. For each pair of sentences, if both belong to the same category, a positive pair (label 1) is created; otherwise, a negative pair (label 0) is created. This exhaustive enumeration produces 66,150 pairs, which is 184 times more training signal than the 360 pairs generated by the random sampling approach used in the original SetFit paper. The exhaustive approach was found to be critical: random sampling of 360 pairs yielded only 72% accuracy, while exhaustive pairing achieved 86%.

**Hard Negative Mining.** To address confusion between semantically proximate categories, hard negative pairs are mined for the *anxious*/*overwhelmed* and *frustrated*/*overwhelmed* category boundaries. These pairs are upsampled in the training set so that the contrastive loss assigns higher gradient weight to the most difficult distinctions. Confusion matrix analysis confirmed that these two boundaries accounted for 68% of all misclassifications prior to hard negative mining.

**Training Configuration.** The model is trained for exactly one epoch over the pair corpus, with a batch size of 16 and a learning rate of 2e-5 using the AdamW optimiser. A critical finding was that training for two epochs degraded accuracy from 86% to 84%, indicating overfitting on the small training set. Hyperparameter sweeps over learning rate values (1e-5, 2e-5, 5e-5) showed no sensitivity at the one-epoch configuration, suggesting that the pair corpus provides sufficient gradient signal for convergence within a single pass. Training completes in approximately 22 minutes on the M4 GPU.

```python
# [Code Snippet 4.5: Contrastive pair generation with hard negative mining]
# Source: services/emotion_classifier_setfit.py
```

```python
# [Code Snippet 4.6: CoSENTLoss training loop — single epoch]
# Source: evaluation/accuracy/train_and_eval_setfit.py
```

**Classification Head.** After contrastive fine-tuning, the 768-dimensional embeddings of all 210 training sentences are extracted and used to train a scikit-learn Logistic Regression classifier with L2 regularisation (C=1.0) and the `lbfgs` solver. The two-stage architecture (contrastive fine-tuning followed by linear classification) is the defining characteristic of the SetFit paradigm: the contrastive stage transforms the embedding space so that a simple linear classifier suffices, avoiding the need for full model fine-tuning with labelled data.

**Performance.** The production classifier achieves 86% accuracy on the held-out test set of 50 sentences, with an average prediction confidence of 0.76 (up from 0.33 in Approach A). Per-class F1 scores range from 0.80 (*anxious*) to 0.94 (*joyful*), with *anxious* and *overwhelmed* remaining the most challenging categories.

```latex
\begin{table}[htbp]
  \centering
  \caption{Per-class precision, recall, and F1 scores for the production SetFit classifier}
  \label{tab:perclass_f1}
  \begin{tabular}{lccc}
    \toprule
    \textbf{Category} & \textbf{Precision} & \textbf{Recall} & \textbf{F1} \\
    \midrule
    joyful & — & — & 0.94 \\
    focused & — & — & 0.89 \\
    frustrated & — & — & 0.82 \\
    anxious & — & — & 0.80 \\
    disengaged & — & — & 0.86 \\
    overwhelmed & — & — & 0.80 \\
    \bottomrule
  \end{tabular}
\end{table}
```

### 4.3.4 Approach C: DistilBERT Fine-Tuning

The third approach fine-tuned the DistilBERT model as a standard sequence classification model using cross-entropy loss. On the original 210-sentence training set, this approach achieved only 62% accuracy, confirming that transformer fine-tuning requires substantially more data than contrastive learning for few-shot settings. An augmented training set of 1,200 sentences improved accuracy to 72%.

A further experiment with 30,000 augmented training sentences revealed a critical failure mode: the model achieved 78% accuracy on an internal validation split but only 32% accuracy on the ADHD-specific test set. This severe domain mismatch demonstrated that data augmentation strategies which do not preserve the domain-specific linguistic characteristics of ADHD self-report text can produce models that are confidently wrong. This finding reinforced the decision to use the contrastive learning approach with curated, high-quality original data rather than pursuing data quantity.

```latex
\begin{table}[htbp]
  \centering
  \caption{Accuracy comparison across three classification approaches and data conditions}
  \label{tab:classifier_comparison}
  \begin{tabular}{lcc}
    \toprule
    \textbf{Approach} & \textbf{Training Data} & \textbf{Accuracy} \\
    \midrule
    A: Hybrid (embedding only) & 210 sentences & 74\% \\
    A: Hybrid (+ SenticNet) & 210 sentences & 70\% \\
    B: SetFit/Contrastive & 210 sentences & \textbf{86\%} \\
    C: DistilBERT & 210 sentences & 62\% \\
    C: DistilBERT (augmented) & 1,200 sentences & 72\% \\
    C: DistilBERT (30K external) & 30,000 sentences & 32\% \\
    \bottomrule
  \end{tabular}
\end{table}
```

### 4.3.5 Data Quality Lessons

An additional experiment attempted to expand the training set from 210 to 498 sentences by adding 288 LLM-generated boundary and general sentences. This augmented corpus *regressed* overall accuracy from 86% to 82%, with the *anxious* class F1 score collapsing from 0.80 to 0.62. Post-hoc analysis revealed two causes: (1) the generated sentences introduced class imbalance, with *frustrated* and *overwhelmed* receiving 98 sentences each while *anxious* received only 83, and (2) the generated boundary sentences diluted the distinctive linguistic signal of the *anxious* category by introducing surface-level overlap with *overwhelmed*. The production system therefore uses only the original 210 curated sentences.

---

## 4.4 SenticNet Affective Computing Pipeline

### 4.4.1 Architecture Overview

The SenticNet pipeline \cite{cambria2024} implements a 13-API orchestration layer that extracts affective, semantic, and personality features from user text. The pipeline is organised into a 4-tier processing cascade: (1) Safety Detection, (2) Emotion Analysis, (3) ADHD Signal Extraction, and (4) Personality Profiling. Each tier is executed sequentially, with early termination possible at the Safety tier if crisis-level content is detected.

### 4.4.2 Safety Tier

The Safety tier invokes SenticNet's polarity and concept-level APIs to detect expressions indicative of self-harm, crisis states, or extreme negative affect. When a safety signal is detected, the pipeline immediately returns a structured alert object to the intervention engine (Section 4.7), bypassing the remaining tiers. This early termination design prioritises user safety above all other system objectives.

### 4.4.3 Emotion and Hourglass Tier

The Emotion tier extracts the four hourglass dimensions — *introspection*, *temper*, *attitude*, and *sensitivity* — through a combination of concept decomposition and sentic pattern matching. Each dimension produces a continuous value, which is subsequently discretised into qualitative labels for the LLM context injection described in Section 4.2.4.

### 4.4.4 ADHD Signal Extraction and Personality Profiling

The third tier extracts signals specific to ADHD executive function deficits, including indicators of task-switching frustration, time blindness, and hyperfocus termination difficulty. These signals are derived by mapping SenticNet concept patterns to Barkley's five executive function domains \cite{barkley2010}. The fourth tier constructs a lightweight personality profile using the Big Five dimensions, which is used by the memory system (Section 4.5) for longitudinal user modelling.

### 4.4.5 HTTP Client and Latency Management

The 13 SenticNet API calls are orchestrated using an asynchronous HTTP client with per-call timeout management. Each API call is configured with a 3-second timeout; calls that exceed this threshold are abandoned, and the pipeline proceeds with partial results. The 4-tier cascade architecture enables early termination: if the Safety and Emotion tiers complete successfully, the system can deliver a useful affective analysis even if the ADHD Signal and Personality tiers time out.

```python
# [Code Snippet 4.7: SenticNet 4-tier cascade with timeout management]
# Source: services/senticnet_pipeline.py
```

---

## 4.5 Memory System Implementation

### 4.5.1 Architecture and Storage Layer

The memory system provides longitudinal context tracking through the Mem0 framework \cite{chhikara2025}, which abstracts over a PostgreSQL 16 database with the `pgvector` extension for vector similarity search. Each memory entry consists of a natural-language summary, an associated 768-dimensional embedding vector (generated by the same `all-mpnet-base-v2` model used in the emotion classifier), a timestamp, and metadata tags including the emotion category and session identifier.

### 4.5.2 Store and Retrieve Operations

The store operation is triggered at two points: (1) at the end of each user interaction, a summary of the exchange is generated by the LLM and stored as a new memory entry, and (2) when the emotion classifier detects a transition between emotion categories, a context snapshot is stored to capture the circumstances of the transition. The retrieve operation performs semantic search: given a query embedding, the system returns the top-k most similar memory entries by cosine similarity. Evaluation on a held-out set showed 95% top-1 relevance.

### 4.5.3 Profile Management for Longitudinal Tracking

The memory system maintains a user profile that aggregates emotional patterns, productivity trends, and intervention response history over time. The profile is updated incrementally after each session using exponential moving averages over the hourglass dimensions and emotion category frequencies. This longitudinal profile enables the intervention engine to personalise its timing and content.

```python
# [Code Snippet 4.8: Memory store and retrieve operations with pgvector]
# Source: services/memory_service.py
```

---

## 4.6 Screen Monitoring and Activity Classification

### 4.6.1 Swift ScreenMonitor

The screen monitoring subsystem is implemented as a native Swift component (`ScreenMonitor.swift`) that runs as a background process within the macOS menu bar application. The monitor uses `NSWorkspace` polling at 1-second intervals to capture the currently active application name and window title. For web browsers (Safari, Chrome, Firefox, and Arc), the monitor additionally extracts the current URL using AppleScript inter-process communication.

### 4.6.2 TransitionDetector

The `TransitionDetector` module processes the stream of application-title-URL tuples to identify context switches. A context switch is defined as a change in the active application that persists for more than 2 seconds (to filter out momentary command-tab transitions). Detected transitions are timestamped and forwarded to the intervention engine, which uses transition frequency as a signal for attentional instability.

### 4.6.3 Four-Layer Activity Classifier

Each screen observation is classified into a productivity category (*productive*, *neutral*, *distracting*) using a four-layer cascade classifier. **Layer 1 (L1)** performs exact matching on the application name against a curated dictionary, resolving 56.5% of observations. **Layer 2 (L2)** performs URL-based matching for browser activities. **Layer 3 (L3)** applies keyword matching on the window title, resolving an additional 21.5% of observations. **Layer 4 (L4)** uses embedding-based semantic classification for the remaining 22.0% of observations. The cascade architecture achieves a batch throughput of 549 titles per second.

```swift
// [Code Snippet 4.9: NSWorkspace polling and AppleScript URL extraction]
// Source: swift-app/ADHDSecondBrain/ScreenMonitor.swift
```

---

## 4.7 Intervention Engine

### 4.7.1 JITAI Framework and Executive Function Mapping

The intervention engine implements the Just-in-Time Adaptive Intervention (JITAI) paradigm, which delivers support precisely when an individual is most receptive and in need. The engine maps each detected state — comprising the emotion classification, SenticNet hourglass values, transition frequency, and productivity classification — to one or more of Barkley's five executive function (EF) domains \cite{barkley2010}: time management, self-organisation, self-restraint, self-motivation, and self-regulation of emotion.

### 4.7.2 Thompson Sampling for Intervention Timing

The system addresses the challenge of optimal intervention timing through Thompson Sampling, a Bayesian bandit algorithm that maintains a Beta distribution over the success probability for each intervention timing option. After each intervention, the user's subsequent emotional trajectory is used to update the Beta parameters, gradually learning the timing preferences of the individual user.

### 4.7.3 Multi-Tier Intervention Escalation

Interventions are delivered through a four-tier escalation system of increasing intrusiveness: (1) **nudge** — a subtle visual indicator in the menu bar icon, (2) **popup** — a brief notification with a coaching suggestion, (3) **overlay** — a semi-transparent screen overlay with a structured task re-engagement prompt, and (4) **block** — a full-screen intervention for crisis-level states.

### 4.7.4 Explainable AI Integration

Each intervention is accompanied by an explanation generated through two XAI mechanisms. First, a Concept Bottleneck Model \cite{koh2020} extracts human-interpretable intermediate features that justify the intervention. Second, counterfactual explanations describe what the user could change to avoid future interventions. These explanations are designed to build user trust and promote self-awareness, both of which are therapeutic objectives in ADHD management.

```python
# [Code Snippet 4.10: Thompson Sampling update for intervention timing]
# Source: services/jitai_engine.py
```

```python
# [Code Snippet 4.11: Concept Bottleneck feature extraction and counterfactual generation]
# Source: services/xai_explainer.py
```

---

## 4.8 macOS Application and Web Dashboard

### 4.8.1 SwiftUI Menu Bar Application

The native macOS interface is implemented as a SwiftUI menu bar application that provides persistent, unobtrusive access to the ADHD Second Brain. The application resides in the system menu bar and presents a dropdown panel containing the current emotional state, a quick-entry text field for journaling, and controls for intervention preferences. The menu bar paradigm was selected because it occupies minimal screen real estate and does not compete for the user's attentional resources.

The application communicates with the Python backend via a local FastAPI server. All API calls are made over `localhost` to ensure that no user data leaves the device. The Swift networking layer uses `URLSession` with JSON serialisation, and all calls are dispatched asynchronously to prevent UI thread blocking.

### 4.8.2 React Web Dashboard

The web dashboard, implemented in React with TypeScript, provides a richer analytical interface for users who wish to review their emotional and productivity patterns over time. The dashboard comprises three primary views: (1) an **emotion timeline** that visualises the sequence of classified emotions over a session or day, (2) a **productivity metrics** panel that aggregates screen monitoring data into daily and weekly summaries with trend lines, and (3) a **memory explorer** that allows users to search and browse their stored memories using natural-language queries.

```
[Screenshot 4.5: React dashboard — emotion timeline view with daily productivity summary]
[Screenshot 4.6: SwiftUI menu bar application — dropdown panel with emotion state and quick-entry field]
```

---

## 4.9 Implementation Challenges and Solutions

### 4.9.1 SetFit Library Incompatibility

The `setfit` library was found to be incompatible with `transformers` 5.x due to an internal dependency on the `default_logdir` function, which was removed in the 5.x release. Rather than downgrading the `transformers` library — which would have introduced cascading incompatibilities with the MLX inference pipeline — the contrastive learning training loop was reimplemented manually using the `sentence-transformers` library's loss functions and the PyTorch training API. This manual implementation provided greater control over the pair generation and hard negative mining strategies, ultimately contributing to the 86% accuracy achieved by the production classifier.

### 4.9.2 LLM-Generated Training Data Degradation

Expanding the training corpus from 210 to 498 sentences using LLM-generated data caused a regression from 86% to 82% accuracy, with a particularly severe collapse in the *anxious* class. The root cause was twofold: class imbalance in the generated data and semantic dilution of category boundaries. The solution was to abandon data augmentation entirely for the contrastive learning approach and to rely on the exhaustive pair generation strategy (66,150 pairs from 210 sentences) to extract maximum training signal from the curated corpus.

### 4.9.3 SenticNet API Latency

The 13 SenticNet API calls introduced significant latency when executed sequentially. The solution was the 4-tier cascade architecture with asynchronous execution and per-call timeouts, as described in Section 4.4.5. Additionally, a local caching layer was implemented: SenticNet results for previously analysed concepts are stored in an in-memory LRU cache with a 1-hour TTL, reducing redundant API calls for users who revisit similar topics within a session.

### 4.9.4 Memory Constraints on 16 GB Unified Memory

Running the Qwen3-4B model (2.3 GB), the sentence transformer (420 MB), and PostgreSQL simultaneously on 16 GB of unified memory required careful resource management. The load-on-demand strategy described in Section 4.2.1 was the primary mitigation: the LLM is loaded only when generation is required and released after an idle timeout. Peak GPU memory usage was measured at less than 2.5 GB, leaving sufficient headroom for the operating system and other applications.

### 4.9.5 Python Version Incompatibility

Python 3.14, which was the default `python3` on the development machine, introduced breaking changes in several dependencies, including modifications to the `importlib` module that caused `scikit-learn` 1.7.2 to fail during model serialisation. The solution was to pin all project execution to Python 3.11, enforced through the Makefile and a `.python-version` file.

```latex
\begin{table}[htbp]
  \centering
  \caption{Summary of implementation challenges, root causes, and solutions}
  \label{tab:challenges}
  \begin{tabular}{p{3.5cm}p{4cm}p{5.5cm}}
    \toprule
    \textbf{Challenge} & \textbf{Root Cause} & \textbf{Solution} \\
    \midrule
    SetFit library failure & Missing \texttt{default\_logdir} in transformers 5.x & Manual contrastive learning implementation \\
    LLM data degradation & Class imbalance + semantic dilution & Use only 210 curated sentences \\
    SenticNet latency & 13 sequential API calls & 4-tier cascade + async + caching \\
    Memory constraints & 16 GB shared across all components & Load-on-demand LLM, $<$2.5 GB peak \\
    Python 3.14 breakage & importlib changes in 3.14 & Pin to Python 3.11 \\
    \bottomrule
  \end{tabular}
\end{table}
```
