# Skill: Memory Extraction (run at the end of EVERY session)
Turn the conversation into graph growth. Be selective — a session yields 0–3 observations, not a transcript.

1. **Scan for durables:** goals, preferences (how he wants to be coached/talked to), commitments and dates, people and orgs that recur, topics he's drawn to, tools he uses, habits and working patterns, insights about how he learns.
2. **Skip:** one-off details, task chatter, anything already in the graph, your own advice (only what HE said or decided), transient moods.
3. **Ask before filing anything personal:** "Want me to remember that?" If he says no, don't — and don't file a vaguer version of it either.
4. **Set visibility deliberately.** Work/craft/deliverable-affecting -> `--shared`. Life, family, money, feelings, opinions about people -> default `--private` (the tool's default). Ambiguous -> ask.
5. **Write it:**
   `python3 tools/remember.py node goal:learn-colour goal --attr note="wants Resolve-level grading by Dec" --shared --confirmed`
   `python3 tools/remember.py edge person:jamal prefers preference:blunt-feedback --private --confirmed`
6. **Then** append the session event to logs/sessions.jsonl (if craft work happened) and run `python3 kb/ingest.py`.
7. On "forget that": `python3 tools/remember.py forget <id>` and confirm out loud.

Never file: precise health details, financial account details, anything he retracted. Never widen a private fact to shared later without asking him.
