# OmniMind Multi-Agent Workflow

## How Agents Coordinate

1. **User Action:** User uploads resume and syncs GitHub.
2. **Parsing:** Resume Agent and GitHub Agent extract raw data independently.
3. **Skill Aggregation:** Skill Agent takes output from Resume & GitHub Agents to generate a unified Skill Graph.
4. **Career Matching:** User inputs a target job. Career Agent compares Skill Graph with ATS requirements.
5. **Interview Simulation:** Interview Agent dynamically generates questions based on Career Agent's identified missing or weak skills.
6. **Recommendation:** Recommendation Agent builds a final personalized learning roadmap based on interview performance and skill gaps.
