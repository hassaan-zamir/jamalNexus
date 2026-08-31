# Skill: Teardown Coach
For Block D and P5. Enforce the CSV schema:
video_id,ts_in,ts_out,duration_s,shot_type,source_type,transition_in,sfx_present,text_on_screen,text_treatment,music_state,colour_temp,notes
- shot_type: aerial|wide|medium|closeup|screen|document|graphic|archive
- transition_in: hard_cut|whip|dissolve|speed_ramp|match_cut|film_burn|glitch
- music_state: absent|bed|build|peak|drop_out
Teardowns land in projects/<project>/teardowns/. After 50+ rows, compute with him: median shot length, cuts/min by section, music-change points, pattern-interrupt spacing. Push findings into kb via a session event (defects/insights). The point is internalising rhythm — make him say the numbers out loud.
