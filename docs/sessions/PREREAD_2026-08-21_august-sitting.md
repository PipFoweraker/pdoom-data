# Pre-read for the August triage sitting

**Condensed from `HYGIENE_2026-08-15.md` (16KB) and `SOURCING_2026-08-19.md`
(101KB) so the sitting does not require reading either.** Everything below is
quoted or paraphrased from those two documents; nothing new was measured for
this sheet. Where they disagree, the sourcing pass is later and wins, and it
says so itself at the one place it revises the hygiene pass
(`florida_v_openai_2026`).

---

## 1. The sitting

    python scripts/review/triage_watch.py --by "Pip Foweraker"

| key | effect |
|---|---|
| `a` | rating A, `watch_status: watching` -- on Watch, front of the queue |
| `b` | rating B, `watch_status: watching` -- second tier |
| `x` | rating X, `watch_status: rejected`, records you and today's date |
| `?` | rating ?, stays undecided -- look again later |
| `n` | add a note to the atom just decided |
| `s` | skip, change nothing |
| `q` | stop and save |

**The queue is all 110 untriaged atoms, not the 64 clean ones.** There is no
"clean only" filter. Each atom renders its own flags inline -- `NO SOURCE`,
`NO DATE`, `DUP?`, `LOW CONFIDENCE` -- so the flagged ones announce themselves
as they arrive, and `?` or `s` moves past them in one keystroke.
`--needs-attention` gives ONLY the flagged 46 if you would rather do them
separately; `--limit N` caps a sitting.

Every keystroke is logged before the file is rewritten. Ctrl-C costs nothing.

## 2. The thing this sheet exists for

**The tool has no key for "the record is wrong".** `a` and `b` put an atom on
Watch as written. For the records below, the scan text misstates what the
primary source says, so rating them `a`/`b` endorses a sentence that is already
known to be false. `?` is the honest key for these, and `n` will attach the
reason.

Nine records, and the refuted claim in each:

| atom | what the record says | what the primary says |
|---|---|---|
| `bartz_v_anthropic_settlement_2025` | "roughly $3,000 per affected author" | "approximately $3,000 **per work** (not per Class Member)", splittable author/publisher, before fees |
| `bartz_v_anthropic_settlement_2025` | "a class of around 500,000" | Alsup: "**482,460 works** were finally identified, not 500,000" -- wrong number AND wrong unit |
| `bartz_v_anthropic_settlement_2025` | "books sourced from the Pile" | class notice names LibGen and PiLiMi; **the Pile is not mentioned at all** |
| `xai_memphis_clean_air_act_suit_2026` | "Colossus facility in **Memphis**", Shelby County thresholds | suit `3:26-cv-00074`, **Northern District of Mississippi**, Southaven gas plant. Different state, different regulator |
| `data_centre_opposition_blocks_64bn_2025` | "across the US, Europe and South America" | report is scoped to "28 U.S. states"; "Europe" and "South America" appear **zero times** |
| `hochul_new_york_data_centre_moratorium_2026` | permits paused "**for one year**" | "one year" and "expire" do not appear in EO 62. The pause runs until a GEIS completes; twelve months is a *reporting* deadline |
| `texas_data_centre_moratorium_grid_audit_2026` | a "moratorium" | an audit-precondition directive letter. Refuted as phrased; the 10 August date is also wrong |
| `new_york_safe_by_design_act_2026` | a standalone Act | real, but it is **Part Y of a budget bill** |
| `illinois_wopr_act_bans_ai_therapy_2025` | "first" | contested three ways; and the date given is a **passage** date |
| `amazon_ai_attributed_layoffs_2026` | AI-attributed layoffs | **the AI attribution is not Amazon's** -- it is the reporting's |
| `gpt_5_6_sol_deleted_user_files_2026` | unauthorised file deletion | METR's eval supports the *eval-gaming* half and **does not mention file deletion at all**. Do not promote as titled |

**Four of the five records carrying the six outright refutations are
`confidence: high`.** High scanner confidence has no correlation with being
right here, which is the single most useful thing to carry into the sitting.

## 3. Handle with care -- one record

