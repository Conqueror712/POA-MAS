# Title and Abstract

## Title

**ORCA: Organizational Reuse of Coordination Assets for Multi-Agent LLM Systems**

## Abstract

Multi-agent LLM systems often develop useful coordination patterns during execution, including role specialization, repair procedures, and handoff conventions. Yet these patterns are typically discarded after a run or reused as unstructured context. We ask whether emergent coordination can instead be converted into persistent, typed assets and reused selectively on later tasks. We present ORCA, a lightweight framework that logs multi-agent trajectories, extracts role-level and organization-level coordination assets, and reuses them through prompt guidance, asset-based routing, or both. On APPS-derived code-repair tasks, prompt-level assets improve shifted-split success from 68.9% to 82.2% and reduce empty or missing patch failures from 13/45 to 4/45 attempts. In contrast, full reuse underperforms free self-organization, indicating that organizational memory is not monotonically beneficial. A second study in repeated social dilemmas shows that reusable strategy assets produce more stable cooperation and social welfare than persona prompts alone, especially in Public Goods games. Overall, ORCA supports a structured view of multi-agent memory: coordination patterns can transfer across tasks, but they should be decomposed into typed assets and reused selectively rather than replayed wholesale.
