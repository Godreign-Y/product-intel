# 06_simulator_spec.md

```markdown
# SIMULATOR SPEC

## Inputs

1. Product Definition
2. Baseline State
3. Market Conditions
4. Action Schedule

---

# Processing Order

Step 1

Apply Market Effects

↓

Step 2

Apply Active Action Effects

↓

Step 3

Apply Interaction Effects

↓

Step 4

Apply Noise

↓

Step 5

Generate Next State

---

# Output

State(t+1)

---

# Trajectory Generation

Input

```text
Anchor State
+
Action Schedule
+
365 Days
````

Output

```text
State(t+1)
State(t+2)
...
State(t+365)
```

---

# Training Data Generation

Input

```text
Past State Window

+

Future Action Schedule
```

Output

```text
Future State Trajectory
```

---

# Future Capabilities

1. Forecasting

Action
→
Outcome

2. Planning

Desired Outcome
→
Recommended Actions

3. Explainability

Outcome
→
Reasoning

````