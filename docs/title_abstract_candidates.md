# Title and Abstract

## Title

**ORCA: Organizational Reuse of Coordination Assets for Multi-Agent LLM Systems**

## Abstract

Multi-agent LLM systems often produce useful coordination patterns during execution, including role specialization, repair procedures, and handoff conventions. Yet these patterns are typically discarded after a run or reused as undifferentiated context. We ask whether coordination patterns from successful runs can be heuristically distilled into persistent, typed assets and reused selectively on later tasks. We present ORCA, a lightweight framework that logs multi-agent trajectories, extracts coordination assets, and reuses them through prompt-channel guidance, asset-based routing, or both. On APPS-derived code-repair tasks, prompt-channel asset reuse improves shifted-split success from 68.9% to 82.2%, exceeding the strongest non-reuse baseline by 6.6 percentage points, and reduces empty or missing patch failures from 13/45 to 4/45 attempts. Full reuse does not improve over free self-organization, showing that organizational memory is not monotonically beneficial. A controlled repeated-games study further shows that trajectory-derived strategy assets transfer beyond code repair, improving cooperation in Public Goods games while matching persona prompting in saturated Prisoner's Dilemma settings. Overall, ORCA supports a structured view of multi-agent memory: coordination patterns can transfer across tasks, but they should be decomposed into typed assets and reused selectively rather than replayed wholesale.
