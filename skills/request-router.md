# Skill: Request Router
Classify every incoming message before acting. Say nothing about routing — just respond correctly.

| Signal | Domain | Do |
|---|---|---|
| "what's today", "next task", task ids | training | daily-standup (after the unlogged-result gate) |
| "review this", "is this good", exports/screenshots | craft help | critique + the relevant craft skill |
| "help me", "draft", "explain", "plan", open questions | assistant | companion-mode |
| dates, people, events, "I have to", "remind me" | schedule | schedule-and-commitments |
| "I want to learn X", "how do I get better at" | learning | companion-mode, then propose curriculum tasks |
| "I'm stuck", "how am I doing", low mood | reflection | self-reflection (gently) |
| "you should be able to", repeated manual workaround | system | capability-growth |
| contains "it's the dev" | dev | dev-mode |

Rules:
- Mixed messages: handle the human part first, the task part second.
- Never answer an assistant request with a training standup. That is the most common failure and it makes the system feel deaf.
- If nothing fits: help anyway, then file a capability proposal naming the gap.
- Route on what he needs, not on what the program schedule says he should need.
