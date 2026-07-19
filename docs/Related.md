# Related Work Notes for ORCA

## Scope

This note records literature that can support the Related Work section of the
ORCA paper. It separates verified conference papers from candidates whose
publication venue still needs confirmation. The paper should position ORCA as
an empirical study of trajectory-derived coordination assets, not as the first
multi-agent framework, memory system, or software-engineering agent.

## Verified Core References

| Key | Work | Venue / CCF | What it establishes | How ORCA should relate to it |
|---|---|---|---|---|
| `reflexion2023` | *Reflexion: Language Agents with Verbal Reinforcement Learning* | NeurIPS 2023, CCF-A | Verbal feedback from prior attempts can improve later agent behavior. | Contrast individual-agent reflection with reusable team-level role and organization assets. |
| `expel2024` | *ExpeL: LLM Agents Are Experiential Learners* | AAAI 2024, CCF-A | Agents can accumulate and retrieve cross-task experience. | Use as the closest experience-reuse reference. ORCA changes the unit of reuse from task-solving experience to coordination structure. |
| `metagpt2024` | *MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework* | ICLR 2024, CCF-B | Standard operating procedures and predefined roles can organize LLM-agent teams. | Contrast predefined SOPs with assets distilled from successful trajectories and then ablated on held-out tasks. |
| `chatdev2024` | *ChatDev: Communicative Agents for Software Development* | ACL 2024, CCF-A | Role-specialized agents and structured communication can support software-development workflows. | Contrast static role/chat-chain design with cross-run reuse of coordination information. Do not claim ORCA is the first role-based software team. |
| `sweagent2024` | *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering* | NeurIPS 2024, CCF-A | Interface and tool design materially affect end-to-end software-engineering agents. | Use to establish the code-agent setting; distinguish ORCA's question of coordination reuse from stronger single-agent interfaces. |
| `autocoderover2024` | *AutoCodeRover: Autonomous Program Improvement* | ISSTA 2024, CCF-B | Repository-aware localization and repair workflows are important for autonomous program improvement. | Use as code-repair context, not as a direct multi-agent-memory baseline. |

### Source Links

- Reflexion: https://doi.org/10.52202/075280-0377
- ExpeL: https://doi.org/10.1609/aaai.v38i17.29936
- MetaGPT: https://dblp.org/rec/conf/iclr/HongZCZCWZWYLZR24
- ChatDev: https://aclanthology.org/2024.acl-long.810/
- SWE-agent: https://doi.org/10.52202/079017-1601
- AutoCodeRover: https://doi.org/10.1145/3650212.3680384

## Conditional References

| Work | Status | When to use it |
|---|---|---|
| *AFlow: Automating Agentic Workflow Generation* | 2025 candidate; verify the official proceedings record and CCF classification before citing. | Useful to contrast automated workflow search with ORCA's reuse of previously observed coordination assets. |
| *Generative Agents: Interactive Simulacra of Human Behavior* | UIST 2023; relevant to memory and social behavior rather than the APPS result. | Cite only if the repeated-games domain is redesigned as a genuine trajectory-derived asset experiment. |

The current repeated-games implementation uses static strategy prompts rather
than assets extracted from source trajectories. It should not be used to claim
that ORCA's asset-extraction mechanism transfers to social dilemmas.

## Recommended Paper Structure

### 1. Multi-Agent Coordination and Role Design

MetaGPT and ChatDev show that LLM agents can be organized with explicit roles,
standard operating procedures, and structured communication. These systems
primarily specify coordination before execution. ORCA instead asks whether
coordination information observed in successful source trajectories can be
stored as typed assets and reused selectively on later tasks. This distinction
is about the provenance and transfer of coordination, not whether role-based
collaboration itself is novel.

### 2. Agent Memory and Experience Reuse

Reflexion and ExpeL demonstrate that language agents can improve through
feedback and accumulated experience. ORCA is complementary: its assets encode
how a team divided and handed off work, rather than only how an individual
agent solved a task. The paper should state this as a different empirical unit
of memory, not as a claim that prior work ignores memory or experience reuse.

### 3. LLM-Based Software Engineering Agents

SWE-agent and AutoCodeRover establish that reliable software engineering
requires effective interfaces, localization, and repair workflows. ORCA does
not compete on benchmark-leading repair performance. It uses executable
APPS-derived repair tasks to test whether trajectory-derived coordination
assets improve held-out reliability, particularly under the shifted split.

## Suggested Related Work Draft

Large-language-model multi-agent systems commonly coordinate work through
predefined roles, procedures, or communication structures. MetaGPT organizes
agents around standardized operating procedures, while ChatDev uses role-based
chat chains for software development. ORCA builds on this line of work but
focuses on a different question: whether coordination observed in successful
runs can be retained as explicit, typed assets and reused on later tasks.

Agent memory and experience learning provide a second foundation. Reflexion
uses verbal feedback to improve subsequent attempts, and ExpeL stores and
retrieves cross-task experience for language agents. In contrast, ORCA treats
the unit of reuse as team coordination: role tendencies and organization-level
handoff procedures extracted from successful multi-agent trajectories. The
prompt-only, routing-only, and full-reuse conditions test these mechanisms
separately.

Finally, recent software-engineering agents such as SWE-agent and
AutoCodeRover demonstrate the importance of agent interfaces, localization,
and repair workflows. ORCA is complementary rather than a direct replacement
for these systems. Its APPS-derived experiment evaluates whether reusable
coordination assets affect multi-agent repair reliability, with the shifted
split used as the primary transfer condition.

## Claims to Keep Calibrated

- Say "trajectory-derived" or "heuristically distilled from successful
  trajectories" rather than claiming that all assets are fully emergent.
- Say that prompt-level reuse is an all-asset prompt injection in the current
  implementation; it is not an organization-asset-only ablation.
- Report the shifted APPS result as an observed three-seed comparison. Do not
  claim statistical significance without an appropriate paired analysis.
- Describe full reuse as not improving over free self-organization in this
  setting, rather than claiming a general harm from organizational memory.
- Omit the repeated-games result from the main Related Work positioning until
  that domain uses source-trajectory asset extraction and repeated evaluation.

## Before Paper Submission

1. Export the verified references to the paper's bibliography with author,
   title, venue, year, pages, and DOI/URL.
2. Confirm current CCF classifications against the official CCF directory
   required by the target venue or institution.
3. Verify the formal venue of every 2025 or 2026 candidate before it appears
   in the bibliography.
4. Keep the final Related Work section to the three themes above; avoid a
   broad survey of all LLM-agent systems.
