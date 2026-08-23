# ClarifyAI Backend

# Confidence-Scored, Source-Verified Question Answering System

ClarifyAI is an AI-powered question-answering system designed to reduce
LLM hallucinations by grounding generated answers in retrieved evidence,
verifying the generated response against that evidence, calculating a
confidence score, and identifying contradictions or discrepancies between
different sources.

The backend contains the core intelligence of the ClarifyAI system.

---

# 1. Problem Statement

Large Language Models can generate fluent and convincing answers that may
contain incorrect, outdated, incomplete, or contradictory information.

A conventional question-answering system generally follows:

    User Question
         ↓
    LLM
         ↓
    Answer

The main problem with this architecture is that the generated answer may
not be sufficiently grounded in reliable evidence.

ClarifyAI introduces an additional verification layer:

    User Question
         ↓
    Query Processing
         ↓
    Evidence Retrieval
         ↓
    Answer Generation
         ↓
    Semantic Verification
         ↓
    Confidence Calculation
         ↓
    Discrepancy Detection
         ↓
    Contradiction Detection
         ↓
    Verified API Response

The objective is not only to generate an answer, but also to provide
evidence about how trustworthy that answer is.

---

# 2. Main Objectives

The backend was designed around the following objectives:

1. Accept natural-language questions from users.
2. Validate and normalize incoming queries.
3. Retrieve relevant external evidence.
4. Generate an answer using the retrieved evidence.
5. Verify the generated answer against the evidence.
6. Calculate a confidence score.
7. Detect conflicting information between different sources.
8. Identify evidence that contradicts the generated answer.
9. Preserve source information for transparency.
10. Protect API endpoints using authentication.
11. Return all verification information through a structured API response.

---

# 3. Complete System Architecture

The current ClarifyAI backend follows this architecture:

```text
                         ┌───────────────────┐
                         │     User Query    │
                         └─────────┬─────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │ Query Normalization &    │
                    │ Validation               │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │    Evidence Retrieval    │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │     Retrieved Evidence   │
                    │  Source + Content +      │
                    │  Relevance + Quality     │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │    Answer Generation     │
                    │          LLM             │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Semantic Verification  │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────┴─────────────┐
                    │                          │
                    ▼                          ▼
          ┌───────────────────┐     ┌────────────────────┐
          │ Confidence        │     │ Answer vs Evidence │
          │ Calculation       │     │ Contradictions     │
          └─────────┬─────────┘     └──────────┬─────────┘
                    │                          │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Cross-Source             │
                    │ Discrepancy Detection    │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      API Response        │
                    │                          │
                    │ Answer                   │
                    │ Confidence               │
                    │ Evidence                 │
                    │ Contradictions           │
                    │ Discrepancies            │
                    └──────────────────────────┘