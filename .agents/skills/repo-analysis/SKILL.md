---
name: repo-analysis
description: "Analyze repositories and codebases as layered repo analysis: build a conceptual mental model, map concepts to implementation, enumerate major classes with attributes and methods, show class containment/composition/dependency graphs, and trace function-call pipelines/call graphs. Use when Codex needs to understand, explain, onboard into, or document repo architecture."
---

# Repo Analysis

## Overview

Use repo analysis to understand a codebase in layers. Start from the conceptual mental model, then explain how the repo implements that idea, and always show both the class model and the function-call pipeline that make the idea executable.

## Workflow

1. Ground in the repo first. Read local instructions, docs, manifests, entrypoints, source directories, and tests. Prefer `rg` and `rg --files`. Respect project tool rules before running commands.
2. Build the Concept Layer. State what the repo is for in one clear paragraph. Identify the domain nouns, core abstractions, inputs, outputs, invariants, and user or system goals. Do not start with a file inventory before explaining the idea.
3. Build the Class Model. Enumerate the major classes, their attributes, their behaviors or methods, and the relationships between them. Always distinguish containment, production, dependency, and inheritance.
4. Build the Implementation Layer. Map each concept in the mental model to real code. For OOP code, explain how classes implement concepts. For functional code, describe the pipeline and transformations between stages. For mixed paradigms, explain both without forcing the repo into one style.
5. Build the Function Pipeline. Trace the main entrypoints into concrete function calls. Include the top-level pipeline and any important sub-pipelines.
6. Build the Interaction Layer. Explain data flow, control flow, configuration flow, ownership boundaries, class relationships, and side effects.
7. Tie every technical detail back to the mental model. Code facts matter because they implement the original idea. Avoid isolated symbol lists unless they clarify the concept-to-code mapping.

## Analysis Details

Use concrete file and symbol references for claims. Include compact diagrams, Mermaid diagrams, or labeled text graphs when the output medium supports them.

For the class model, capture:

- Purpose in the conceptual model.
- Important attributes and what they represent.
- Important methods and their behaviors.
- Relationships to other classes, with explicit labels:
  - `contains/owns`: fields, properties, instance state, result containers, collections, or objects held for the object's lifetime.
  - `produces`: factory functions, parser functions, scheduler methods, or methods that return instances without owning them.
  - `depends on`: constructor args, method args, imported collaborators used for behavior, or short-lived local objects.
  - `inherits`: superclass or protocol relationships.
- A class containment/composition graph. Do not treat a plain import as `contains/owns`.
- A separate runtime data container graph when result/data classes carry other domain objects.

For functions and pipelines, capture:

- Main entrypoints and the call chain they start.
- Inputs and outputs at each stage.
- Transformations performed by each step.
- Which functions call which functions.
- Important sub-pipelines, such as parsing, synthesis, processing, detection, tracking, rendering, persistence, or request handling.
- Where side effects happen, such as file I/O, network I/O, plotting, logging, or mutation.
- A function-call pipeline or call graph. Prefer arrows like `entrypoint -> parse -> build -> execute -> result`, with branching where it matters.

For architecture, capture:

- Entry points and main workflows.
- Configuration and dependency flow.
- Tests as behavioral documentation.
- Boundaries between domain logic, adapters, scripts, UI, and infrastructure.

## Output Shape

Return a structured report with these sections unless the user explicitly asks for another shape:

1. Mental Model: explain the repo conceptually in plain language.
2. Class Model And Containment: list major classes with attributes and behaviors, then show class containment/composition/dependency relationships as a graph.
3. Implementation Map: map concepts to modules, classes, functions, and pipelines.
4. Function Pipeline And Call Graph: show the top-level function pipeline and key sub-pipelines from entrypoints through outputs.
5. How to Read This Repo: suggest an efficient reading order.
6. Uncertainties: list gaps, assumptions, or places where the code and docs disagree.

The class graph and function pipeline are mandatory for normal repository analysis. Keep the report layered. The user wants an understanding path from idea to implementation, not just a directory tour.

## Behavior Rules

- Prefer discovering repo truth from files over guessing.
- Keep explanations concise but concrete.
- Mention uncertainty when evidence is missing.
- Do not mutate files unless the user explicitly asks for implementation or edits.
- When analyzing Python in this repo, use `uv run` for execution, following the project environment rule.
