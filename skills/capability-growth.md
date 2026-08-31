# Skill: Capability Growth (the system extends itself)
Trigger: a request you handled poorly, a workaround repeated 2+ times, an explicit "you should be able to X", or a domain with requests but no skill file.

1. Name the gap in one sentence: what he wanted, what you couldn't do.
2. Classify:
   - **Class A** — a new or edited *skill file* that only changes how you behave in a domain you already serve. You may write it yourself now.
   - **Class B** — new tool code, network/API access, credentials, changes to visibility rules, the dev bridge, or anything that acts outside this repo. Propose only; the dev approves.
3. `python3 tools/remember.py capability "<title>" --class A|B --rationale "..." --spec "..."`
4. Class A: write `skills/<name>.md` in the house format (purpose, triggers, procedure, rules), add it to the router table, tell Jamal what you just learned to do.
   Class B: tell him it's queued, write it to dev/flags.md, and carry on with the best manual workaround.
5. Never grant yourself Class B powers by writing a Class A skill that describes them. If you're unsure which class something is, it's B.

Retire capabilities too: if a skill hasn't triggered in 6 weeks, raise it at the weekly review and consider merging or deleting it. A bloated skill set makes routing worse.
