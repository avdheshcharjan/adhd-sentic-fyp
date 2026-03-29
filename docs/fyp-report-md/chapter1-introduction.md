# Chapter 1: Introduction

---

## 1.1 Background and Motivation (~2 pages)

### Paragraph 1: ADHD Prevalence and Adult Impact

Open with the clinical reality of ADHD as a persistent neurodevelopmental disorder that extends well beyond childhood. Present the epidemiological data from \cite{song2021}, the most comprehensive global meta-analysis, establishing that ADHD affects between 2.58% of the adult population (persistent, fully symptomatic cases) and 6.76% (symptomatic remitters who retain clinically significant impairment) \cite{faraone2021}. Translate these percentages into absolute numbers — conservatively, over 200 million adults worldwide live with some form of ADHD symptomatology. Note that these figures likely underrepresent actual prevalence due to historic underdiagnosis in women, non-Western populations, and adults who were never assessed in childhood. Establish that ADHD is not a disorder of attention per se, but of executive function — the suite of top-down cognitive processes including working memory, inhibitory control, and cognitive flexibility that enable goal-directed behaviour \cite{diamond2013}. This framing is critical because it shifts the intervention target from "paying attention" to supporting the executive function infrastructure that ADHD impairs.

### Paragraph 2: Economic and Occupational Burden

Transition from clinical prevalence to real-world economic impact. Present the finding from \cite{barkley2010} that ADHD imposes an estimated cost of \$4,336 per affected worker per year in lost productivity, arising from increased absenteeism, task-switching overhead, missed deadlines, and difficulty sustaining effort on non-preferred tasks. Extrapolate this to the knowledge economy, where workers are expected to self-regulate across unstructured digital environments with minimal external scaffolding — precisely the conditions under which ADHD-related executive dysfunction is most debilitating. Argue that this productivity cost is not immutable; it represents a design failure in the tools knowledge workers use, not an inherent limitation of individuals with ADHD. Effective environmental and technological accommodations can substantially narrow this gap, yet the current landscape of productivity software is designed for neurotypical executive function profiles.

### Paragraph 3: The Digital Distraction Paradox

Address the bidirectional relationship between ADHD and digital technology. Cite \cite{thorell2022}, whose systematic review established that individuals with ADHD engage in significantly more problematic digital media use, while \cite{dontre2021} demonstrated that digital technology actively disrupts academic and occupational performance through notification-driven context switching. Present this as a paradox: the desktop computer is simultaneously the primary workspace for knowledge workers and the primary vector for ADHD-exacerbating distractions. Current approaches to this problem — website blockers, focus timers, "digital wellbeing" features — treat symptoms rather than causes. They impose rigid, one-size-fits-all restrictions that fail to account for the fluctuating attentional states characteristic of ADHD, where the same individual may be hyperfocused and highly productive in one hour and entirely disengaged the next. What is needed is an adaptive system that understands the user's current cognitive-affective state and responds accordingly.

### Paragraph 4: Emotion Dysregulation as the Fourth Core Symptom

Introduce the emerging clinical consensus that emotion dysregulation (ED) should be considered a fourth core symptom of ADHD alongside inattention, hyperactivity, and impulsivity. Cite \cite{beattie2025}, who argued on the basis of neurobiological, phenomenological, and functional evidence that ED is not merely comorbid with ADHD but intrinsic to it. This has direct implications for productivity tools: an application that monitors only behavioural signals (e.g., time on task, application usage) while ignoring affective state is missing a fundamental dimension of the ADHD experience. Frustration, anxiety, and emotional overwhelm are not peripheral inconveniences — they are primary drivers of task abandonment, avoidance, and the doom-scrolling cycles that destroy productivity. Any comprehensive ADHD support system must therefore incorporate affective awareness, detecting emotional states and responding with appropriate interventions before dysregulation escalates.

### Paragraph 5: The Efficacy Gap — Evidence for Digital Interventions

