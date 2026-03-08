# XAI Framework — Explainability Design Document

> Concept Bottleneck architecture for transparent, human-readable ADHD intervention explanations.

---

## Overview

The XAI (Explainable AI) framework ensures every intervention is accompanied by a transparent justification. Users should never wonder "why is this app telling me to take a break?" The system explains the **what**, **why**, and **how** of every decision.

---

## Architecture: Concept Bottleneck Model

```
Raw Screen Data         SenticNet Concept Layer        Decision Layer         Explanation
────────────────   →   ──────────────────────   →   ───────────────   →   ──────────────
• App switches         • Emotion: frustration        • Rule matched:        • WHAT: "15 switches"
• Focus time           • Intensity: 82/100             distraction_spiral   • WHY: "frustration detected"
• Distraction %        • Engagement: -45/100         • EF domain:           • HOW: "2-min reset helps"
• Streak time          • Concepts: [deadline,          self_restraint       
                         overwhelm]                                        
```

The **concept layer** (SenticNet outputs) acts as a bottleneck — all decisions pass through interpretable concepts rather than opaque neural network activations. This makes the system inherently explainable.

---

## Three Explanation Types

### 1. WHAT — Observational (Data-driven)

Describes what the system observed. Uses concrete numbers from metrics.

| Intervention Type | Template |
|-------------------|----------|
| Distraction spiral | "You've switched apps {rate} times in the last 5 minutes, with {ratio}% of time on non-work apps." |
| Sustained disengagement | "You've been away from focused work for {streak} minutes." |
| Hyperfocus check | "You've been on the same task for {hours} hours." |
| Emotional escalation | "Your recent activity patterns suggest emotional intensity is rising." |

### 2. WHY — Causal (SenticNet-driven)

Explains why the system believes intervention is needed. References SenticNet emotional analysis.

**With SenticNet data**:
> "Emotional analysis detected {emotion} (intensity: {score}/100). This maps to executive function challenges with focus and task initiation."

**Without SenticNet data**:
> "This pattern is common in ADHD and relates to executive function differences."

### 3. HOW — Counterfactual (Evidence-based)

Suggests what would improve the situation. Based on research evidence, not opinion.

| Intervention Type | Counterfactual |
|-------------------|---------------|
| Distraction spiral | "Research shows a 2-minute breathing reset can reduce context switching by ~40%." |
| Sustained disengagement | "Starting with a 5-minute micro-task often breaks the avoidance cycle." |
| Hyperfocus check | "Time-boxing the remaining work can preserve your focus while protecting other priorities." |
| Emotional escalation | "Acknowledging the emotion (even briefly) helps regulate the prefrontal cortex response." |

---

## Concept Traversal (Knowledge Graph)

SenticNet's concept parsing extracts semantic concepts that can be traversed:

```
"frustrated with deadline"
    → concept: frustration
        → EF domain: self-regulation of emotion
            → intervention: emotional_escalation
                → explanation references frustration + EF deficit
```

This creates an auditable chain from raw input to intervention.

---

## SHAP Validation

For the FYP report, SHAP (SHapley Additive exPlanations) can be used to validate that the concept bottleneck captures the most important features:

1. Collect intervention decisions + feature values
2. Compute SHAP values for each feature
3. Verify that SenticNet concepts align with SHAP feature importance
4. Document in FYP report results chapter

---

## ADHD-Friendly Communication Rules

All explanations must follow these constraints:

| Rule | Reason |
|------|--------|
| Max 2–3 sentences | Working memory deficits |
| Validate before suggesting | RSD (Rejection Sensitive Dysphoria) |
| No guilt/shame framing | Emotional dysregulation sensitivity |
| Upward framing only | "What WILL help" not "what went WRONG" |
| Concrete actions | Executive function needs specificity |
| Include "why" | ADHD brains need to understand the reason |