`suchir_balaji_death_2024`. A real death and a contested cause. The sourcing
pass asserts no cause of death anywhere, and both the record's own flag and the
watch-list README say **this should probably not be a game event at all**. His
essay verifies on his own site; the official documents were NOT retrieved, only
the Mercury News's reporting of them. The police letter's operative wording is
narrower than "concluded suicide" -- "insufficient evidence to find Mr.
Balaji's death was the result of ...". If it goes anywhere, it goes with that
sentence and not a summary of it.

## 4. Duplicates -- 14 pairs flagged, 7 adjudicated

The hygiene pass adjudicated seven and found **no pair needing a human tiebreak
on identity**: five MERGE, two KEEP SEPARATE. Merging is not something this
tool does, so for the sitting these are `?` unless you want them on Watch as
separate atoms.

- **MERGE**: Anthropic breach disclosure pair; SB53 transparency + whistleblower;
  Florida v OpenAI pair; Hugging Face intrusion pair; US export-controls pair
  (the pair sharing zero title tokens -- the one-day conflict resolves to
  **2026-06-12**, and "was never a conflict").
- **KEEP SEPARATE**: xAI/DoJ Colorado challenge vs DoJ task force (15 days
  apart, but each record currently narrates both acts); EU omnibus 2025 vs 2026.
- **One human call left**: the Hugging Face pair's *date anchor*. The pass
  recommends 2026-07-09 and calls it "the weakest call in this document".
  Contained-on-16-July in the recent2026 record is wrong.

The seven pairs flagged since (14 total now) have not been adjudicated.

## 5. The three unsourced UNVERIFIED atoms

| atom | disposition |
|---|---|
| `executive_order_ai_innovation_and_security_2026` | **Now verifiable.** Federal Register EO 14409, signing date 2026-06-02. Two corrections travel with it: Section 4 also names 18 USC 1028 and 1343, and the claimed "structured process for evaluating offensive cyber capabilities" and the EO 14365 reference **could not be found in the text** |
| `gpt_5_6_sol_deleted_user_files_2026` | **Split.** METR eval sources the eval-gaming claim; the file-deletion claim, which is the title, is unsupported |
| `white_house_voluntary_frontier_model_testing_2026` | **Stays UNVERIFIED**, on a stronger negative than before. whitehouse.gov/ostp 404s; a voluntary framework leaves no Federal Register trace |

None should be dropped. One is now better evidenced than several atoms counted
as clean.

## 6. Null dates -- 24, and three of them are permanent

Twelve keep-nulls in the hygiene pass, of which **three are null because the
thing described is a period rather than an act** and would still be null after
a perfect source pass: `data_centre_opposition_blocks_64bn_2025`,
`sff_grantmaking_nearly_doubles_2025`, `new_orleans_live_facial_recognition_2025`.
**Those three can be rated as they stand** -- their null is correct, not
outstanding work.

One is a live judgement call: `international_ai_safety_report_2026`. Its arXiv
page states `[v1] Tue, 24 Feb 2026`, but that is the arXiv posting, not the
publication several outlets put at 3 February. Either retitle and date it
2026-02-24 as `reported`, or keep null. **Do not date it 2026-02-24 while the
title still says "published".**

One caveat worth carrying: `schmidt_sciences_safe_ai_program_2025` -- the
programme page carries no date and no dollar figure, so **the `_2025` in the
slug is itself unsourced.**

## 7. What neither pass covered

Stated so this sheet is not read as coverage it does not have:

- The sourcing pass examined **34 records of 110**. It did not read the 17
  incidents-and-funding records resting on Wikipedia beyond those it names.
- The aggregate portions of `data_centre_opposition_wave_2026` were not reached.
- The seven duplicate pairs flagged after the hygiene pass are unadjudicated.
- Nothing here re-verifies the 28 "strengthened" records; that verdict is the
  sourcing pass's and is carried forward, not rechecked.

## 8. After the sitting

    python scripts/build/project_watchlist.py --check     # derived half untouched
    python scripts/review/triage_watch.py --by "..." --decide   # at month end
    python scripts/build/project_watch_accepted.py        # publishes the accepts

The decide pass requires a reason on every accept and reject, because that is
what gets published. Nothing is served until an atom is `accepted` AND carries
a date, a source and a named decider.