Establish that digital mental health interventions have demonstrated measurable efficacy for related conditions, but that the ADHD-specific evidence base remains thin. Cite the meta-analytic evidence from \cite{garciaperal2025}, an umbrella review encompassing 26 systematic reviews and 34,442 participants, which found a statistically significant but small overall effect (Hedges' g = −0.32) for digital interventions targeting mental health conditions. This effect size, while modest, is clinically meaningful at population scale. Point to \cite{fitzpatrick2017}, whose randomised controlled trial of the conversational agent Woebot found significant reductions in depression symptoms (F = 6.47, P = .01) over just two weeks, demonstrating that AI-driven conversational interventions can produce rapid therapeutic effects. However, note the critical gap: \cite{woods2024} found that Brain.fm remains the only ADHD-specific application with peer-reviewed evidence of efficacy, and its scope is limited to auditory entrainment for focus enhancement. No existing application combines the breadth of support — coaching, emotional awareness, behavioural monitoring, and adaptive memory — that the ADHD executive function profile demands.

### Paragraph 6: The Second Brain Paradigm and ADHD

Introduce the "Second Brain" concept from \cite{forte2022} — the practice of building a personal knowledge management system that offloads cognitive burden from biological memory to external, searchable, interconnected digital storage. Argue that this paradigm is especially relevant for ADHD, where working memory deficits mean that insights, commitments, and contextual knowledge are routinely lost. However, existing Second Brain tools (Notion, Obsidian, Roam Research) require substantial executive function to maintain — precisely the resource that ADHD depletes. The vision of the present project is an AI-powered Second Brain that actively manages itself: capturing context automatically, surfacing relevant memories proactively, and adapting its behaviour to the user's current emotional and attentional state. This requires not a cloud-hosted general-purpose assistant, but a privacy-preserving, on-device AI system that operates within the user's desktop environment with minimal cognitive overhead.

### Paragraph 7: The Privacy Imperative and On-Device AI

Conclude the motivation section by addressing why on-device processing is not merely a technical preference but an ethical necessity. An application that monitors screen content, classifies emotional states from journal text, and maintains a longitudinal memory of the user's cognitive patterns handles extraordinarily sensitive data. Transmitting this to cloud servers would create unacceptable privacy risks and violate the trust required for therapeutic applications. Recent advances in edge AI make on-device processing feasible: Apple's MLX framework \cite{hannun2023} enables efficient neural network inference on Apple Silicon, while parameter-efficient models like Qwen3-4B \cite{yang2025} deliver capable language generation within the memory constraints of consumer hardware. The convergence of these technologies — efficient edge inference, compact language models, and privacy-preserving architectures — creates a window of opportunity to build what was previously impossible: a comprehensive, intelligent, on-device ADHD support system.

---

## 1.2 Problem Statement (~0.5 page)

### Paragraph 1: The Fragmentation Problem

State the core problem directly: adults with ADHD who work primarily on desktop computers currently lack a unified, privacy-preserving tool that addresses the interconnected challenges of executive dysfunction, emotion dysregulation, and knowledge management. To approximate the functionality required, an individual must cobble together three to five separate applications — a focus timer, a website blocker, a journaling app, a task manager, and perhaps a conversational AI tool — each with its own interface, data silo, and cognitive overhead. This fragmentation is itself an ADHD tax: the executive function required to configure, maintain, and switch between multiple tools actively exacerbates the condition these tools purport to help. Furthermore, none of these individual tools incorporate affective awareness; they operate on fixed rules rather than adapting to the user's fluctuating cognitive-emotional state.

### Paragraph 2: The Technical Gap

Articulate the problem in technical terms. No existing application integrates on-device large language model inference, real-time affective computing, automated screen activity classification, and persistent personalised memory within a single desktop application. Existing ADHD applications are overwhelmingly mobile-first, ignoring the desktop environment where knowledge work actually occurs. Those that do operate on desktop are either narrow in scope (e.g., website blockers) or require cloud connectivity that compromises privacy. The technical challenge is substantial: running a language model, an emotion classifier, a screen monitoring pipeline, and a vector memory system concurrently on consumer hardware, within acceptable energy and memory budgets, while maintaining responsive user interaction. This project addresses that challenge.

---

## 1.3 Project Objectives (~1 page)

### Introductory Paragraph

State that the project defined five specific, measurable objectives aligned with the identified gaps. Each objective maps to a distinct technical subsystem and is evaluated against quantitative performance criteria established through benchmarking.

### Objective 1: On-Device Conversational ADHD Coach

Develop an on-device conversational coaching system powered by a locally-running large language model capable of ADHD-specific guidance, including task decomposition, time estimation support, emotional validation, and accountability check-ins. The target throughput was a minimum of 30 tokens per second to ensure conversational fluency, with peak AI memory consumption under 3 GB to remain viable on consumer MacBook hardware (16 GB RAM). The system was implemented using Qwen3-4B \cite{yang2025} running on Apple's MLX framework \cite{hannun2023}, achieving 37.1 tokens per second throughput with peak memory usage below 2.5 GB on a MacBook Pro M4.

### Objective 2: Real-Time Emotion Classification from Text

Design and train an emotion classifier that maps natural language input (journal entries, chat messages) to six ADHD-specific affective categories — joyful, focused, frustrated, anxious, disengaged, and overwhelmed — enabling the system to adapt its interventions to the user's current emotional state. These categories were derived from clinical ADHD literature on emotion dysregulation \cite{beattie2025} rather than from general-purpose emotion taxonomies (e.g., Ekman's six basic emotions), which lack the granularity needed for ADHD-relevant states such as "overwhelmed" and "disengaged." The classifier was implemented using a manual SetFit-style contrastive learning approach \cite{reimers2019} and achieved 86% accuracy on a held-out test set using only 210 curated training sentences, with integration into a broader affective computing pipeline leveraging SenticNet's 13-API framework \cite{cambria2024} for multi-dimensional sentiment analysis.

### Objective 3: Intelligent Screen Activity Classification

Build an automated screen activity monitoring and classification system that categorises application usage into productive, neutral, and distracting categories without requiring manual configuration or cloud connectivity. The target was real-time classification at desktop-interaction speed with high rule-based coverage to minimise reliance on computationally expensive LLM inference. The system achieved a classification throughput of 549 titles per second with 78% rule-based coverage, falling back to on-device LLM classification only for ambiguous cases.

### Objective 4: Persistent Personalised Memory System

Implement a long-term memory system that retains user preferences, past interactions, emotional patterns, and contextual knowledge across sessions, enabling the AI coach to provide personalised, context-aware responses that improve over time. The system was built on Mem0 \cite{chhikara2025} with pgvector for vector similarity search, achieving 95% top-1 relevance on retrieval benchmarks — consistent with the 26% improvement over baseline memory systems reported in the Mem0 literature.

### Objective 5: Privacy-Preserving, Energy-Efficient Architecture

Ensure that the entire system operates fully on-device with no cloud dependencies for core AI functionality, within energy and memory budgets acceptable for sustained daily use on consumer hardware. The measured energy cost was 21,314 mJ per LLM inference, translating to approximately 1.4% battery consumption per hour of active use — well within the threshold for an always-on background application. Peak AI memory was held below 2.5 GB, leaving ample headroom for the user's primary work applications on a 16 GB MacBook Pro M4.

```latex
\begin{table}[h]
\centering
\caption{Summary of Project Objectives and Achieved Metrics}
\label{tab:objectives}
\begin{tabular}{p{4cm}p{3.5cm}p{3.5cm}}
\hline
\textbf{Objective} & \textbf{Target} & \textbf{Achieved} \\
\hline
LLM throughput & $\geq$30 tok/s & 37.1 tok/s \\
Emotion classification accuracy & $\geq$80\% & 86\% \\
Screen classification throughput & Real-time & 549 titles/s \\
Memory retrieval relevance & $\geq$90\% top-1 & 95\% top-1 \\
Energy consumption & $<$2\% battery/hr & $\sim$1.4\% battery/hr \\
Peak AI memory & $<$3 GB & $<$2.5 GB \\
\hline
\end{tabular}
\end{table}
```

---

## 1.4 Project Scope and Limitations (~0.5 page)

### Paragraph 1: In-Scope

Define the explicit boundaries of the project. The system was developed as a native macOS application targeting Apple Silicon MacBooks (M-series processors) with a minimum of 16 GB RAM. The AI pipeline operates entirely on-device; the only network connectivity required is for optional features such as Google Calendar integration and initial model downloads. The application encompasses five core modules: (1) a conversational AI coach, (2) a text-based emotion classifier, (3) an automated screen activity monitor, (4) a persistent memory system, and (5) an adaptive intervention engine that orchestrates the other modules. The evaluation was conducted through a combination of automated benchmarks (200+ tests, reproducible two-run protocol) and a structured market analysis of 9 existing ADHD applications identifying 8 distinct market gaps.

### Paragraph 2: Out-of-Scope and Limitations

State limitations explicitly. The system does not incorporate multimodal emotion detection (e.g., facial expression, voice tone, physiological signals); emotion classification relies solely on text input. The application was not evaluated through a clinical trial or longitudinal user study — such evaluation, while essential for deployment, exceeds the scope of an individual final-year project. The system is macOS-exclusive due to its reliance on Apple MLX \cite{hannun2023} for on-device inference; cross-platform portability was not a design goal. The LLM component (Qwen3-4B) is a general-purpose language model fine-tuned via prompt engineering rather than parameter-level adaptation (e.g., LoRA \cite{hu2022}); domain-specific fine-tuning represents a natural extension for future work. Finally, the emotion classifier was trained on curated synthetic data rather than clinical ADHD populations, which may limit generalisability to diverse linguistic and cultural contexts.

---

## 1.5 Contributions and Significance (~1 page)

### Paragraph 1: Primary Contribution — An Integrated On-Device ADHD Support Architecture

State the central contribution: the design, implementation, and evaluation of the first integrated desktop application that combines on-device language model inference, real-time affective computing, automated screen monitoring, and persistent personalised memory for ADHD productivity support. This is not merely an aggregation of existing tools; the system's value lies in the orchestration layer that enables these components to inform each other — emotion state modulates coaching tone, screen activity patterns trigger proactive interventions, and accumulated memory enables personalisation that improves across sessions. The architecture demonstrates that a comprehensive AI-powered wellness application can operate entirely on consumer hardware (MacBook Pro M4, 16 GB) with peak memory under 2.5 GB and energy costs of approximately 1.4% battery per hour, establishing a reference point for future on-device AI applications in mental health \cite{lin2025}.

### Paragraph 2: Technical Contributions

Enumerate specific technical contributions. First, a novel 4-tier SenticNet orchestration pipeline \cite{cambria2024} that integrates 13 affective computing APIs into a coherent sentiment analysis framework, demonstrating how symbolic and neural approaches to sentiment analysis can be combined for domain-specific affective computing. Second, a few-shot emotion classification approach achieving 86% accuracy across 6 ADHD-specific categories using only 210 training sentences via contrastive learning on sentence embeddings \cite{reimers2019}, establishing that curated small-data approaches can outperform bulk-data fine-tuning for specialised affective domains. Third, an adaptive screen classification system achieving 549 titles per second with 78% rule-based coverage, demonstrating a practical hybrid architecture where deterministic rules handle common cases and on-device LLM inference handles the long tail. Fourth, a memory-augmented conversational architecture built on Mem0 \cite{chhikara2025} achieving 95% top-1 retrieval relevance, demonstrating practical integration of vector-based episodic memory with on-device language model generation.

### Paragraph 3: Market and Domain Significance

Frame the contribution within the ADHD assistive technology landscape. A systematic analysis of 9 existing ADHD applications revealed 8 distinct market gaps, the most critical being the absence of any desktop-first solution integrating emotional awareness with productivity support. The project addresses a population — desktop-based knowledge workers with ADHD — that is simultaneously high-need and underserved by the mobile-first orientation of current ADHD technology. By demonstrating feasibility with concrete performance metrics, the project lowers the barrier for future research and development in on-device ADHD support, providing an open reference architecture and reproducible benchmarking methodology (200+ automated tests, two-run protocol) that other researchers can build upon.

### Paragraph 4: Broader Implications for Edge AI in Mental Health

Position the work within the broader trajectory of edge AI for mental health applications. The privacy-preserving architecture is not merely a technical convenience; it addresses a fundamental barrier to adoption of AI-powered mental health tools, particularly among neurodivergent populations who may be disproportionately concerned about surveillance and data misuse. The demonstrated performance envelope — 37.1 tok/s LLM throughput, <2.5 GB memory, 1.4% battery/hour — provides empirical evidence that the "on-device AI" paradigm \cite{lin2025} has matured sufficiently for always-on, resource-intensive applications beyond simple classification tasks. This has implications well beyond ADHD, suggesting a viable path for on-device AI assistants targeting anxiety management, autism support, and other conditions where continuous, context-aware, privacy-preserving support is clinically valuable.

```latex
\begin{figure}[h]
\centering
% \includegraphics[width=\textwidth]{figures/market_gap_analysis.png}
\caption{Market gap analysis of 9 existing ADHD applications across 8 feature dimensions. Shaded cells indicate features present in each application. No existing application addresses more than 3 of the 8 identified gaps.}
\label{fig:market_gaps}
\end{figure}
```

---

## 1.6 Report Organization (~0.5 page)

### Single Paragraph: Chapter-by-Chapter Guide

Provide a concise roadmap of the remaining chapters. Chapter 2 (Literature Review) surveys the clinical ADHD literature, examines existing digital ADHD interventions, and reviews the technical foundations — edge AI inference, affective computing with SenticNet \cite{cambria2024}, contrastive learning for few-shot classification, and memory-augmented generation — that underpin the system design. Chapter 3 (System Design and Architecture) presents the system architecture, detailing the design of each subsystem (conversational coach, emotion classifier, screen monitor, memory system, and orchestration layer), the technology choices (MLX \cite{hannun2023}, Qwen3-4B \cite{yang2025}, Mem0 \cite{chhikara2025}, Sentence-BERT \cite{reimers2019}), and the evaluation framework including the two-run benchmarking protocol. Chapter 4 (Implementation) describes the engineering of the macOS application, covering the SwiftUI front-end, the Python AI backend, the 4-tier SenticNet pipeline, the SetFit-style classifier training process, and the pgvector-backed memory architecture. Chapter 5 (Testing and Evaluation) presents quantitative results across all subsystems — 86% emotion classification accuracy, 37.1 tok/s LLM throughput, 549 titles/s screen classification, 95% memory relevance, 21,314 mJ per inference — alongside the market gap analysis and automated test results. Chapter 6 (Conclusion and Future Work) summarises contributions, discusses limitations, and outlines future directions including clinical user studies, LoRA-based domain fine-tuning \cite{hu2022}, multimodal emotion detection, and Concept Bottleneck Model integration for interpretable classification \cite{koh2020}.

---

*End of Chapter 1 Outline*
