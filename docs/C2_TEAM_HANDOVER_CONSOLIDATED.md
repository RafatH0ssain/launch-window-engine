# Challenge 2 Team Handover — Consolidated Technical Document

**Date:** 2026-10-04 (Sun 4 Oct 2026; submission 13:30 ADT)
**Audience note:** This document is the single onboarding + methodology-slide picker for a teammate. She
should be able to (a) get up to speed on Challenge 2 without reading the whole repo, and (b) lift technical
terms, numbers, citations, and file paths directly onto methodology slides. All spec numbers, file paths,
DOIs, and NTRS IDs are kept verbatim/liftable. Section 6 (Results so far) is explicitly marked as evolving —
check `backend/engine/DONE.md` and `backend/engine/progress.md` for the latest state before freezing slides.
No emojis.

This document is written in full explanatory prose on purpose. A teammate with no prior context — no orbital
mechanics background, no knowledge of Spaceport Nova Scotia, no familiarity with our repository layout — must
be able to read it cover to cover and come away with a deep working understanding of the problem we were
given, the gaps we identified in the existing literature and tooling, the prior art we built on, the
methodology we designed, the advanced mathematics and machine learning we claim, the results we have in hand,
the testing discipline that backs those results, the credibility arguments that will persuade judges, and the
live-data platform that turns all of this into a usable product. Every fact from the earlier terse version is
preserved, but every fact is now wrapped in explanation of what it is, why it matters, how it works, and why
we chose it the way we did.

## Table of Contents

1. Problem
2. Gap Analysis (THGASP)
3. Existing Work / SOTA
4. Our Methodology
5. Advanced Maths / ML / Stats / Physics
6. Results So Far (EVOLVING)
7. Tests / Validation
8. Credibility
9. Live-Data + Platform Capability / Functionality
10. What's Next
11. Key Files
12. Glossary

---

## 1. Problem

### 1.1 What Challenge 2 asks for

Challenge 2, nicknamed "Mission Control" and also known internally as Ben's special challenge, asks teams to
build a tool that calculates optimal launch windows from orbital requirements, plus a user-friendly interface
that serves both professional mission planners and members of the public. That two-part framing is deliberate.
The first half is a hard astrodynamics computation problem: given a desired orbit, when should a rocket lift
off so that it can actually reach that orbit from the chosen launch site, subject to geometry, physics,
weather, range safety, and traffic constraints. The second half is a human-factors and communication problem:
how do you present those computed opportunities so that a planner can make a go or no-go decision and a member
of the public can understand when to watch and why a date moved.

Understanding this duality matters because it drives every downstream decision in our project. A team that
only builds a pretty countdown page has not solved the orbital problem. A team that only writes an
astrodynamics library with no interface has not satisfied the mandate that the work be usable by planners and
the public. Our answer, explained in detail below and in Section 1.5 on the track decision, is to declare the
orbital engine as our core and to deliver it through a dashboard interface, so that both halves are honoured
but the judged contribution is unambiguous.

The phrase "optimal launch windows from orbital requirements" deserves unpacking because it is the entire
technical problem in one phrase. An orbit is specified by a set of requirements — in our case principally the
target orbit type, which maps to a target inclination and, for Sun-synchronous orbits, a target node phasing
tied to local solar time. A launch window is a interval of time on a given calendar date during which liftoff
leads to successful insertion into that orbit without violating safety corridors or spending excessive
propellant on out-of-plane manoeuvres. The word "optimal" means we do not just enumerate feasible seconds; we
rank candidate dates and times by a probability of actually launching successfully, accounting for weather and
other stochastic blockers, and ultimately by expected cost of delay. That ranking is what makes the tool
useful to a planner who must choose one date among many.

### 1.2 The launch site: Spaceport Nova Scotia at Canso

All of our analysis is anchored to a single real launch site, and that specificity is a strength rather than a
limitation. The site is Spaceport Nova Scotia, located near the town of Canso, Nova Scotia, Canada. In our
files you will see two closely related coordinate pairs and it is important to understand why both exist and
which one to use when. The general site reference used in the Cyclone-4M User's Guide and in much of our early
documentation is 45.3 degrees North latitude, 61.0 degrees West longitude. That is a rounded site-level
coordinate, convenient for hand calculations and perfectly adequate for explaining the geometry on slides. The
Environmental Assessment (EA) variant, which is the more precise surveyed coordinate tied to the assessed
launch-pad area, is 45.3033 degrees North, 60.9823 degrees West. The difference is roughly one to two
kilometres on the ground, which is negligible for window timing at the seconds-to-minutes level but which
matters for provenance honesty: when we report a number we say which coordinate produced it.

The operator of the spaceport is Maritime Launch Services, universally abbreviated MLS in our documents. MLS
intends to fly the Cyclone-4M vehicle, a medium-lift launcher developed from Ukrainian Zenit heritage.
Whenever you see Cyclone-4M, C4M, or AUG in our files, they refer to this vehicle and its guidance system. The
Ascent Unit Guidance azimuths quoted later are the programmed launch headings for this vehicle from Canso.

Three site facts together define the operating envelope and each of them shapes the engineering. First, all
trajectories fly south over the Atlantic Ocean. This is a range-safety design choice. Launching over water
means that spent stages and any debris from a failure fall into an unpopulated ocean hazard area rather than
over towns or shipping lanes, and it means the permitted launch azimuth corridor is a south-facing fan rather
than a full circle. That fan is why our reachability analysis uses a minimum azimuth near 90 degrees (due
east) and a maximum near 200 degrees (just west of due south), and why certain inclinations are simply
unreachable without an expensive plane change. Second, the Environmental Assessment was approved in June 2019
as a Class I assessment, with the formal approval date recorded as 4 June 2019. The EA is the regulatory
instrument that allows launches to proceed at all, and it carries conditions that flow directly into our
constraints model. Third, two of those conditions are quantitative and slide-liftable: a maximum of 8 launches
per year, and launch hours restricted to 07:00 to 12:00 local time. The flight-rate cap means every scrubbed
date is expensive because there are so few slots in a year. The morning-only window means the daily orbital
geometry must coincide with a five-hour local-time box, which eliminates many otherwise valid ascending-node
alignments and is one reason a probability-ranked list of dates is genuinely useful rather than decorative.
Complementary regulatory references are CARs 602.43 and 602.44, the Canadian Aviation Regulations provisions
governing launches, which we verified at the authoritative source laws-lois.justice.gc.ca. Citing the primary
legal source rather than a secondary summary is part of our credibility discipline described in Section 8.

### 1.3 The three slide inclinations and why they are the engine's target orbit types

The challenge materials and MLS marketing specify three target orbit types by inclination, and we reproduce
them verbatim because they are the contract the engine must satisfy. LEO, meaning low Earth orbit in the
generic low-inclination sense intended by MLS, is quoted at approximately 45.1 degrees. Polar, meaning a
near-polar orbit that passes close to both poles, is quoted as a range from 87.9 to 90 degrees. SSO, meaning
Sun-synchronous orbit, is quoted at approximately 98.1 degrees. These three values — 45.1, 87.9 to 90, and
98.1 — are the three engine Target Orbit Types. Every window the engine computes is computed for one of these
inclinations (or a nearby altitude-specific refinement in the SSO case), and every test, validation anchor,
and slide number traces back to them.

It is worth explaining for a newcomer what inclination means and why these three values matter. Inclination,
conventionally denoted by the lowercase letter i, is the angle between the orbital plane and Earth's
equatorial plane. An inclination of zero would be an orbit directly above the equator flying eastward; 90
degrees is a polar orbit flying over both poles; values above 90 degrees are retrograde, meaning they fly
partly westward against Earth's rotation. Low-inclination LEO at 45.1 degrees is roughly matched to the
latitude of Canso and is attractive for communications or regional missions that do not need global coverage.
Polar orbits near 90 degrees give global coverage as Earth rotates beneath them and are the workhorse for
Earth observation. Sun-synchronous orbits near 98 degrees are a special retrograde family whose nodal
precession is tuned to follow the Sun, so that the satellite always passes overhead at the same local solar
time and therefore sees consistent lighting for imaging. That lighting consistency is why SSO is prized for
optical Earth-observation missions such as the Sentinel family that we use as validation anchors in Section 6.

A central and initially surprising result of our work, documented as a falsification in Section 6 and derived
in Section 4.1, is that the first of these three marketing numbers — 45.1 degrees — is in fact geometrically
unreachable by a direct ascent from a site at 45.3 degrees North without an out-of-plane manoeuvre. This is
not a bug in our code; it is spherical geometry. The minimum inclination reachable by direct launch equals the
site latitude, and 45.1 is two-tenths of a degree below 45.3. The engine therefore correctly returns a priced
refusal for 45.1 degrees rather than a fabricated window, together with the plane-change velocity cost of
about 26.8 metres per second that would be needed to fix the mismatch. That honest refusal is one of our
strongest credibility signals, and it is why the three numbers must be kept verbatim: we test against the real
marketing claims, not against sanitised values that would hide the problem.

### 1.4 The official spec: two tracks, one rubric

The authoritative statement of what the judges expect was transcribed directly from a photograph of the
challenge slides into Appendix A of our build specification, lines 871 to 885 of that appendix, and we keep
the transcription verbatim so that there can be no dispute about what was asked. Track 1, titled "The Orbital
Architect," asks for an engine that takes a Target Orbit Type — the LEO, Polar, and SSO inclinations above —
and produces compatible launch dates and times. Its stated bonus, which we treat as a required deliverable
because it distinguishes a real ascent-aware engine from a simple node-alignment calculator, is Vehicle
Duration, defined as the distinction between the injection-point time and the liftoff-moment time. In other
words, the engine must model the fact that the rocket does not teleport to orbit at the instant of liftoff; it
flies a powered ascent lasting several minutes, during which Earth rotates and the target orbital plane
continues to precess, so the node that matters is the node at injection, not the node at liftoff. Track 2,
titled "The Launch Watcher," asks for a web Launch Dashboard with a countdown, two-dimensional and
three-dimensional trajectory visualisation, and a Weather Impact indicator in Green, Yellow, and Red states
(abbreviated G/Y/R throughout our docs) driven by mock or real weather API data. Its stated bonus is a Viewing
Map showing where members of the public can watch the launch.

The judging rubric has eight rows, each scored from 1 to 5: Definition, Relevancy, Significance, Feasibility,
Viability, Originality, Coherency, and Team Presentation. Understanding each row matters because it tells us
where points are won and lost. Definition rewards a crisply stated problem and scope. Relevancy rewards
alignment with real Canadian space needs, which our Canso-specific, MLS-anchored work satisfies directly.
Significance rewards the magnitude of the impact, which is where a validated probability layer and a
delay-cost model earn their keep. Feasibility rewards a credible plan that can actually be built in the
hackathon window, which is why our gated workflow with a shipped deterministic engine matters. Viability
rewards a path to sustained operation beyond the demo, which is why keyless live-data feeds and a real API
surface matter. Originality rewards novelty relative to published work, which is why our gap analysis and our
honest handling of pre-empted ideas matter. Coherency rewards a solution whose parts fit together, which is
why every dashboard pixel must render an engine output rather than decoration. Team Presentation rewards a
clear, well-evidenced pitch, which is why this handover document keeps every number liftable onto slides.

### 1.5 The track decision and its quantitative rationale

Teams must declare one track as their claimed core while the goals line of the challenge mandates an
interface, and our decision is to declare Track 1 and deliver through a Track 2 interface. In plain language:
we are judged as an orbital-engine team, and the dashboard exists to display what the engine computes, not as
an independent contribution. The rationale is quantified, not asserted, in Section B of
`research/challenge2/C2_prior_art_and_track.md`, where we scored both tracks against the eight-row rubric and
obtained sums of 41 for a Track 1-led entry versus 36 for a Track 2-led entry. The five-point gap comes
principally from Originality and Significance: a validated, forecast-coupled, Canso-specific window engine
with hindcast skill scoring is genuinely novel, whereas a countdown with trajectory graphics, however
polished, is pre-empted by countless prior dashboards and scores poorly on Originality. The operative rule
that falls out of this decision, repeated throughout our workflow docs, is that every pixel must render a
Track 1 engine output and there is to be no decorative 3D. A rotating globe that does not reflect a computed
ground track is not just wasted effort; it actively undermines the Coherency and Originality scores by
suggesting the team confused visualisation with computation.

### 1.6 The authority spec and how it is organised

The single authority for what to build and in what order is
`research/challenge2/C2_framework_and_build_spec.md`, an 891-line specification document, with a verbatim copy
held at `hackathon_repo/docs/spec/` so that the build tree always contains the version the code was written
against. Newcomers sometimes ask why one document needs nearly nine hundred lines; the answer is that it is
simultaneously a science reference, a build manual, a validation plan, an API contract, a frontend guide, and
a judging strategy, and keeping all of those in one versioned place prevents the drift that kills hackathon
integrations. Its structure is as follows. Section 0 is the Executive Summary, which states the Track 1
declaration, the engine-plus-dashboard architecture, and the gated schedule in one page. Part I states the Gap
and the Contribution, which is the material expanded in Section 2 of this handover. Part II is the Scientific
Framework, running from II.0 on symbols and notation through II.10 on constants and provenance, and it is the
mathematical heart of the project: every equation the engine implements, every constant it uses, and every
provenance flag it emits is defined there. Part III is Validation, which defines the unit checks, the hour-12
gate, the hindcast skill scoring, and the honesty requirements. Part IV defines the APIs, meaning the HTTP
surface the engine exposes. Part V defines the Frontend, meaning what the dashboard must and must not do. Part
VI holds the Researcher tables, which are the site, vehicle, and published-window reference data. Part VII
covers the Report and the rubric mapping, meaning how each piece of work converts into judging points. Part
VIII is the Schedule, which maps work items to owners and gates. Appendix A is the verbatim slide
transcription, lines 871 to 885, so that any dispute about what the challenge asked can be resolved by opening
one file.

Our self-score against the eight-row rubric is 37 out of 40, with the two weakest rows at 4 out of 5 each
being Significance and Originality. That self-assessment is deliberately harsh: Definition, Relevancy,
Feasibility, Viability, Coherency, and Presentation are all at or near full marks because the engine is built,
tested, and honestly scoped, but we do not award ourselves full marks for Significance or Originality until
two specific technical milestones land. The path from 4 to 5 on both rows is the same pair of deliverables: a
live hindcast Brier skill score (BSS) demonstrating that our forecast-coupled probabilities beat climatology
on real historical dates, and a delay-cost layer implementing the published O'Neill delay-cost model that
converts a probability distribution over dates into an expected-cost-optimal recommendation. Both are
described in later sections; the point here is that the self-score is tied to verifiable artefacts, not to
optimism.

### 1.7 Supporting research documents

Four supporting research documents sit alongside the authority spec under `research/challenge2/`, and each has
a distinct role that a newcomer should understand before diving in. `C2_launch_window_science.md`, organised
in Sections A through G, is the physics compendium: it collects the window geometry, the J2 perturbation
theory, the operational algorithms literature, the weather and commit-criteria literature, and the
forecast-versus-climatology skill literature in one place with citations. `C2_prior_art_and_track.md`, also in
Sections A through G, is the citation ledger and the track-decision record: it is where every prior-art claim
is sourced, where the rubric arithmetic of 41 versus 36 lives in Section B, and where the pre-emption analysis
that prevents us from claiming novelty for solved problems is recorded. `C2_science_hunt.md` is the site-facts
dossier: it records the coordinate variants, the azimuth derivations, and the Bermuda-overflight note, which
is the observation that certain south-launched trajectories from Canso pass near or over Bermuda and therefore
carry a downrange-safety consideration worth flagging on slides as evidence of real range awareness.
`C2_preemption_map.md` is the kill-versus-keep list: it records, with section references to Section 0 and item
A2 in particular, which ideas are pre-empted by prior art and must be shipped as quantified numbers rather
than novelty claims, and which ideas survive as genuine contributions.

### 1.8 Integration documents and process scaffolding

Because a hackathon project with parallel owners fails without interface discipline, we maintain a set of
integration documents under `hackathon_repo/docs/`. The file `00_INTEGRATION_CONTRACT.md` is the master
contract: it defines the four workflows, the three seams between subsystems, and the six gates G0 through G5
that pace the build. `01_WORKFLOW_ENGINE.md` governs the deterministic orbital engine.
`02_WORKFLOW_WEATHER.md`, also referenced as 02_WEATHER, governs the probabilistic weather layer.
`03_WORKFLOW_API.md`, also referenced as 03_API, governs the HTTP service that exposes the engine to the
frontend. A fourth document, conventionally called 04_FRONTEND, governs the dashboard. Alongside these sit the
per-issue records `docs/issues/issue-01` through `issue-07`, which are the working papers for each GitHub
issue.

The process scaffolding itself is seven single-owner GitHub issues on the repository
`nafisahnubah/MDA_Mission_Accepted_Hackathon`, and single ownership is the point: every deliverable has
exactly one person accountable for it, which eliminates diffusion of responsibility. Issue 1 is CONTRACT/G0,
owned by Rafat, which freezes the JSON schemas. Issue 2 is ENGINE/G1, owned by Anand, which builds and
validates the deterministic core. Issue 3 is WEATHER/G2, owned by Het, which builds the forecast and
climatology adapters. Issue 4 is API, owned by Rafat, which wraps the engine in a FastAPI service. Issue 5 is
FRONTEND, owned by Nubah, which wires the prototype dashboard to the live API. Issue 6 is INTEGRATION, owned
by Anand, which runs the end-to-end tests. Issue 7 is WEATHER-VALIDATION, owned by Het, which computes the
hindcast skill scores. A newcomer who wants to know who to ask about any subsystem need only consult this
list.

---

## 2. Gap Analysis (THGASP)

THGASP in the tasking is this section: the gap analysis. The word "gap" here has a precise meaning that a
newcomer must internalise, because the entire Originality and Significance scoring depends on it. A gap is not
a vague statement that "little work exists." It is a specific, evidenced claim of the form: no published work
does X for site Y with validation method Z, and here is the search we performed that justifies the word "no."
Each of our six gap items below follows that discipline: it states what is missing, it states what we searched
to establish the absence, it states where the supporting evidence lives in our citation ledger, and it ends
with a build directive — KEEP, meaning this is a genuine contribution we will implement and claim, or KILL,
meaning the idea is pre-empted and we will ship it only as a quantified number or a delivery surface without
any novelty claim. That kill-versus-keep discipline is what stops us from embarrassing ourselves in front of
judges by claiming novelty for solved problems.

### 2.1 No published Canso window, azimuth, or climatology study exists

The first gap is the foundation of our Originality claim. To the best of our knowledge, established by the
literature search recorded in Section A.9 and Section C.3 of `C2_prior_art_and_track.md`, there is no
published study that computes launch windows, launch azimuths, or weather-availability climatology
specifically for Canso. What does exist for Canso is Environmental Assessment documentation, economic impact
material, and promotional material from MLS — all valuable for site facts, but none of which contains orbital
analysis.

We want to be concrete about what "searched" means here, because judges rightly press on negative claims. Our
EA evidence comes from a literal text search (grep) over the EA Registration Document numbered 16-5903 and the
EA Focus Report, files running to roughly 9,000, 21,000, and 6,000 lines respectively. That search looked for
fog-day statistics, scrub statistics, availability numbers, and any numeric launch-corridor definition. The
result was negative on all counts: the EA contains no fog-day counts, no scrub or weather-availability
numbers, and no numeric corridor. The corridor figure in the EA, referenced as Figure 2.9, has no axis labels
and no coordinates — it is a schematic, not a specification. A schematic corridor cannot be compiled into an
engine, which is exactly why our corridor bounds are flagged as an assumption (A_min 90 degrees, A_max 200
degrees) with full provenance rather than presented as surveyed fact. The absence of any published
Canso-specific window or azimuth numbers means our engine-verified azimuths (177.01, 180.00, and 191.56
degrees for the three target inclinations) and our window computations are, as far as the published record
shows, the first open numbers of their kind for this site. That is a genuine, defensible contribution, and it
is why this item is marked KEEP in spirit: build it, validate it, and put it on slides.

Why does this gap matter beyond scoring? Because Canada is pursuing sovereign launch capability and the first
Canadian commercial spaceport has no open orbital analysis that a planner, insurer, or student can inspect.
Every other serious launch site in the world — Cape Canaveral, Kourou, Vandenberg, Plesetsk — has decades of
published window analyses that newcomers can read and reproduce. Canso has none. Closing that gap with an
open, tested, provenance-flagged engine is therefore significant in the plain English sense as well as the
rubric sense.

### 2.2 No open, forecast-based, orbit-coupled, hindcast-validated probability of success exists for any Canadian site

The second gap is the deeper technical claim, and each adjective in it carries weight, so let us unpack them
one at a time. "Open" means the method, code, and data are inspectable rather than locked inside an agency
internal tool. "Forecast-based" means the probability on a given date comes from actual weather forecasts for
that date — ensemble prediction systems with explicit lead times — rather than from long-run averages alone.
"Orbit-coupled" means the probability is computed for a specific target orbit and its specific window geometry
(node alignment, corridor, ascent profile), not as a generic "good weather day" statistic divorced from what
the rocket is trying to do. "Hindcast-validated" means the method has been run retrospectively on past dates
for which both the forecast inputs and the actual outcomes are known, and scored against a reference, so that
we can say honestly whether it adds skill. A hindcast, for the newcomer, is a forecast run after the fact: you
rewind to a past date, generate the prediction your system would have made with only the information available
then, and compare it against what actually happened. It is the only honest way to validate a forecasting
system without waiting years for new data to accumulate.

Our claim is that no published system combines all four properties for any Canadian launch site. The evidence
is comparative and recorded in Sections C.1 and C.5 of the citation ledger. The American 45th Weather Squadron
(45WS) products and their Applied Meteorology Unit analyses compute per-constraint Probability of Violation on
launch day itself — excellent work, but day-of rather than forecast-horizon, per-constraint rather than
orbit-coupled, and Floridian rather than Canadian. The Marshall Space Flight Center APRA and PACER tools,
discussed in item 2.4 below and in Section 3.7, are climatology-only: they answer "what fraction of historical
days like this one violate a constraint" rather than "what does the forecast for next Thursday say," and they
are internal tools with no forecast coupling, no orbit coupling, and no public API. The Space Launch System
window work is internal to NASA and is about deterministic node alignment rather than probabilistic success
estimation. None of these is open, forecast-based, orbit-coupled, and hindcast-validated at a Canadian site.
The conjunction matters: individual pieces exist somewhere, but the combination — which is precisely what a
Canso planner needs — does not.

Why does this matter? Because a deterministic window that ignores weather is a fiction: it tells you when
geometry permits launch, not when launch is likely to succeed. And a generic weather probability that ignores
the orbit is nearly as unhelpful: a day with perfect weather at 09:00 is useless if the node alignment for
your target inclination occurs at 14:00 outside permitted launch hours. Only the coupled probability,
P(success given date), answers the planner's actual question, which is "which date should I pick." Building
that coupling with honest hindcast validation is our central Significance contribution.

### 2.3 Vehicle-duration ascent-aware windows are pre-empted: ship as numbers, not novelty

The third item is a KILL in the novelty sense and a KEEP in the engineering sense, and understanding that
distinction is essential to our claim discipline. The Track 1 bonus asks for Vehicle Duration — the
distinction between the injection-point time and the liftoff-moment time, meaning the engine must account for
the minutes-long powered ascent during which the Earth rotates beneath the vehicle and the target plane
precesses. The mathematics of ascent-aware window correction is genuinely important, but it is not novel: it
is pre-empted by the Space Launch System window algorithm work, by the Landsat Data Continuity Mission (LDCM)
analyses, and by the Astos ALWA (Ariane Launch Window Analysis) tooling, with the evidence recorded in Section
A.8 and Section C.2 of the citation ledger. Prior teams have solved the problem of shifting a window to
account for finite ascent time, and we must not claim to have invented it.

The correct response to pre-emption is not to delete the capability — the challenge explicitly asks for it —
but to ship it as quantified Canso numbers rather than as a novelty claim. Our slides will say, in effect:
"ascent-aware correction implemented via an injection-consistent fixed-point solve; for Canso and Cyclone-4M
the injection shifts are +1.48 and −0.40 seconds on the verified test cases; method follows the published
SLS/LDCM/ALWA lineage." That sentence earns Feasibility and Coherency points for a complete implementation
while conceding Originality on this sub-item, which protects our credibility on the items where Originality is
genuinely ours. A judge who catches a team claiming novelty for textbook material discounts everything else
the team says; a team that pre-emptively cites the lineage is trusted on its real claims. This is the
kill-versus-keep discipline in action, and it recurs throughout the pre-emption map.

### 2.4 Canso availability climatology is a KEEP

The fourth item converts the negative EA finding of item 2.1 into a positive work item. Because the grep over
the EA Registration Document and Focus Report found no fog-day data, no scrub data, and no availability
statistics, the basic climatological facts about Canso launch availability are simply unknown in the open
literature. Fog and precipitation are hard no-go constraints for launch — fog violates visibility and tracking
requirements, precipitation violates vehicle and lightning-related constraints — so the fraction of mornings
lost to these two phenomena is the single most important climatological number for a Canso planner, and nobody
has published it.

Quantifying that number from ERA5 reanalysis and ECCC station and model archives is therefore a genuine
contribution: the first open Canso availability climatology. It is also a prerequisite for everything else,
because the climatology serves as the reference forecast against which our forecast-based probabilities must
demonstrate skill. The Brier skill score described in Sections 4.5 and 5.3 is literally defined relative to
this climatology baseline, so without the climatology there is no honest skill claim. The work is unglamorous
— counting historical exceedances of threshold constraints month by month and hour by hour — but it is exactly
the kind of foundational empirical contribution that judges reward under Significance, because every
downstream probability depends on it.

### 2.5 Lobster fishing-area hazard cost is a KEEP

The fifth item is our most Canso-specific contribution and the one most likely to be remembered by judges. The
waters south of Canso, over which all trajectories fly, include Lobster Fishing Areas 31A, 31B, and 29 —
active commercial lobster grounds, abbreviated LFA31A, LFA31B, and LFA29 throughout our documents. A launch
hazard area that closes these grounds, even temporarily, imposes a real economic cost on fishers and a real
coordination cost on the range. No published launch-window analysis prices that cost or couples it to the
window selection, because no published launch-window analysis exists for Canso at all.

Our contribution is to treat the fisheries closure as a hazard-area cost layer in the opportunity model: each
candidate date carries not only a probability of launching but an expected cost that includes the hazard-area
impact, so that the optimiser can prefer dates whose hazard footprint avoids peak fishing activity where
geometry permits. This is Canso-specific in a way that no generic tool can replicate, it is relevant to the
actual community around the spaceport, and it speaks directly to the Relevancy and Significance rubric rows.
It also demonstrates the kind of grounded, place-aware engineering that distinguishes a serious proposal from
a generic orbit widget with the site name swapped in.

### 2.6 Dashboards and countdowns as ideas are pre-empted: build the surface, do not claim it

The sixth item closes the loop on the track decision. The idea of a launch dashboard with a countdown,
trajectory graphics, and weather lights is thoroughly pre-empted — every space agency, launch provider, and
enthusiast site operates one — and the pre-emption map records this in Section 0 and item A2. We therefore
build the dashboard strictly as the delivery surface for Track 1 engine outputs, and we claim nothing for it
under Originality. Every number on the dashboard must be traceable to an engine computation: the countdown
counts to a computed window, the trajectory renders a computed ground track, the weather lights reflect
computed constraint probabilities, and the viewing map reflects computed geometry. A decorative element that
renders no engine output is not neutral; it is negative evidence on Coherency, because it suggests the team
does not understand what its own contribution is. This rule is enforced in review: any frontend element that
cannot name the API field it displays does not ship.

---

## 3. Existing Work / SOTA

This section surveys the state of the art that we build on. Its purpose is twofold. First, it gives a newcomer
the background needed to understand why our engine looks the way it does: every equation we implement comes
from somewhere, and knowing the lineage prevents both reinvention and accidental plagiarism-by-omission.
Second, it is our pre-emption shield: by naming precisely what prior work did, we delimit precisely what we
may and may not claim as novel. The organisation follows the terse version — window geometry, J2 and SSO
theory, operational algorithms, tools, site facts, weather and commit criteria, climatological availability,
skill horizons, data sources, cost and manifesting, and early landscape context — but each item is now
explained in full: what the work actually did, why it mattered in its own context, and why it is insufficient
for the Canso problem, which together define the space our contribution occupies.

### 3.1 Window geometry (solved — build, do not claim)

The classical launch-window geometry is solved textbook material, and we treat it accordingly: we implement it
carefully, we test it rigorously, and we claim no novelty for it. The central relation is the
spherical-trigonometry identity cos(i) = cos(phi_s) * sin(beta). Here i is the target orbital inclination,
phi_s (sometimes written phi with a subscript s for site) is the geodetic latitude of the launch site, and
beta is the launch azimuth, which is the compass heading of the initial velocity vector measured clockwise
from true north, so that 90 degrees is due east and 180 degrees is due south. In words, the equation says that
the inclination you can reach directly is determined jointly by how far north your site is and which compass
direction you launch toward. Its physical content is the projection of the site's eastward rotational velocity
onto the target orbital plane combined with the geometric constraint that the launch site must lie in the
target plane at the instant of direct insertion.

Three immediate consequences fall out of this one equation and each is load-bearing for our engine. First, the
minimum direct inclination, denoted i_min, equals the site latitude phi_s. This is because sin(beta) cannot
exceed 1, so cos(i) cannot be smaller than cos(phi_s), which means i cannot be smaller than phi_s for direct
ascent. For Canso at 45.3 North, nothing below 45.3 degrees is directly reachable, which is the entire content
of our 45.1-degree priced refusal. Second, for any reachable inclination strictly above the minimum there are
two solutions — two azimuths, or equivalently two branches — corresponding to launching somewhat eastward
versus somewhat westward of the extreme, and on any given day the Earth's rotation brings the site under the
target plane twice, giving the familiar two-windows-per-day structure for non rappelling targets. Third, the
textbook form assumes an inertial launch direction, whereas the rocket actually flies in the rotating
Earth-fixed frame subject to winds and Earth rotation during ascent, so operational practice applies a
rotating-frame correction, commonly expressed as a tan(beta_rot) variant, that converts the inertial azimuth
into the compass heading the guidance system must actually fly. Getting this correction right matters at the
tens-of-arcseconds level for window timing and at the degree level for corridor compliance.

Our sources for this material are the standard textbooks by Vallado and by Curtis, which any astrodynamicist
will recognise as the canonical references; Volume 16 of the Robertson launch-vehicle series, which treats the
operational window problem; the early DTIC report AD0601072 from approximately 1962 on window-versus-delta-v
trades, which is worth citing because it shows the problem's lineage stretches back to the dawn of orbital
launch; the Apollo-era technical memorandum 19690067838, which documents how window analysis was done for
crewed lunar missions; and the OrbiterWiki worked example of a Cape Canaveral launch to the 51.6-degree
inclination of the International Space Station, which is pedagogically valuable because it walks through the
same two-branch arithmetic our engine automates. The detailed section references are Sections A.1, A.4, and
A.5 of `C2_launch_window_science.md`. The takeaway for slides is one sentence: window geometry is
nineteenth-century spherical trigonometry applied to twentieth-century launch problems, we implement it
exactly, and our contribution lies elsewhere.

### 3.2 J2 secular node regression and Sun-synchronous orbits

If window geometry answers "which inclinations can I reach," the J2 perturbation answers "where is the orbital
plane when I get there, and how fast is it moving." J2 is the largest deviation of Earth's gravity field from
a perfect sphere: Earth bulges at the equator, and that equatorial bulge exerts a torque on inclined orbits
that causes their ascending nodes to precess steadily around the pole. The ascending node is the point where
the orbit crosses the equator going north, and its celestial longitude is the Right Ascension of Ascending
Node, abbreviated RAAN and denoted by the capital Greek letter Omega. Secular here means a steady long-term
drift rather than a short-period oscillation, and regression means the direction of that drift for prograde
orbits. The governing equation, quoted from the NASA Goddard GDC Orbit Primer of October 2018, is dOmega/dt =
-(3/2) * J2 * n * (Re/p)^2 * cos(i). In words: the nodal drift rate equals negative three-halves times the J2
coefficient times the orbital mean motion n (which is the satellite's angular speed around its orbit, larger
for lower orbits) times the square of the ratio of Earth's radius Re to the orbit's semi-latus rectum p (which
is approximately the orbital radius for near-circular orbits, so lower orbits feel a stronger bulge torque)
times the cosine of the inclination (which sets the sign: prograde inclinations below 90 degrees regress
westward, retrograde inclinations above 90 degrees precess eastward).

This single equation is the reason Sun-synchronous orbits exist and the reason our SSO numbers look the way
they do. A Sun-synchronous orbit is a retrograde orbit whose eastward nodal precession is tuned to match
Earth's mean orbital motion around the Sun, which is 360 degrees per 365.2422-day tropical year, or
approximately +0.9856 degrees per day. When the node advances eastward at exactly the rate the Sun appears to
move, the angle between the orbital plane and the Sun stays constant, so the satellite crosses the equator at
the same local solar time every orbit — dawn-dusk or mid-morning, depending on the chosen phasing — giving the
consistent illumination that optical imaging missions require. Because the required precession rate is fixed
by the Sun while the J2 torque varies with altitude and inclination, each altitude demands its own
inclination: higher orbits feel a weaker bulge torque and so need a larger retrograde tilt to recover the same
eastward rate. Our verified SSO inclination-versus-altitude curve makes this concrete: 97.4 degrees at 500 km,
97.79 at 600 km, 98.08 at 674 km, 98.19 at 700 km, 98.6 at 800 km, and 99.03 at 900 km, with a local slope
di/dh of approximately 0.004 degrees per kilometre. The MLS marketing value of 98.1 degrees therefore
corresponds to an altitude near 675 to 700 km, which is exactly the altitude band of missions like the
Sentinels — a consistency check worth one line on a slide.

The correct Canso reference value for the J2 drift at 600 km altitude and 45.1 degrees inclination is negative
5.14 degrees per day (engine-verified as −5.1354), and the value 3.99 degrees per day that appeared in an
early draft is WRONG. The sign is negative because 45.1 degrees is prograde and prograde nodes regress
westward; the magnitude follows directly from substituting n for a 600 km orbit, Re/p for that radius, and
cos(45.1) into the GDC equation. We belabour this because a wrong drift rate corrupts every downstream number
— window recurrence, azimuth phasing, SSO coupling — and because the correction is slide-ready evidence of our
validation discipline: a literal grep for the string 3.99 over `backend/engine/*.py` exits with status 1 and
zero hits, meaning the wrong constant appears nowhere in the codebase, while the `j2.py` docstring names the
rejected constant in words without containing the literal, so the grep stays clean by construction. The
section reference is A.2 of the science compendium.

### 3.3 Operational window algorithms

Beyond textbook geometry, the operational literature contains complete flown algorithms for computing launch
windows under real constraints, and we studied them to ensure our engine follows established practice rather
than improvising. The Space Launch System algorithm documented as AAS paper 20-591 and archived as NTRS ID
20205004470 fits fifth-order polynomials to RAAN, inclination, and yaw-steering biases over a window of plus
or minus two hours, which is the heavyweight operational answer to the ascent-aware correction our fixed-point
solver handles more simply. The SLS Day-of-Launch (DOL) methodology in NTRS 20205001580 addresses the
complementary problem of updating the window solution on launch day as measured winds and final targeting
arrive. The Magnetospheric Multiscale mission's SWM76 solver in NTRS 20140010795 searched 32,400 pairs of RAAN
and argument of perigee in under 10 seconds, which is the existence proof that exhaustive grid search over
node phasing is computationally cheap and therefore a legitimate implementation choice rather than a naive
one. The James Webb Space Telescope analysis by Yu and Richon in NTRS 20160001318 evaluated 26,901 launch
epochs, demonstrating the scale of epoch enumeration that flagship missions consider routine. The Duan and Liu
2020 paper documents a two-dimensional search with a factor-of-100 speedup, relevant because it shows how
gridded search can be accelerated without sacrificing the global picture. The Zhou et al. paper at DOI
10.1002/oca.2546 treats the window problem with optimal-control machinery, and Deaton's yaw-steering work
treats the out-of-plane steering that connects window analysis to the plane-change costs we price. The section
references are A.1 through A.3 of the citation ledger and C.4 and E of the science compendium. The collective
lesson is that the deterministic window problem is thoroughly solved at the algorithm level, which is why we
claim engineering completeness and validation honesty for our deterministic core rather than algorithmic
novelty, reserving novelty for the Canso-specific coupling and validation described in Section 2.

### 3.4 Tools

The tooling landscape confirms the same conclusion from a different angle: general-purpose trajectory software
exists and is excellent, but none of it answers the Canso planner's question out of the box. STK (Systems Tool
Kit) is the industry-standard mission-analysis environment; GMAT, the General Mission Analysis Tool archived
as GSC-17778-1 with its verification and validation documented in NTRS 20140017798, is NASA's open-source
counterpart; Orekit is the Java-based open-source astrodynamics library; FreeFlyer is a commercial
mission-design tool; POST and its successor Copernicus are NASA's trajectory optimisation workhorses; Astos
ALWA is the commercial Ariane launch-window analyser; and the codingace LST-equals-RAAN calculator is the
simple web utility that equates local sidereal time to RAAN for quick estimates. Each of these can, in
sufficiently expert hands, be configured to compute a Canso window — but configuration is not a product, none
of them ships Canso climatology or Canso-specific hazard costing, none of them exposes a Canso-tuned
probability API, and none of them validates itself against published windows with an adversarial audit trail.
Our anti-GMAT positioning in Section 8 states this crisply: we are a decision layer over HTTP, not a
trajectory propagator, and our value is the coupling, the validation, and the honest refusal semantics, not
raw propagation capability.

### 3.5 Site facts (VERIFIED)

The site facts are the empirical bedrock, and every one of them carries a verification flag because a
surprising amount of what circulates about Canso is approximate, outdated, or marketing-rounded. The MLS
verbatim marketing numbers 45.1, 87.9, and 98.1 are reproduced exactly as published, because testing against
the real claims — including the unreachable 45.1 — is the honest course. The Cyclone-4M User's Guide pad
coordinates 45.3 North, 61.0 West are the reference coordinates for hand calculations. The EA facts — Class I
assessment approved 4 June 2019, maximum 8 launches per year, launch hours 07:00 to 12:00 local, all
trajectories south over the Atlantic, a 3-sigma ocean corridor, and CARs 602.43 and 602.44 — are verified
against the assessment documents and the statute source. Alternate coordinates seen in secondary sources,
specifically 45.3036 North 60.9829 West and 45.3223 North 61.7076 West, are recorded rather than suppressed,
with the first essentially coinciding with the EA variant and the second being a coarser regional reference;
recording all three with provenance is more credible than pretending only one exists. The Cyclone-4M Ascent
Unit Guidance azimuths 118.5, 180, and 181 degrees are VERIFIED against the User's Guide, while the
time-to-injection value of 540 seconds is flagged as an ASSUMPTION because no published source states the
powered-flight duration for a Canso ascent profile and the number must therefore be retired by measurement or
by vendor confirmation. The ledger references are Sections A.4 and A.9 of `C2_prior_art_and_track.md`. The
general principle worth stating on slides is that every site or vehicle number in our system travels with a
VERIFIED-or-ASSUMPTION flag in its provenance block, so a judge can see at a glance which numbers are surveyed
facts and which are placeholders awaiting retirement.

### 3.6 Weather and probabilistic launch commit

The weather literature is where probability enters launch operations, and it is essential background for our
probabilistic layer. The 45th Weather Squadron and its Applied Meteorology Unit developed the
Probability-of-Violation (PoV) methodology, documented in NTRS reports 20100021378, 20130010089, and
20120015454, which computes for each individual launch-commit constraint — electric field, cloud thickness,
temperature, winds aloft, and others — the probability that the constraint will be violated given current
observations and short-term forecasts. Per-constraint is the key phrase: PoV answers "what is the chance the
field-mill rule is violated" rather than "what is the chance we launch," and combining per-constraint
violations into an overall go probability requires modelling their joint dependence, which is part of what our
Hidden Markov Model layer in Section 5.5 addresses. The Lightning Launch Commit Criteria (LLCC) overview in
AMS paper 103803 quantifies the operational stakes: lightning-commit violations account for roughly a 5
percent scrub rate and contribute to roughly a 35 percent delay rate, with per-delay costs in the 150,000 to
1,000,000 dollar band — numbers that motivate the entire delay-cost layer of Section 5.2, because they convert
probabilities into dollars. The Goetz Air Force Institute of Technology thesis provides 1989-to-1998
climatology for the Cape, the field-mill Green/Red climatology in arXiv paper 2403.07016 shows how
electric-field climatology is constructed, the Dass, Rodriguez, and Chittenden 2024–2025 AMS conference papers
represent the current state of operational lightning forecasting, the Shuttle Lightning Launch Criteria
document archived as 167476main is the historical root of the modern rules, the Falcon 9 Crew fact sheet and
the 2025 Falcon 9 User's Guide give the modern commercial reference points including a 4-hour
propellant-service window and a 15-second instantaneous window that illustrate how tight real windows can be,
the Decker and Leach 2005 Jimsphere paper documents balloon-measured wind profiles used for day-of loads
assessment, NTRS 20070013713 covers related commit-criteria analysis, and the Starlink loss event of 3–4
February 2022 — in which a geomagnetic storm inflated the upper atmosphere and doomed freshly deployed
satellites — is the cautionary case that space weather belongs in any complete risk picture. The compendium
references are Sections B, D.3, and F of the science document. The lesson for our project is that the
launch-commit community has excellent per-constraint, day-of methodology and essentially no orbit-coupled,
forecast-horizon, hindcast-validated synthesis — which is exactly the synthesis our engine provides.

### 3.7 Climatological availability: APRA and PACER

The Marshall Space Flight Center's APRA (Applied Probability of Range Availability) and PACER tools, published
as AMS 2008 Paper 133849 and NTRS 20080013555, are the closest prior art to our availability climatology and
therefore deserve a careful explanation of what they do and where they stop. APRA and PACER compute
climatological probability of constraint violation by month and hour of day, converting years of historical
observations into a Go-probability table: a planner can look up, for example, the historical fraction of
January 09:00 windows that violated the temperature or wind constraint. That is genuinely useful — it is the
climatological baseline against which any forecast system must prove skill, and our Section 5.3 conjecture on
skill is defined relative to exactly this kind of baseline. But three limitations define our contribution
boundary. First, APRA and PACER are internal tools with no public API, so no external planner can query them
programmatically. Second, they are climatology-only: they answer the historical-average question and cannot
ingest next week's ensemble forecast, so they cannot distinguish a benign Thursday from a stormy one within
the same month-hour bin. Third, they are not orbit-coupled: their probabilities are per-constraint
climatologies rather than probabilities that a specific target orbit's specific window is launchable. A
telling detail from a 2008 requirements document is that conditional day-after probability — the probability
of launching tomorrow given a scrub today, which is precisely what a planner معن needs during a campaign — is
named as an UNMET requirement, meaning even the internal tooling community recognised the gap. Related
analyses include the SLS Monte Carlo wind-availability studies and the Orion EFT-1 sea-state analysis, with
references in Section A.6 of the ledger. Our engine's forecast-coupled, orbit-specific, hindcast-scored
probability is the synthesis these tools point toward but do not themselves provide.

### 3.8 The skill horizon: the forecast-versus-climatology rule

One of the most important quantitative rules in our system is also one of the simplest to state: use numerical
weather forecasts for horizons of 10 days or less, and climatology beyond. This is the
FORECAST-versus-CLIMATOLOGY rule, and it exists because weather forecasts lose skill with lead time until they
become no better than historical averages — at which point presenting a forecast-derived probability is
dishonest precision. The theoretical foundation is Lorenz's 1982 predictability work, which established the
approximately two-week limit on deterministic atmospheric predictability arising from chaotic error growth:
beyond about fourteen days, the atmosphere's sensitive dependence on initial conditions means any specific
forecast is no more informative than climatology. The empirical refinements pin down where the crossover
happens in practice. The Tellus A 2013 paper at DOI 10.3402/tellusa.v65i0.19022 shows ensemble-mean skill
decaying toward climatology around day 10. The Buizza–Leutbecher QJRMS 2015 analysis extends the window to
16–23 days for certain large-scale patterns but confirms the rapid skill decay in the first ten days. The
ECMWF verification statistic that anomaly correlation reaches 71 percent at around 9 days over the Northern
Hemisphere is the operational community's standard skill threshold crossing. Our team rule splits the
difference conservatively: FORECAST for d less than or equal to 10 days, CLIMATOLOGY beyond, with the
references in Sections D.1 and D.2 of the science compendium. The honesty payoff is direct: a dashboard that
shows forecast probabilities at day 20 is fabricating confidence, while one that switches to climatology and
labels the transition is telling the truth about what is knowable. The skill-horizon conjecture of Section 5.3
and the Brier skill scoring of Section 4.5 exist to verify this rule empirically rather than merely asserting
it.

### 3.9 Data sources

The engine's live-data feeds, detailed in Section 9, rest on four primary sources whose roles a newcomer
should understand now. Open-Meteo provides a 16-day deterministic and ensemble forecast API plus a historical
archive API with data since 2021; it is keyless, generous, and the backbone of our short-range forecast
probabilities and our hindcast archive. ECCC, Environment and Climate Change Canada, provides the Canadian
sovereign sources: dd.weather.gc.ca (the Datamart) and api.weather.gc.ca (GeoMet), serving the Global
Deterministic Prediction System (GDPS) at 15 km resolution with a 10-day horizon; these are the nationally
authoritative model outputs for Canadian territory and the natural complement to the global Open-Meteo feed.
ERA5, the European Centre's fifth-generation reanalysis accessed through the Copernicus Data Store, provides
hourly data at 0.25-degree resolution stretching back to 1940; a reanalysis, for the newcomer, is a
retrospective fusion of observations with a fixed modern weather model, producing the best-estimate historical
atmosphere that serves as our climatology and our hindcast truth. GEFS, the American Global Ensemble Forecast
System, serves as the fallback ensemble when primary feeds are unavailable. Together these four sources cover
the forecast horizon, the climatological baseline, the sovereign Canadian requirement, and the redundancy a
viable operational service needs.

### 3.10 Cost and manifesting literature

The delay-cost and manifesting literature is published and directly relevant, but it addresses a different
question from the window-intersection problem, which is why we cite it as the path to full marks rather than
as prior art that pre-empts us. The O'Neill–Davidheiser paper at DOI 10.2514/1.a36618 provides the delay-cost
model we adopt: it converts a probability distribution over launch dates into an expected cost by pricing each
day of delay, which is what turns our ranked date list into a cost-optimal recommendation and what carries our
Originality and Significance rows from 4 to 5. The STAR work by Levinson and colleagues in 2025, the Colombi
paper at DOI 10.2514/1.a33796, and the Hwang paper at DOI 10.2514/1.a36124 address manifesting, scheduling,
and related optimisation formulations. The ledger reference is Section A.5. The key distinction for slides is
that this literature prices delays and schedules manifests given assumed launch opportunities, whereas our
engine computes the opportunities themselves from orbital mechanics coupled to weather; the two compose rather
than compete, and our contribution is the composition — opportunity probabilities feeding a published cost
model — applied openly to Canso for the first time.

### 3.11 Early landscape context (not C2 core)

For completeness and to prevent confusion when browsing the repository, several early-research documents
provide landscape context but are not part of the Challenge 2 core and must not appear on methodology slides
unless a judge explicitly asks about project history. The seven-field Earth-observation screening in
`F4_scientific_opportunity_landscape.md` and `mission-accepted-deep-research.md`, the Phase-3 four-survivor
Gates A through D analysis in `survey/mission-accepted-phase-3/question.md`, the Directions 1 through 3
exploration in `THREE_DIRECTIONS.md` and `research-prompts/README.md`, the physics-constraint falsifier based
on a differentially-constrained neural-network stream function in `OUR_DIRECTION_PHYSICS_RESEARCH.md`, and the
top-5 RCM, Orbits, and Wind shortlist in `TOP_5_PROBLEM_STATEMENTS.md` all predate or parallel the Challenge 2
focus and informed our thinking without contributing equations, data, or validation to the engine. A newcomer
who stumbles on these should read them as evidence of thorough exploration, not as dependencies of the build.

---

## 4. Our Methodology

Our methodology is a deterministic core plus a probabilistic layer plus pre-screens, with the full authority
in Part II (sections II.0 through II.10) of the build specification. The architecture is deliberately layered
because each layer answers a different planner question and fails independently: the deterministic core
answers "when does geometry permit launch," the probabilistic layer answers "how likely is each permitted date
to actually go," and the pre-screens answer "is there any categorical reason — safety corridor, orbital
traffic, airspace notice — to remove this date regardless of geometry and weather." A newcomer should think of
the pipeline as a funnel: dates enter, geometry admits a subset, screens remove a further subset, and
probabilities rank the survivors. Every equation below is implemented in the shipped engine, tested by the
suites of Section 7, and explained here in words with each symbol defined on first use.

### 4.1 Reachability: which inclinations can Canso reach at all

The reachability test is the first gate in the funnel and the simplest to understand, but its Canso
consequence is our most striking single result. Formally, we define a predicate reachable(i) that is true if
and only if there exists an azimuth beta within the permitted corridor [Amin, Amax] such that cos(i) =
cos(phi) * sin(beta). Here i is the target inclination, phi is the site latitude (45.3 degrees for the rounded
Canso reference), beta is the launch azimuth measured clockwise from north, and Amin and Amax are the corridor
bounds, defaulting to Amin = 90 degrees (due east) and Amax = 200 degrees (just west of due south). In words:
an inclination is reachable exactly when the spherical-geometry equation of Section 3.1 has a solution whose
compass heading lies inside the south-facing safety fan. The defaults encode the all-south Atlantic
range-safety design: nothing launches north over land, and the fan from east around through south to
slightly-west-of-south keeps all ascent ground tracks over water.

The Canso consequence is immediate and must be worked through numerically because it is the centrepiece of our
honesty narrative. Substituting the LEO marketing inclination i = 45.1 degrees and the site latitude phi =
45.3 degrees gives sin(beta) = cos(45.1°)/cos(45.3°) = 1.0035, which exceeds 1 and therefore has no real
solution for beta: no compass heading, inside or outside the corridor, puts a direct ascent from Canso into a
45.1-degree plane. The engine consequently returns reachable:false with an empty window list — a priced
refusal, not an error — together with the plane-change delta-v that would repair the mismatch. A plane-change
delta-v, for the newcomer, is the propulsive velocity change needed to rotate the orbital plane after
insertion; a dogleg is the related in-atmosphere manoeuvre in which the rocket turns during ascent to achieve
part of that rotation, at the cost of performance and corridor complications. Our priced refusal uses the
impulsive plane-change formula dv = 2 * vc * sin(di/2), where vc is the circular orbital velocity
(approximately 7.67 km/s in low Earth orbit) and di is the required plane rotation (here 0.2 degrees, the
latitude-minus-inclination shortfall). Substituting gives 2 * 7670 * sin(0.1°) ≈ 26.8 m/s, engine-verified as
26.768 m/s. Twenty-seven metres per second is small against a launcher's total budget but large against a
precision-insertion margin, and quoting it converts an apparent failure ("your engine found no window") into
demonstrated competence ("your engine proved no direct window exists and priced the fix"). The spec references
are II.2 through II.4.

Why does the default corridor run from 90 to 200 degrees rather than some surveyed polygon? Because, as
established in Section 2.1, the EA contains no numeric corridor — Figure 2.9 is an unlabelled schematic — so
any numeric bound we use is necessarily an assumption. We chose the widest defensible south-facing fan, due
east around through south to 200 degrees, and flagged it ASSUMPTION with full provenance, so that replacing it
with surveyed coordinates the moment they become available is a one-line data change rather than a code
change. That assumption-retirement path is tracked in Section 10.

### 4.2 Canso launch azimuths: the three headings the engine stands behind

For each reachable target inclination the engine computes the required launch azimuth — the compass heading
the vehicle must initially fly — and our three Canso numbers are engine-verified to two decimal places. From
Canso, the 87.9-degree Polar-lower-bound target requires an azimuth of 177.0 degrees (verified 177.01), the
exact-polar 90-degree target requires 180 degrees due south (verified 180.00), and the 98.1-degree SSO target
requires 191.6 degrees (verified 191.56). In words: near-polar missions launch almost due south with a slight
eastward or exactly-south heading, while the retrograde SSO mission launches south-southwest, tilted about
11.6 degrees west of south to build in the westward component that a retrograde orbit demands.

Two properties of these numbers are slide-worthy. First, the 87.9-degree case needs no dogleg: its 177-degree
azimuth lies comfortably inside the 90-to-200 corridor, so the vehicle flies a clean southerly ascent with no
in-flight plane rotation. This is falsification (b) of Section 6 — the demonstration that at least one Polar
target is reachable with a simple, corridor-compliant heading, which rebuts any suspicion that our
reachability analysis is tuned to refuse everything. Second, the progression 177.0 → 180.0 → 191.6 with
increasing inclination is exactly the monotonic behaviour the spherical-geometry equation predicts, which is a
built-in sanity check: had the engine returned, say, 150 degrees for the SSO case, the non-monotonicity would
have flagged a sign error without any external reference. The spec references are II.2 through II.4, and the
azimuth derivation history is in `C2_science_hunt.md`.

### 4.3 Window search: from node alignment to clock time

The window search is the heart of the deterministic core: it converts the abstract requirement "launch into
plane Omega_t" into concrete clock times a planner can put on a calendar. The governing equation is GMST +
lambda = Omega_t + delta, where GMST is Greenwich Mean Sidereal Time (the angle of Earth's rotation measured
against the fixed stars rather than the Sun, which advances about 0.9856 degrees per day faster than solar
time because Earth orbits while it spins), lambda is the site's east longitude (negative 61.0 degrees for
Canso, i.e., 61 degrees west), Omega_t is the target Right Ascension of Ascending Node, and delta is the
geometric offset asin(tan(phi)/tan(i)) — the arcsine of the ratio of the tangent of the site latitude to the
tangent of the target inclination. In physical words: the left side is the site's current celestial longitude
(rotation angle plus geographic position), the right side is the target plane's node plus a correction for the
fact that the site is generally not under the node at the moment of alignment, and a window occurs whenever
Earth's rotation brings the two sides into equality.

Because Earth rotates at the sidereal rate of 15.0411 degrees per hour while the target node itself drifts at
the J2 rate Omega_dot (negative ~5.14 degrees per day for our LEO reference, positive ~0.9856 for SSO), the
two sides sweep past each other at a known relative rate, and the window half-width tau_half — half the
duration of the open window — equals the tolerable node error DeltaOmega divided by the magnitude of that
relative rate, |15.0411 − Omega_dot| in degrees per hour. The worked example we hand-check against is: a tight
tolerance of ±0.1 degrees gives a window of about 24 seconds, while a loose tolerance of ±5 degrees gives
about 40 minutes. The 24-second number is worth memorising because it conveys instantly to judges how
demanding precision insertion is: the difference between a direct injection and a costly correction burn can
be half a minute of clock time. The recurrence period P — how long before the same geometry repeats — is
360/(360.9856 − Omega_dot) in days, which evaluates to 0.9973 days (essentially one sidereal day) for
fixed-inclination targets whose nodes drift slowly, and exactly 1 solar day for SSO targets whose nodes are
defined to track the Sun. The spec references are II.3 and II.4.

For the newcomer, RAAN deserves a fuller gloss since it appears everywhere. The Right Ascension of Ascending
Node is the celestial longitude of the point where the orbit crosses the equator going north, measured
eastward from the vernal equinox direction. It fixes the swivel of the orbital plane around Earth's axis:
inclination fixes the tilt, RAAN fixes the swivel. Launch-window analysis is, at its core, the problem of
predicting when Earth's rotation will carry the launch site into the target swivel — and, for SSO, when it
will do so at the right local solar time.

### 4.4 The injection-consistent fixed point (Track 1 bonus: Vehicle Duration)

The Track 1 bonus — Vehicle Duration, the distinction between the injection-point time and the liftoff-moment
time — is implemented as an injection-consistent fixed-point solve, and this subsection explains what that
means and why a naive approach fails. The naive approach computes the node alignment for the instant of
liftoff and declares that the window. But the rocket does not reach orbit at liftoff: it flies a powered
ascent lasting roughly 540 seconds (our flagged assumption for Cyclone-4M), during which Earth rotates
eastward by about 2.25 degrees and the target node precesses by its J2 rate, so the plane the vehicle actually
enters is the plane as it stands at injection, not at liftoff. Ignoring this is equivalent to aiming at where
a moving target is now rather than where it will be when the arrow arrives — a small error for short ascents,
but a systematic one that corrupts precision-insertion claims and that the challenge explicitly asks us to
handle.

Our solve defines the residual function g(t) = wrap[GMST(t) + lambda − delta − Omega_t(t + T(t))], where t is
the candidate liftoff time, T(t) is the ascent duration (540 s nominally, altitude- and profile-dependent in
general), Omega_t evaluated at t + T(t) is the target node at the injection instant rather than at liftoff,
and wrap maps the angular error into the [−180, +180] interval so that the solver sees a continuous signed
error rather than a 359-versus-0 discontinuity. The fixed point is the liftoff time t at which g(t) = 0 — the
time such that launching then puts the vehicle into the plane as it will be at injection. We solve it by
relaxation and Newton iterations with a Brent bracket fallback: relaxation iterates t ← t − g(t)/rate until
convergence, Newton uses the analytic derivative for quadratic convergence near the root, and Brent provides
the guaranteed bracketed fallback if the iterates ever leave the bracket. The engine reports four quantities
per window: t_liftoff (the answer the planner sets the countdown to), t_injection (liftoff plus ascent
duration), shift_s (the signed correction in seconds between the naive liftoff-node solution and the
injection-consistent one), and liftoff_error_min (the residual expressed in minutes for human inspection). Our
verified injection shifts of +1.48 and −0.40 seconds on the test cases are small — which is itself a result,
because it quantifies rather than hand-waves the ascent effect for this vehicle — and the contraction analysis
of Section 5.1 proves the iteration converges. The spec reference is II.5.

### 4.5 The weather and probability layer: from constraints to P(success | date)

The probabilistic layer converts the deterministic window list into a ranked recommendation by estimating, for
each candidate date, the probability that launch actually succeeds. Its logical structure has four stages,
each with its own equation, and a newcomer should master the inputs and outputs of each before worrying about
implementation details.

Stage one is the launch-day predicate L(d), which equals 1 if and only if the weather constraints W hold over
the window interval I(d) on date d, and 0 otherwise. The constraints W are the familiar commit criteria —
surface winds below the vehicle limit, no lightning within the standoff distance, cloud-thickness and
temperature rules satisfied, visibility above minimum, sea state within the recovery or hazard tolerance — and
the interval I(d) is the deterministic window computed by the core for that date. The predicate is binary and
deterministic given a weather realisation: either every constraint holds through the whole window, or the date
scrubs.

Stage two is the forecast probability P_forecast, which handles the fact that future weather is uncertain. For
horizons within the 10-day skill horizon, we use ensemble prediction: P_forecast = (1/N) Σ 1{member passes W},
the fraction of the N ensemble members whose forecast weather satisfies all constraints over the window
interval. In words, if 34 of 50 ensemble members keep winds, lightning, and clouds within limits through the
window, the forecast probability is 0.68. The ensemble spread is doing the uncertainty quantification for us:
confident forecasts have members in agreement, uncertain ones do not, and the member fraction converts that
agreement into a calibrated probability without any parametric assumptions.

Stage three is the climatological probability P_clim(month, hour), used beyond 10 days where forecasts have no
skill. It is the historical fraction of past window intervals in the same calendar month and hour-of-day bin
whose reanalysis weather satisfied the constraints — the APRA/PACER-style number, but computed openly for
Canso from ERA5 and ECCC archives. Its honesty function is as important as its numerical function: reporting a
climatological 0.61 with a label that says "climatology, no forecast skill at this horizon" is truthful, while
reporting a forecast-derived 0.613 at day 25 would be fabricated precision.

Stage four combines the weather probability with the two non-weather success factors: p_success = P_weather ×
P_range × P_conj. Here P_weather is the forecast or climatological probability from stages two and three,
P_range is the probability the range is available (no conflicting operation, no unresolved hazard-area
closure, crew and systems ready), and P_conj is the probability of no conjunction veto — no predicted close
approach with a catalogued object that would force a hold. Multiplication is justified under the working
assumption that weather, range, and traffic blockers are approximately independent day-to-day failure modes;
the chance-constrained formulation of Section 5.2 states the exact assumptions (exchangeability, stationarity,
independence) under which the product is the correct joint probability, and the SKETCHED tier marking records
that these assumptions are reasonable rather than proved.

Verification closes the loop: we score the probabilities with the Brier score BS, which is the mean squared
error between forecast probabilities and binary outcomes (0 for scrub, 1 for launch), and the Brier skill
score BSS = 1 − BS/BS_ref, where BS_ref is the score of the climatological reference forecast. A BSS above
zero means our forecast-coupled probabilities beat the historical average — the conjecture C1 of Section 5.3 —
and we supplement it with reliability diagrams (predicted probability versus observed frequency in each
probability bin, which should lie on the diagonal for a calibrated system) and ROC curves per lead time (which
show the trade-off between hit rate and false-alarm rate as the go/no-go threshold varies). The spec reference
is II.7.

### 4.6 Screens: corridor, conjunction, and airspace pre-filters

Before probabilities are computed, three pre-filters remove dates that are categorically unacceptable
regardless of geometry or weather. They are called screens because they screen out rather than rank: each
returns a binary pass/fail, and a fail removes the date with a stated reason. The first is the ground-track
and footprint screen: the computed ascent ground track and its debris footprint are tested against the
corridor polygon, returning 1 for contained and 0 for violating. Because the EA provides no numeric corridor,
the polygon currently used is the assumption rectangle A_min 90 to A_max 200 degrees documented in Section 4.1
— an honest placeholder that keeps the pipeline testable while advertising exactly what must be retired with
surveyed data. The second is the conjunction pre-screen: catalogued-object state vectors from CelesTrak TLEs
(Two-Line Element sets, the standard orbital-element format propagated by the SGP4 simplified-perturbations
propagator) are screened for predicted miss distances below the safety threshold during the ascent and
early-orbit phase; a predicted violation vetoes the date. The third is the NavCanada NOTAM screen, which is
display-only: Notices to Airmen affecting the launch airspace are shown to the planner but do not
automatically veto, because airspace coordination is a human decision involving lead times and exemptions that
an engine should inform rather than pre-empt. The spec reference is II.8.

### 4.7 The validation plan

The validation plan in Part III of the specification is the contract between our claims and our evidence, and
a newcomer should read it as the definition of "done" for every subsystem. The unit checks require:
reproducing the SSO inclination-versus-altitude table to 0.01 degrees, which pins the J2-plus-SSO chain;
reproducing the three engine azimuths 177.01, 180.00, and 191.56 degrees, which pins the
reachability-plus-geometry chain; reproducing the J2 drift of −5.14 degrees per day at 600 km and 45.1 degrees
inclination within 1 percent, which pins the perturbation chain; and reproducing the 24-second hand-check
window for a ±0.1-degree tolerance, which pins the rate arithmetic. The hour-12 gate in Section III.2 is the
integration milestone with teeth: before any frontend work proceeds on real data, the engine must reproduce 3
to 5 published launch windows within 5 minutes of their documented times. Five minutes is the tolerance
because it is tighter than any plausible accumulation of rounding but looser than the tens-of-seconds
precision that would demand proprietary ascent profiles we do not have; passing it proves the engine is
anchored to reality rather than to its own assumptions. The skill requirement is BSS above zero versus the
climatology reference — the minimum viable evidence that the probabilistic layer adds information. The honesty
requirement is that the 45.1-degree case returns reachable:false with an empty window list and HTTP 200
semantics (a successful computation of unreachability, not a server error), because fabricating a window for
an unreachable target would be the single most discrediting thing the engine could do. The determinism
requirement is byte-identical numerics across runs except for the excluded wall-clock field computation_ms, so
that any result can be reproduced exactly. The constants and provenance-echo requirement is that every
response carries the constants and the VERIFIED/ASSUMPTION flags that produced it, so that no number ever
appears without its lineage. The risks and plumbing analysis in Section 0 and Part VIII records what can still
go wrong — feed outages, key management, corridor-data absence — and the API surface of Parts IV and V fixes
the five endpoints `/v1/windows`, `/v1/series`, `/v1/offsets`, `/v1/tube`, and `/v1/validation/skill`, each
documented with its request and response schema so that weather, API, and frontend owners can build against
frozen contracts.

### 4.8 Process: how the methodology is executed

Methodology without process is a wish list, so this subsection records how the work is actually done. The
framework-as-experiment-loop means every claim passes through propose, implement, test, validate, and audit
before it is merged — there is no direct path from idea to slides that bypasses the test suites. The ENGINE
seam is the function signature `compute_windows(request) -> dict`, accompanied by `probability()` and
`hindcast()` for the probabilistic stages; the JSON Schemas in `tests/contract/` freeze the request and
response shapes, and a fixture-based demo floor guarantees that the dashboard always has valid data to render
even when live feeds are down. The engine was built by test-driven development over work items E0 through E12
with a 70-test contract gate, meaning each capability was specified as a failing test before it was
implemented — the 723-line TDD log in `backend/engine/progress.md` is the complete record.
Apparent-versus-mean Sun handling corrects for the Equation of Time (up to 4 degrees, or 16 minutes of time,
between the true Sun that drives SSO lighting and the mean Sun that drives clock time), and the G1 green
anchors are the published-window reproductions that pin the engine to reality. The audit lessons applied
throughout are: citation checking (every number traces to a source), tolerance discipline (tolerances are set
by physics and locked by tests that fail if widened), dead-code mutant testing (candidate code that the tests
cannot kill is removed), and dual-exit solver discipline (every iterative solver has both a convergence exit
and a bounded-failure exit, so no solver can hang the pipeline).

---

## 5. Advanced Maths / ML / Stats / Physics

This section teaches the advanced claims the way a teammate with no prior exposure would need them taught:
each item states the idea in plain language, explains the mathematics or the model structure with every symbol
defined, says why the step exists in our pipeline, and states its claim tier. Claim tiers follow Section II.9
of the specification, whose venue note names Acta Astronautica as the target journal standard — meaning our
PROVED items must meet the standard of a peer-reviewed aerospace proof, our SKETCHED items must state their
assumptions explicitly enough that a reviewer could complete them, and our CONJECTURE items must be framed as
testable predictions with named verification procedures rather than as established facts. Every tier is marked
in code as PROVED, SKETCHED, or CONJECTURE, so the tier travels with the implementation and cannot drift in
retelling.

### 5.1 PROVED items: the contraction and the reachability algebra

Item (i) is the contraction proof for the injection fixed-point map, and it deserves a full teaching
exposition because fixed-point theory is the kind of mathematics judges respect only when they see you
understand its hypotheses. The claim is that the relaxation iteration for the injection solve converges to a
unique root. The mathematical instrument is the Banach fixed-point theorem, which says: if a map Phi maps a
complete interval into itself and is a contraction — meaning there exists a constant q < 1 such that |Phi(a) −
Phi(b)| ≤ q|a − b| for all points in the interval, so that every application shrinks distances by at least the
factor q — then repeated application from any starting point converges to exactly one fixed point, and the
distance to that point shrinks geometrically. The contraction factor is bounded by the supremum of the
derivative: q = sup|Phi'|, so proving |Phi'| < 1 uniformly is the whole game.

For our injection map, the derivative works out to |Phi'| = |Omega_dot × (1 + dT/dt)| / |omega_sid −
Omega_dot|. In words: the numerator is the target-node drift rate Omega_dot (degrees per day from J2, Section
3.2) multiplied by one plus the sensitivity of the ascent duration to the liftoff time dT/dt (which is near
zero because ascent duration barely depends on when during the morning you launch); the denominator is the
relative sweep rate between Earth's sidereal rotation omega_sid (15.0411 degrees per hour, Section 4.3) and
the node drift. Because the denominator is dominated by Earth's fast daily rotation while the numerator
contains only the slow nodal drift, the ratio is tiny: numerically approximately 0.017, engine-verified as
0.014024 on the test cases against the 0.017 bound. A contraction factor of 0.017 means each iteration kills
roughly 98 percent of the remaining error — convergence in a handful of steps from any start, with uniqueness
guaranteed by Banach. The honest note, which we state on slides rather than hiding, is that the proof as
written covers the relaxation map, while the shipped code uses bisection over a bracketed interval, which
carries a strictly stronger guarantee (bisection converges for any continuous sign-changing function with no
derivative condition at all). The proof therefore understates rather than overstates the code's reliability,
which is exactly the direction honesty should point.

Item (ii) is the reachability interval algebra: the admission condition |cos(i)/cos(phi)| ≤ 1. This is the
equation cos(i) = cos(phi)·sin(beta) of Section 4.1 rearranged: since |sin(beta)| ≤ 1 for any real heading, a
solution exists exactly when the ratio |cos(i)/cos(phi)| does not exceed 1. It is marked PROVED because it is
a two-line consequence of the boundedness of the sine function with no modelling assumptions — the kind of
airtight lemma that anchors the priced-refusal semantics. Its pipeline function is to make unreachability a
theorem rather than a numerical accident: the 45.1-degree refusal follows from 1.0035 > 1 by pure algebra,
independent of tolerances, grids, or solver settings.

### 5.2 SKETCHED items: chance-constrained formulation and opportunity thinning

Item (iii) is the chance-constrained formulation of the window-selection problem. An ordinary constrained
optimisation demands that constraints hold deterministically: |g| ≤ DeltaOmega (the node error within
tolerance), beta inside the corridor, hazard flag equal to 1 (clear). A chance-constrained formulation
recognises that weather and range inputs are random and instead demands P(success) ≥ p*, meaning the
probability of the constraint set holding must exceed a planner-chosen confidence level p* — for example,
launch only on dates with at least 70 percent modelled success probability. The sketch states the three
assumptions under which our product-form probability of Section 4.5 is the correct joint probability:
exchangeability (the ensemble members are symmetric draws, so the member fraction estimates the true
probability), stationarity (the climatological statistics are stable across the years pooled into each
month-hour bin), and independence (weather, range, and conjunction blockers fail independently so their
probabilities multiply). Each assumption is reasonable for a first operational system and each is named so
that a reviewer — or a teammate extending the work — knows exactly what would need relaxing for version two,
for instance by modelling weather-range correlation during major storms. SKETCHED is the right tier: the
formulation is standard stochastic-programming practice and the assumptions are explicit, but the full
measure-theoretic proof with our specific constraint predicates is outlined rather than completed.

Item (iv) is opportunity thinning with expected-cost planning: E[T_next] = Σ (1 − Π (1 − p)) for the expected
waiting time to the next launchable date, and E[cost] = C_day × (E[T] − T_nom) for the expected delay cost. In
words: if each candidate date d has success probability p_d, the probability that at least one date in a set
goes is one minus the product of the individual scrub probabilities, and summing the complementary tail over
successive dates gives the expected time to the next success — the standard thinning of a Bernoulli
opportunity process, where a Bernoulli trial is simply a success/fail coin flip per date and thinning means
keeping each date with its probability. Multiplying the expected excess wait (expected time minus the nominal
earliest date T_nom) by the per-day delay cost C_day prices the schedule risk in dollars. The cost model plugs
in the published O'Neill delay-cost model at DOI 10.2514/1.a36618, which supplies the C_day parameterisation
from the launch-economics literature rather than from our invention. The pipeline function is the planner's
bottom line: instead of "here are ten dates with probabilities," the dashboard can say "launching no earlier
than Thursday minimises expected cost at the following dollar figure," which is the sentence that converts
Significance from 4 to 5.

### 5.3 Conjectures C1 through C4: testable predictions, not facts

The four conjectures are predictions with named verification procedures, and the discipline of listing them as
conjectures rather than results is itself a credibility signal. Conjecture C1 states BSS > 0: our
forecast-coupled probabilities will score a positive Brier skill score against the climatology reference on
the hindcast set, meaning they add genuine information beyond historical averages. Conjecture C2 states the
skill horizon is approximately 10 days: BSS computed per lead time will cross zero near day 10, empirically
confirming the Section 3.8 rule rather than merely citing textbooks. Conjecture C3 states the bounded-negative
result shape: when the system fails on individual dates, the failures will be bounded and negative — small
probability errors in the pessimistic direction rather than confident wrong predictions — which is the safe
failure mode for a decision aid. Conjecture C4 states proxy-LCC validity: our openly computed proxy lightning
and commit constraints will correlate with the proprietary Lightning Launch Commit Criteria outcomes closely
enough that the proxy is decision-useful, which is what allows an open system to stand in for closed
operational rules. Each conjecture names its verification — hindcast BSS, per-lead skill curves, reliability
diagrams, proxy-versus-record correlation — so that confirming or refuting them is mechanical rather than
interpretive.

### 5.4 SSO LTAN coupling and the J2 rule

The SSO Local Time of Ascending Node coupling is Omega_req = alpha_sun + 15 × (TLT − 12h). Here Omega_req is
the required RAAN of the target plane, alpha_sun is the Sun's right ascension (the celestial longitude of the
Sun, advancing ~0.9856 degrees per day), TLT is the target local time of the ascending node in hours (for
example 10.5 for a 10:30 AM crossing), and the factor 15 converts hours of local-time offset into degrees of
Earth rotation. In words: the node must sit ahead of the Sun by exactly the local-time offset converted to
angle, so that when the satellite crosses the equator going north, clocks on the ground below read the desired
local time. Two subtleties matter operationally. First, altitude-specificity: because the SSO inclination
depends on altitude (Section 3.2), the LTAN condition and the inclination condition must be satisfied jointly
— picking an altitude fixes both the required tilt and, through the node rate, the phasing maintenance.
Second, LTAN drift: real SSO missions drift by about 6 minutes of local time per year for each 0.01 degree of
inclination error, because a slightly wrong inclination gives a slightly wrong nodal rate and the Sun-plane
angle walks off. Our engine carries this drift so that multi-month campaigns see the window times migrate
realistically rather than sitting frozen.

The J2 rule is stated once more because violating it once cost us a draft cycle: the correct drift is −5.14
degrees per day at 600 km and 45.1 degrees inclination — never hard-code a drift constant anywhere, always
compute it from the GDC equation — and 3.99 degrees per day is WRONG. The rule exists in this section because
LTAN coupling consumes J2 rates: an SSO node rate computed from a wrong J2 constant would silently misplace
every dawn-dusk phasing by compounding daily errors, which is precisely the class of silent corruption our
provenance-echo and literal-grep discipline (Section 7) is designed to make impossible.

### 5.5 The statistics and machine-learning layer

The stats-ML layer turns raw weather and traffic data into the calibrated probabilities the planner sees, and
each component below is explained as a teacher would explain it: what it models, what its parameters mean, and
why it belongs in the pipeline. The Hidden Markov Model (HMM) for G/Y/R weather states models the
launch-weather regime as a hidden discrete state — Green (all constraints satisfied with margin), Yellow (one
or more constraints near limits), Red (a constraint violated) — that evolves as a Markov chain (tomorrow's
regime depends on today's, capturing frontal passages and storm persistence) while emitting observable sensor
and model outputs probabilistically. The HMM matters because launch weather is regime-like rather than
smoothly varying: a frontal passage flips conditions categorically, and a model that tracks regimes produces
sharper, better-calibrated Green/Yellow/Red lights than one that thresholds instantaneous values. The ensemble
Probability-of-Violation (PoV) extends the 45WS per-constraint violation probability of Section 3.6 to our
forecast horizon: for each constraint, the fraction of ensemble members violating it estimates its violation
probability, and hindcast calibration maps those raw fractions to observed frequencies so that a stated 0.2
means 0.2 empirically. The wind-triplet Monte Carlo propagates the three-dimensional wind uncertainty (zonal,
meridional, vertical components) through the loads and drift response to estimate the probability of
wind-induced violation — Monte Carlo here meaning simply repeated random sampling of plausible wind profiles
rather than any exotic mathematics. Site-date and storm-block thinking governs verification aggregation: skill
statistics are pooled in blocks (by site, by date, by storm event) rather than over individual window
instances, because windows on the same stormy day are correlated and naive pooling would overstate effective
sample size. Wilson score intervals and cluster-bootstrap intervals quantify the uncertainty on our reported
probabilities and skill scores honestly: the Wilson interval is the correct binomial confidence interval for a
success fraction (unlike the naive normal approximation, it stays within [0,1] and works for small samples),
and the cluster bootstrap resamples whole storm blocks rather than individual windows so that the confidence
bands reflect the true correlated structure of the data.

The top-5 method faces, inherited from `TOP_5_PROBLEM_STATEMENTS.md`, are the three advanced modelling
directions that survived our earlier screening and that extend the shipped baseline. Honest Orbits conformal
tubes wrap trajectory predictions in distribution-free uncertainty bands: conformal prediction takes any point
predictor and a calibration set and returns intervals with a guaranteed coverage frequency (for example, 90
percent of true positions fall inside the 90 percent tube) under only the exchangeability assumption — no
Gaussianity, no linearity. Wind-Band NGBoost with Student-t outputs and conformal calibration models the
conditional distribution of upper-level winds: NGBoost (natural-gradient boosting) fits a full parametric
distribution whose parameters vary with atmospheric predictors, the Student-t distribution provides heavy
tails that respect gust extremes better than a Gaussian, and a conformal layer on top restores exact coverage.
Provenance Guard hierarchical Bayes with Wishart effective-sample-size (ENL) modelling tracks data quality
itself: a hierarchical Bayesian model pools information across feeds while allowing feed-specific biases, and
the Wishart-distributed precision estimate yields an effective number of looks (ENL) — the effective
independent sample size after accounting for correlation — so that the system knows how much to trust each
input. Together these three faces show judges a credible path from the shipped deterministic-plus-ensemble
baseline to a genuinely modern uncertainty-quantification stack, which is why they are summarised here and
detailed in the stats-ML design notes.

---

## 6. Results So Far (EVOLVING)

This section changes as gates land. It is explicitly marked evolving because several of its numbers — the G1
anchor residuals, the gate statuses, the assumption-retirement state — will move as weather, API, frontend,
and integration work lands. Before freezing any slide, re-check `backend/engine/DONE.md`,
`backend/engine/progress.md` (the 723-line TDD log that records every test-driven work item in order), and
`backend/engine/README.md` for the latest state. What follows explains each result: what the number is, how it
was obtained, what it means, and why we report it — including the results that flatter us and the ones that do
not, because honest reporting of misses is itself one of our strongest credibility signals.

### 6.1 Spec complete and integration contract frozen

The specification is COMPLETE and checklist-verified: all eight parts plus appendices of
`C2_framework_and_build_spec.md` are written, cross-referenced, and reviewed. Completeness here means
something concrete: every subsystem owner can build solely from the spec without asking the author clarifying
questions, because interfaces, equations, constants, tolerances, and acceptance criteria are all stated. The
integration contract derived from it defines 4 workflows (engine, weather, API, frontend), 3 seams (the
function and HTTP boundaries where subsystems meet: the engine seam, the weather seam, and the API seam), and
gates G0 through G5 (the six acceptance milestones from frozen schemas to validated integration). Freezing
this contract before building is why parallel development by four owners has proceeded without interface
drift: the schemas cannot change without a contract amendment, so the engine team and the frontend team never
discover at integration time that they disagree about a field name.

### 6.2 Engine issue 2 shipped

ENGINE issue number 2 SHIPPED on 2026-10-04: all TDD work items E0 through E12 are complete, merged over 6
commits on the `engine/issue-02` branch, with the adversarial audit findings fully remediated (the audit is
detailed in Section 7). For a newcomer, "shipped" means the deterministic core — reachability, J2, window
search, injection solve, SSO coupling, screens, frames, provenance — is implemented, tested, reviewed, and
merged, not prototyped. The E0–E12 sequence ran from scaffolding and constants through each physics module to
the published-window reproduction gate, and the 6-commit history shows the review checkpoints. The adversarial
audit verdict was SHIP WITH FIXES, and every fix landed before merge, so the shipped state already
incorporates hostile review rather than awaiting it.

### 6.3 G1 green anchor residuals: what each number means

The G1 GREEN anchor residuals are the engine-minus-published differences on real historical launches,
evaluated against a 5-minute tolerance, and they are the single most important evidence that the engine is
anchored to reality. Each residual is computed by running `compute_windows` over the real launch's date range
with the actual site coordinates and target inclination, taking the computed window centre, and subtracting
the published liftoff time: a residual of −1.545 minutes means our engine predicted a window centre 1.545
minutes before the rocket actually lifted off. The four anchors are: Sentinel-1C from Kourou at −1.545
minutes, EarthCARE from Vandenberg at −0.547 minutes, Sentinel-5P from Plesetsk at +0.914 minutes, and
Sentinel-3C from Kourou at +2.257 minutes. Three of the four sit inside the stricter 2-minute standard of spec
Section III.2, which demands near-coincidence with published times; Sentinel-3C at +2.257 exceeds that
2-minute standard by 0.257 minutes — about 15 seconds — and is recorded as such rather than dropped or rounded
into compliance. All four are inside the 5-minute hour-12 gate tolerance, so G1 is GREEN.

Why do these numbers persuade? Because they are computed against launches our engine never saw during
development, at sites on three continents with different latitudes and target inclinations, using only public
inputs. An engine that reproduces Kourou, Vandenberg, and Plesetsk windows to within a couple of minutes has
no Canso-specific tuning hiding inside it — the physics generalises, which is exactly what must be true before
we trust its Canso predictions. And why report the Sentinel-3C overage openly? Because a judge who discovers a
hidden 15-second exceedance concludes the team cannot be trusted; a team that volunteers it with the exact
figure demonstrates the tolerance discipline of Section 4.8. The residual table is the difference between
claiming accuracy and proving it.

### 6.4 The honesty case: 45.1 degrees returns a priced refusal

The honesty case is the 45.1-degree LEO marketing inclination launched from 45.3 North: the engine returns
reachable:false, plane_change_dv_m_s = 26.768 (against the spec's rounded 26.8), an empty windows list, and
HTTP 200 semantics. Each element of that response is deliberate. Reachable:false states the geometric theorem
of Section 5.1 rather than a numerical failure. The plane-change figure 26.768 m/s prices the repair via the
dv = 2·vc·sin(di/2) formula of Section 4.1, matching the spec's 26.8 to the quoted precision. The empty
windows list refuses to fabricate what geometry forbids. And HTTP 200 — success — rather than an error status
encodes the philosophical point: correctly proving unreachability is a successful computation, and the
dashboard should render it as an explained refusal with the price tag, not as a crash page. This is priced
refusal instead of an error, and it is the behaviour that most sharply distinguishes our engine from a demo
that always returns something plausible-looking.

### 6.5 Engine-verified physics numbers

The physics numbers that follow are engine-verified, meaning each was produced by running the shipped code
rather than by hand calculation, and each is reported with the comparison that gives it meaning. The J2 drift
of −5.1354 degrees per day at 600 km and 45.1 degrees inclination matches the spec's rounded −5.14 and
definitively excludes the wrong 3.99 value — the sign, magnitude, and precision together pin the perturbation
chain. The three azimuths 177.01, 180.00, and 191.56 degrees match the Section 4.2 hand values 177.0, 180, and
191.6 to the quoted precision, pinning the geometry chain end to end. The window width of 47.86894 seconds is
the full open duration for the reference tolerance case — the number a countdown would actually bracket —
reported to five decimals because determinism (Section 7) makes the fifth decimal reproducible rather than
noise. The injection shifts of +1.48 and −0.40 seconds on the two test profiles quantify the Track 1 bonus
effect: small, signed, profile-dependent corrections, exactly as the fixed-point theory of Section 4.4
predicts, and their smallness is itself informative because it bounds how wrong the naive liftoff-node
approximation would have been. The contraction figure 0.014024 against the 0.017 bound confirms the Banach
analysis of Section 5.1 empirically — the iteration contracts faster than the proven worst case, as expected.
The solar apparent-Sun validation to within 0.005 degrees on the four equinox and solstice anchors confirms
the Equation-of-Time handling: at the two equinoxes and two solstices, where the Sun's apparent position is
known analytically, our solar-longitude computation agrees to five millidegrees, which is far tighter than the
arcminute-level accuracy the SSO phasing needs. Together these numbers say: every link in the chain from
constants through perturbations through geometry through solvers reproduces its independent check.

### 6.6 Honestly unreproduced cases: what we could not match and why

The honestly UNREPRODUCED cases are documented in `DONE.md` and in `data/published_windows.json` with reasons,
not hidden — and this subsection explains each one because a newcomer must be able to defend them under
questioning. Sentinel-3A at +24.947 minutes and Sentinel-3B at +7.514 minutes are both unexplained: the engine
runs cleanly and returns windows, but they sit well outside tolerance with no identified cause, possibly
involving unpublished dogleg profiles or plane-change targeting at Plesetsk that our direct-ascent model
cannot reproduce. Landsat-9 at +16.011 minutes carries a documented 30-minute loft explanation: the published
trajectory included an extended coast or lofted profile segment that shifts the effective injection node
beyond our 540-second assumption, and modelling that profile is tracked as assumption-retirement work.
Sentinel-1D at +9.641 minutes traces to a source typo in the published time we ingested — the reference itself
appears wrong, and we record that rather than tuning the engine to match a bad reference. TDRS-M and the GEO
case are circular by construction: geostationary targets have no published RAAN to reproduce because the
requirement is longitude station rather than node alignment, so there is nothing to check against. MetOp-SG-A1
carries coast-phase ambiguity: the published profile's coast duration is underspecified, leaving the injection
epoch uncertain by more than our tolerance. Reporting all seven cases with these explanations is the honesty
policy in action: the engine's validated envelope is stated exactly, the boundary cases are named with causes
where known and flagged as unexplained where not, and no slide may imply a broader validation than this list
supports.

### 6.7 G0 frozen; G2 through G5 not started

G0 is frozen: 8 JSON schemas plus 20 good and 43 bad contract examples, meaning the request and response
shapes for every endpoint are fixed and every known malformed input has a named rejection with the single rule
it violates. The good examples prove the contracts accept what they should; the bad examples prove they reject
what they must, one rule at a time, which is what makes the contract enforceable in review. Gates G2 through
G5 are NOT started, and the absent paths are stated plainly: `backend/weather/`, `backend/api/app.py`,
`frontend/`, and `scripts/integration_test.py` do not exist, and `backend/api/` contains only an `__init__.py`
placeholder. Stating absence explicitly prevents the most common hackathon failure mode — two owners each
assuming the other created the shared directory — and gives Section 10's work plan a clean baseline:
everything from G2 onward is greenfield against frozen contracts.

### 6.8 The teammate prototype

The teammate prototype `Canso Launch Prototype.html` (1041 lines) is a self-contained in-browser
implementation with its own compute, findWindows, and GMST functions, a mock-or-engine seam, the SSO 98.1
preset, and a four-state weather display whose fourth state is the honest 'No forecast yet (beyond ~16d)'
indicator. Its role needs careful framing for a newcomer: it is the Track 2 delivery surface in preview form,
proving that the dashboard concept renders engine-shaped outputs, but it is NOT the engine and must not be
confused with it — its in-browser math is a stand-in, and the integration path is the `fromMock()` function
that swaps mock data for live FastAPI `/v1/*` responses, not a rewrite of the dashboard. That seam design is
why the prototype's 1041 lines are an asset rather than throwaway work: every display element already expects
engine-shaped fields, so wiring it to the real API is a data-source change, not a redesign.

### 6.9 The three falsifications: slide-ready science

The three falsifications are our most slide-ready scientific content, because each one states a claim, the
evidence that settles it, and the consequence — the classic falsification structure judges recognise from real
science. Falsification (a): the 45.1-degree LEO target is unreachable from 45.3 North by direct ascent,
because |cos(45.1°)/cos(45.3°)| = 1.0035 > 1 admits no real azimuth, so the engine returns reachable:false
with an approximately 27 m/s plane-change price. Falsification (b): the 87.9-degree Polar target needs no
dogleg, launching cleanly at azimuth 177.0 degrees (with 98.1-degree SSO at 191.6), which rebuts any suspicion
of blanket refusal and shows the corridor comfortably contains real missions. Falsification (c): the
3.99-degrees-per-day J2 drift value is wrong, with the correct value being −5.14 degrees per day at 600 km and
45.1 degrees inclination, established by the GDC equation, confirmed by the engine at −5.1354, and enforced by
a literal grep that keeps the wrong constant out of the codebase. Together the three tell a story no generic
dashboard can tell: we tested the marketing numbers, we proved one of them geometrically impossible as stated,
we showed the others work cleanly, and we caught and corrected our own perturbation constant along the way.

---

## 7. Tests / Validation

This section explains what each test suite does, what it proves, and why it exists — because a test count
without an explanation is just a number, while a test count with a threat model is evidence. Our testing
philosophy is that every suite exists to defeat a specific way the project could be wrong: wrong physics,
widened tolerances, untested contracts, network-dependent flakes, non-reproducible numerics, or audit findings
left unaddressed. A newcomer who understands the threat behind each suite can extend the suites correctly; one
who sees only the counts will add tests that prove nothing.

### 7.1 The engine suite: 283 passed

Running `python -m pytest backend/engine/ -q` produces 283 passed with zero failures, and that command is the
first thing to run on any clean checkout because it validates the entire deterministic core. The count matters
less than the coverage structure: the suite exercises reachability algebra including the 45.1-degree refusal,
J2 rates across the altitude-inclination grid, window search against hand-checks, the injection fixed-point
solve with convergence and bracketing behaviour, SSO LTAN coupling, corridor and conjunction screens,
reference-frame conversions, provenance echoing, schema conformance of every response, and the
published-window reproduction gate. Each suite file has a named threat: the smoke suite catches import-time
and wiring breakage; the provenance suite catches numbers that lost their lineage flags; the frames suite
catches rotation-matrix and sidereal-time errors; the reachability suite catches corridor and admission-logic
regressions; the J2 suite catches perturbation-constant drift; the window suite catches rate-arithmetic
errors; the injection suite catches solver convergence failures; the SSO suite catches LTAN and
altitude-coupling errors; the screens suite catches filter-logic inversions; the schema-conformance suite
catches response-shape drift; the provenance-echo suite catches responses that fail to repeat their inputs and
constants; and the reproduce-published-windows suite catches physics that no longer matches reality. The
twelve engine test files are test_smoke, test_provenance, test_frames, test_reachability, test_j2,
test_window, test_injection, test_sso, test_screens, test_schema_conformance, test_provenance_echo, and
test_reproduce_published_windows.

### 7.2 The contract suite: 70 passed

Running `pytest tests/contract/ -q` produces 70 passed, and this suite guards a different threat: interface
drift between subsystems built by different owners. The 70 tests load the 8 frozen JSON schemas and validate
the 20 good examples (which must all accept) and the 43 bad examples (which must each reject for exactly its
named single rule). The per-bad-example single-rule audit means every rejection is attributable: bad example
17 fails only the azimuth-range rule, for instance, so a change that accidentally weakens that rule breaks
exactly one named test rather than silently admitting bad input. The format-checker load-bearing note in the
contract proof records which format validators actually enforce their formats at runtime as opposed to merely
documenting them — a subtle but critical distinction, because a documented-but-unenforced format is an open
door for malformed data at integration time. The proof log for all of this is `docs/log/api.md`, which a
newcomer should read as the contract's flight recorder.

### 7.3 Clean-clone verification and the TDD log

Both suites are clean-clone verified: from a fresh `git clone --branch engine/issue-02` followed by `pip
install -e '.[dev]'`, both suites pass without any developer-machine state — no cached artefacts, no local
keys, no uncommitted helpers. Clean-clone verification exists to defeat the "works on my machine" failure mode
that kills hackathon demos, where a result depends on a file that was never committed. The full evidence trail
is the 723-line TDD log in `backend/engine/progress.md`, which records every work item from E0 to E12 in order
with its tests, its implementation, and its review notes. A newcomer ramp-up exercise that pays large
dividends is to read that log start to finish: it is the complete narrative of how the engine came to be,
including the dead ends.

### 7.4 G1 at two levels, with a guard on the guard

The G1 validation gate operates at two levels because one level proved insufficient under adversarial review —
and the story of why is itself worth understanding. Level L1 is the physics residual check: the engine's
window centres minus published liftoff times must fall within tolerance on the anchor set. Level L2 is the
end-to-end `compute_windows` check over a real date range: the full pipeline, called exactly as the API will
call it, must reproduce the anchors, which defeats the failure mode where unit-tested components are miswired
at the seam. The guard-on-guard is a test that stubs the solver with a broken implementation and asserts that
the gate FAILS: it proves the gate is capable of detecting failure rather than passing vacuously. The
tolerance-locking test, whose full name is `test_the_gate_does_not_widen_its_tolerance_to_absorb_a_miss`,
asserts that the tolerance constant has not been enlarged to absorb a regression — it defeats the most
tempting form of validation fraud, which is moving the goalposts instead of fixing the physics. Together the
two levels plus the meta-tests mean G1 GREEN certifies the physics, the wiring, the gate itself, and the
tolerance.

### 7.5 The adversarial audit and its remediation

The adversarial audit returned the verdict SHIP WITH FIXES, and every fix is remediated and merged — this
subsection explains each finding because the findings are the kind of subtle validation holes that judges
probe. Finding one was gate re-implementation mutation: an empty `find_windows` that returns nothing, a
raising solver that always throws, and zeroed J2/GMST functions all previously PASSED the L1 gate, which meant
the gate was not actually exercising the code it claimed to certify — the testing equivalent of a smoke
detector with no battery. The remediation was the L2 end-to-end level described above, which all three mutants
fail. Finding two was dead Sentinel-3C reference URLs: the published-window sources returned 404, meaning our
anchor evidence pointed at vanished pages; all 10 reference URLs were replaced with live sources and are now
200-tested, meaning an automated check fetches each one and asserts HTTP 200. Finding three was the 13:35
ambiguity: a published time quoted as "13:35" without specifying hours-minutes versus decimal hours (13.35
hours = 13:21) creates a 14-minute interpretation spread that dwarfs our tolerance, so the anchor is now
dual-asserted under both readings with the ambiguity documented. Finding four was GMST precision: a
1e-4-degree loosening of the sidereal-time tolerance was split into a 5e-5 component plus a 2e-6 component
with the gap between them pinned by analysis, so that no future change can silently consume the slack. Each
remediation is the kind of unglamorous validation hygiene that separates a demo from an instrument — and
saying so on slides, briefly, signals a team that has been reviewed rather than merely built.

### 7.6 Literal grep, offline tests, determinism, and contract proof

Four final disciplines close out validation. The literal grep — `grep -rn '3.99' backend/engine/*.py` exiting
with status 1 and zero hits — mechanically enforces the J2 correction of Sections 3.2 and 6.9: the wrong
constant cannot re-enter the codebase through any edit without breaking the suite, and the `j2.py` docstring
names the rejected constant in words without containing the literal so the grep stays meaningful. The
offline-tests rule states that tests never touch the network: the 3 real CelesTrak TLEs vendored into the
fixtures (the International Space Station at 426.8 km, TIANQIN at 591.5 km, SENTINEL-3A at 814.4 km, all
fetched at 2026-10-03T22:29:12Z with checksums under test) mean conjunction and propagation tests run
identically on an aeroplane as in the lab, and any fixture tampering breaks a checksum test. Vendoring with
provenance — recording what the object is, its altitude, and exactly when it was fetched — is what makes
offline testing honest rather than stale. The determinism rule states byte-identical numerics across runs
except for the excluded wall-clock field `computation_ms`: rerunning any computation reproduces every digit,
which is what makes every number in this document auditable rather than anecdotal. And the contract proof in
`docs/log/api.md` records the 70-test pass, the per-bad-example single-rule audit, and the format-checker
load-bearing note, so that the API boundary — the highest-risk integration surface — carries its own evidence
file.

---

## 8. Credibility

This section explains why each credibility element convinces a judge — because credibility is not a mood but a
set of verifiable artefacts, each aimed at a specific scepticism a judge will hold. The default judicial
posture toward any hackathon claim is disbelief: the numbers are assumed tuned, the novelty assumed
pre-empted, the demo assumed hard-coded, and the Canadian content assumed decorative. Each subsection below
names the scepticism and the artefact that defeats it.

### 8.1 The rubric self-score and the path to full marks

The self-score of 37 out of 40, with Significance and Originality at 4 each, defeats the scepticism that the
team cannot assess its own work. A team claiming 40/40 on day one signals either dishonesty or
incomprehension; a team claiming 37 with named gaps and a priced path to the missing points signals exactly
the judgment the rubric rewards. The path to 5 on both rows is concrete rather than aspirational: a live
hindcast Brier skill score demonstrating forecast-coupled probabilities beat climatology on real historical
dates (Significance — the work changes decisions), plus the O'Neill delay-cost layer at DOI 10.2514/1.A36618
converting probabilities into cost-optimal recommendations (Originality — the composition is new). Both are
buildable from frozen contracts with named owners, so the path is a schedule rather than a hope.

### 8.2 Claim discipline: PROVED, SKETCHED, CONJECTURE in code

The claim-tier discipline of Section 5 defeats the scepticism that the mathematics is decorative. Every
advanced claim is marked in code as PROVED (the reachability algebra |cos i / cos phi| ≤ 1, a two-line
sine-boundedness lemma; and the fixed-point contraction, honestly noted as the relaxation-map proof while the
shipped bisection carries the stronger guarantee), SKETCHED (the chance-constrained formulation and the
opportunity process, with assumptions named), or CONJECTURE (Brier skill above zero and the ~10-day horizon,
with verification procedures named). A judge who asks "is your Banach claim real?" gets walked to the
derivative bound 0.014024 versus 0.017 and the honest bisection note — an answer that demonstrates
understanding rather than incantation. The tier marking travels in the source so it cannot be inflated in
retelling: no slide can promote a CONJECTURE to a result without contradicting the code.

### 8.3 Anti-GMAT positioning: a decision layer, not a propagator

The anti-GMAT positioning defeats the scepticism that the engine is a weak clone of existing tools. GMAT, STK,
Orekit, and their kin propagate trajectories; our engine decides launch dates. It sits above propagation as a
decision layer exposed over HTTP, consuming orbital geometry, weather ensembles, corridor polygons, and
traffic catalogues and emitting ranked, priced, provenance-carrying recommendations — including the priced
refusal, which no propagator emits because no propagator is asked whether launch should happen. Positioning as
a decision layer rather than a propagator also explains why we do not compete on propagator features
(high-fidelity force models, manoeuvre optimisation): those are inputs to our layer, interchangeable behind
the seam, and our value is the coupling, the calibration, and the honesty semantics.

### 8.4 CSA and MDA relevance: sovereign launch, verified sources

The CSA/MDA relevance material defeats the scepticism that the Canadian content is decorative. Sovereign
Canadian launch is the mission: Spaceport Nova Scotia as the site, MLS and Cyclone-4M verbatim inclinations as
the targets, all-south Atlantic trajectories as the range design, CARs verified at the primary legal source
laws-lois.justice.gc.ca. The data-sovereignty story is equally concrete: ECCC GeoMet and Datamart are keyless
Canadian model feeds already probed at HTTP 200, Open-Meteo forecast and ensemble feeds are keyless global
complements, ERA5 reanalysis comes via the Copernicus Data Store with the key held by Het, CelesTrak TLEs are
keyless now with the Space-Track key also held by Het behind a one-line switch. Keyless-now plus
key-held-for-upgrade means the demo runs without secrets while the operational path is already secured — the
exact viability narrative the rubric rewards.

### 8.5 Canso real-data honesty: VERIFIED versus ASSUMPTION

The provenance-flag discipline defeats the scepticism that the inputs are invented. The EA Registration
Document 16-5903 and Focus Report were searched and found to contain NO numeric corridor — Figure 2.9 has no
axis — so the corridor A_min 90 / A_max 200 is flagged ASSUMPTION, openly a placeholder awaiting surveyed
data. The Cyclone-4M AUG azimuths 118.5, 180, and 181 are VERIFIED against the User's Guide; the 540-second
time-to-injection is ASSUMPTION, openly awaiting vendor confirmation. Every row of `site_canso.json`,
`cyclone4m.json`, and the TLE and published-window fixtures carries its VERIFIED-or-ASSUMPTION flag, and the
flags travel inside every engine response's provenance block. A judge can therefore audit any number on any
slide back to its evidentiary status in seconds — which is precisely the behaviour that makes the remaining
assumptions trustworthy rather than suspicious.

### 8.6 Gap honesty: pre-emption conceded where it exists

The gap-honesty posture defeats the scepticism that the novelty is inflated. No published orbital analysis for
Canso exists — the Section 2.1 negative result with its grep evidence — and where prior art does pre-empt us,
we concede it by name: the SLS window algorithm (NTRS 20205004470) pre-empts ascent-correction novelty, so the
correction ships as Canso numbers rather than as a claim; APRA and PACER pre-empt climatological-availability
novelty in the generic sense, so our claim is scoped to the open, forecast-coupled, orbit-specific,
hindcast-validated synthesis they do not provide. Conceding pre-emption where it exists is what makes our
surviving novelty claims — the Canso-first numbers, the coupled probability, the priced refusal, the
hazard-cost layer — believed rather than discounted.

### 8.7 The weather-honesty rule and the one-line contribution

The weather-honesty rule — FORECAST at or under 10 days, CLIMATOLOGY beyond, with skill scored as BSS against
climatology — defeats the scepticism that the probabilities are fabricated precision. It is a public,
physics-grounded commitment (Section 3.8) with a mechanical verification (Section 4.5), and the prototype's
fourth weather state 'No forecast yet (beyond ~16d)' shows the rule already shaping the interface. The
one-line contribution for slides compresses the entire project into a single claim a judge can write down: an
open Canso engine plus forecast-coupled P(launchable) with hindcast-validated skill, where the ascent
correction ships as a number rather than as novelty. If a teammate remembers nothing else, she remembers that
sentence — and every section of this document is the evidence behind one of its clauses.

---

## 9. Live-Data + Platform Capability / Functionality

This section explains how each live-data feed fits the platform — what it provides, why the platform needs it,
and what its operational status is — because "live data" on a slide invites the immediate judicial question of
whether anything is actually live. The honest answer has three parts: what works keyless today, what is
key-held for upgrade, and what is planned but not yet built. Each is stated plainly so that no demo accident —
an expired key, a feed outage — can expose a claim the platform cannot support.

### 9.1 Keyless feeds working now

Three feeds work today with no API key, and each fills a distinct platform role. Open-Meteo provides the
16-day deterministic forecast, the ensemble forecast whose member fraction becomes P_forecast, and the archive
API reaching back to 2021 that powers hindcast construction — it is simultaneously the short-range predictor
and the historical record, which is why it is the backbone feed. ECCC GeoMet (`api.weather.gc.ca`) and
Datamart (`dd.weather.gc.ca`) provide the sovereign Canadian model outputs, principally the 15 km GDPS to a
10-day horizon already probed at HTTP 200; their platform role is authoritative Canadian guidance plus the
viability narrative that the system does not depend solely on foreign feeds for domestic launches. CelesTrak
provides the keyless TLE catalogue behind the conjunction pre-screen: current element sets for catalogued
objects, propagated by SGP4, screened for ascent-phase miss distances. Keyless matters operationally because
it means the demo and the hindcast pipeline run without credential management — there is no secret that can
expire mid-presentation — and it matters for viability because it proves the platform's core loop functions on
open infrastructure.

### 9.2 Key-held upgrades: ERA5 and Space-Track

Two capabilities are secured but key-held, both by Het, and the one-line-switch design means upgrading is a
configuration change rather a rebuild. The Copernicus Data Store key unlocks ERA5 reanalysis — the hourly,
0.25-degree, 1940-to-present best-estimate atmosphere that serves as climatology baseline and hindcast truth —
without which the BSS skill claim of Sections 4.5 and 5.3 cannot be computed. The Space-Track key unlocks the
authoritative American catalogue behind the same conjunction screen CelesTrak feeds today; switching from
CelesTrak to Space-Track is a single-source-line change precisely because the screen consumes standard TLEs
either way. Naming the key-holder in the document matters for team operations: there is exactly one person to
ask, and the bus factor is visible rather than discovered during a demo crisis.

### 9.3 The planned API surface: five endpoints

The API planned in Parts IV and V of the specification exposes the engine as five HTTP endpoints, each with a
distinct planner function that a newcomer should understand before building or demoing against them.
`/v1/windows` returns the computed launch windows for a target orbit type and date range — the core
deliverable. `/v1/series` returns time series of window opportunities and probabilities across a campaign
horizon — the manifesting view. `/v1/offsets` returns the injection-versus-liftoff timing offsets, the Track 1
bonus quantities shift_s and liftoff_error_min — the ascent-awareness evidence. `/v1/tube` returns the
trajectory-uncertainty representation behind the visualisation — the honesty geometry for the 3D view. And
`/v1/validation/skill` returns the hindcast Brier and skill scores with reliability and ROC summaries — the
self-grading endpoint no competing dashboard exposes. The status is honestly NOT YET BUILT: `backend/api/`
contains only an `__init__.py` placeholder, so no slide may imply a live endpoint until issue 4 lands. Stating
the surface now, against frozen schemas, is what lets the frontend prototype's `fromMock()` seam (Section 6.8)
become a live integration by data-source swap rather than redesign.

### 9.4 Frontend: prototype today, live wiring next

The frontend state mirrors the API state: a real, substantial prototype exists — `Canso Launch Prototype.html`
at 1041 lines with in-browser compute, findWindows, and GMST functions, the SSO 98.1 preset, and the
four-state weather display including the honest 'No forecast yet (beyond ~16d)' state — but live wiring to
FastAPI `/v1/*` awaits the API build, with the integration path being the `fromMock()` function rather than a
rewrite. The platform capability today is therefore precisely statable: the deterministic engine is complete
and contract-gated behind 283 engine tests plus 70 contract tests, while the weather adapters, the API
service, and the frontend live integration are pending as gates G2 through G5. That sentence is the whole
platform status in one breath, and it is what every status conversation should open with.

### 9.5 Scope note and submission logistics

Two administrative facts prevent wasted effort. First, the `HACKATHON_PROBLEMS/` package contains no
`challenge2/` directory, and its README states explicitly that Challenge 2 is out of scope for that package,
which covers Challenges 1 and 3 — so no Challenge 2 work belongs there and no Challenge 2 dependency will be
found there. Second, submission is Sunday 4 October at 13:30 Atlantic Daylight Time, which fixes the freeze
schedule for slides, code, and this document: Section 6's evolving marker exists because results after the
freeze belong to the post-submission roadmap, not to the judged package.

---

## 10. What's Next

This section is the build plan from the current state to submission and beyond, ordered so that each item
unblocks the next and each carries its owner, its issue number, and its acceptance gate. A newcomer reading it
should come away knowing exactly what to work on Monday morning, what must be true before it, and how its
completion is recognised. The ordering principle is risk-first: the hour-12 gate and the weather validation
carry the most judging weight and the most schedule risk, so they lead; polish follows proof.

### 10.1 G2 WEATHER: the forecast and climatology adapters (Het, issue 3)

The first build item is G2 WEATHER, owned by Het under issue number 3, producing the `backend/weather/`
package that does not yet exist. Its contents are the Open-Meteo and ECCC adapter modules that fetch, cache,
and normalise forecast and ensemble data; the ensemble PoV computation that converts member fractions into
per-constraint violation probabilities; and the ERA5 climatology module served through the Copernicus Data
Store that answers P_clim for any month-hour bin. The governing rule throughout is FORECAST for date horizons
d ≤ 10 days and CLIMATOLOGY beyond, enforced in code rather than by convention so that no caller can
accidentally request forecast precision at day 25. Acceptance is the weather seam returning calibrated
probabilities for historical hindcast dates — the input the skill scoring of item 10.4 consumes. This item
leads the build because every Significance and Originality point beyond the current self-score depends on
probabilities that only this package can produce.

### 10.2 G3 API: the FastAPI service (Rafat, issue 4)

The second build item is G3 API, owned by Rafat under issue number 4, producing `backend/api/app.py` — the
FastAPI application that wraps the `compute_windows(request) -> dict` engine seam behind the five HTTP
endpoints of Section 9.3 (`/v1/windows`, `/v1/series`, `/v1/offsets`, `/v1/tube`, `/v1/validation/skill`). Its
acceptance criteria are conformance to the 8 frozen G0 schemas on all 20 good examples, correct single-rule
rejection of all 43 bad examples, and byte-determinism of responses excluding the wall-clock field. The API
depends on G2 only for the probability-bearing endpoints; the deterministic endpoints can ship against fixture
probabilities first, which is why G3 starts in parallel with G2 rather than after it. Its completion converts
the engine from a library into a service — the precondition for the frontend integration and for any
judge-operated live demo.

### 10.3 G4 FRONTEND: wiring the prototype to live data (Nubah, issue 5)

The third build item is G4 FRONTEND, owned by Nubah under issue number 5, producing the `frontend/` directory
by wiring the existing prototype's `fromMock()` seam to the live `/v1/*` endpoints. The governing constraint
from the track decision is absolute: every pixel renders a Track 1 engine output, with no decorative 3D and no
element that cannot name its API field. Acceptance is a dashboard that, against the live API, displays
computed windows, the countdown to the next computed opportunity, the ground track of the computed ascent,
G/Y/R lights derived from computed constraint probabilities, and the viewing map derived from computed
geometry — with the fourth weather state 'No forecast yet' appearing correctly beyond the skill horizon. G4
depends on G3 for live data but proceeds against fixtures until then, which is exactly what the fixture-based
demo floor was designed to enable.

### 10.4 G5 INTEGRATION and WEATHER-VALIDATION (Anand and Het, issues 6 and 7)

The fourth build item is really two coupled gates: G5 INTEGRATION, owned by Anand under issue number 6,
producing `scripts/integration_test.py`, and WEATHER-VALIDATION, owned by Het under issue number 7, producing
the hindcast skill analysis. The integration script runs the full pipeline end to end — engine through weather
through API to frontend fixtures — and asserts the contract invariants, so that subsystem drift is caught
mechanically rather than at demo time. The weather validation computes hindcast Brier scores and Brier skill
scores against the climatology reference with reliability diagrams and ROC curves per lead time — the C1 and
C2 verification procedures of Section 5.3. These two land together because integration without validation
proves only plumbing, while validation without integration proves only components; the judging weight sits on
the conjunction.

### 10.5 The hour-12 gate comes first

The fifth item is a scheduling constraint rather than a deliverable, and it is stated separately because
violating it is the fastest way to lose the plot: the hour-12 gate — reproducing 3 to 5 published windows
within 5 minutes per spec Section III.2 — must pass before frontend work proceeds on real data. The rationale
is that a dashboard rendering unvalidated windows is a misinformation instrument: every hour spent polishing
the display of wrong numbers is an hour spent making the project worse. The gate currently stands GREEN at G1
(Section 6.3), so the constraint is satisfied and frontend work may proceed — but any physics change that
turns G1 non-green freezes frontend real-data work until it is green again. Newcomers should treat G1 status
as the project's traffic light.

### 10.6 The rubric-5 path: hindcast BSS plus the O'Neill layer

The sixth item is the explicit work plan for the two missing rubric points: live hindcast BSS for Significance
and the O'Neill delay-cost layer at DOI 10.2514/1.a36618 for Originality, as analysed in Section 8.1. The BSS
work is the G5 validation output above, presented as a per-lead-time skill curve crossing zero near day 10 —
the empirical confirmation of conjecture C2 and the visual centrepiece of the methodology slides. The O'Neill
layer implements the expected-cost computation of Section 5.2 item (iv), converting the ranked date list into
a cost-optimal recommendation with dollar figures. Landing both converts the self-score from 37 to the 39–40
band with evidence rather than aspiration, and both are scoped, owned, and scheduled rather than wished for.

### 10.7 Assumption retirement: corridor, ascent duration, and coast handling

The final item is assumption retirement — replacing each ASSUMPTION flag with surveyed or measured fact —
because assumptions are technical debt that judges can price. The numeric corridor replaces the A_min 90 /
A_max 200 placeholder with surveyed polygon coordinates the moment range documentation or vendor data supplies
them; the change is a data edit precisely because the screens were built against a polygon interface rather
than hard-coded bounds. The 540-second time-to-injection is retired by vendor confirmation or by profile
measurement, with the engine already parameterised on T(t) so the update propagates through the fixed-point
solve automatically. The MetOp-SG-A1 coast-phase ambiguity is resolved by sourcing the published coast profile
or by bounding the ambiguity analytically and carrying it as an explicit uncertainty rather than an unknown.
Each retirement is recorded by flipping the corresponding provenance flag from ASSUMPTION to VERIFIED, which
means the provenance system doubles as the debt tracker: the count of remaining ASSUMPTION flags is the exact
measure of what is left to verify.

---

## 11. Key Files

This section is the repository map: for every document, module, fixture, and test artefact referenced anywhere
in this handover, it states where it lives, what it contains, and when a newcomer should open it. A teammate
who has read this section should be able to navigate the tree without guidance and — just as important —
should know which files are authority, which are evidence, and which are context-only background that must not
leak onto methodology slides.

### 11.1 Authority and science sources

The authority spec `research/challenge2/C2_framework_and_build_spec.md` (891 lines, with a verbatim copy at
`hackathon_repo/docs/spec/`) is opened first whenever any dispute arises about what to build, what equation to
implement, what tolerance applies, or what the challenge asked — it outranks every other file including this
one. The science compendium `research/challenge2/C2_launch_window_science.md` (Sections A through G) is opened
when implementing or reviewing any physics: window geometry, J2 theory, operational algorithms, weather
literature, or skill-horizon foundations. The citation ledger and track record
`research/challenge2/C2_prior_art_and_track.md` (Sections A through G, with the rubric arithmetic 41 versus 36
in Section B) is opened when writing or defending any novelty, pre-emption, or track-decision statement. The
site dossier `research/challenge2/C2_science_hunt.md` is opened for azimuth derivations, coordinate variants,
and the Bermuda-overflight note. The kill-versus-keep list `research/challenge2/C2_preemption_map.md` (Section
0 and item A2 in particular) is opened before claiming novelty for anything, as the checklist that prevents
pre-empted claims.

### 11.2 Contract, workflows, and issues

The master contract `hackathon_repo/docs/00_INTEGRATION_CONTRACT.md` is opened to learn the four workflows,
the three seams, and the G0–G5 gate definitions that govern all parallel work. The workflow files
`01_WORKFLOW_ENGINE.md`, `02_WORKFLOW_WEATHER.md` (also referenced as 02_WEATHER), `03_WORKFLOW_API.md` (also
referenced as 03_API), and the 04_FRONTEND document are opened by each subsystem owner as the build manual for
their gate. The per-issue records `hackathon_repo/docs/issues/issue-01` through `issue-07` are opened to see
the working history, decisions, and acceptance state of each GitHub issue. Together these files are the
project's operating system: anyone unsure what to do next, who owns it, or what done looks like finds the
answer here rather than in chat history.

### 11.3 The shipped engine and its fixtures

The shipped engine lives in `hackathon_repo/backend/engine/`, and its ten modules map one-to-one onto the
methodology of Section 4: `engine.py` orchestrates the `compute_windows` seam; `target.py` models the target
orbit types; `reachability.py` implements the admission algebra; `j2.py` computes the perturbation rates with
the wrong-constant grep guard; `window.py` implements the node-alignment search; `injection.py` implements the
fixed-point solve; `sso.py` implements the LTAN coupling; `screens.py` implements the three pre-filters;
`frames.py` handles reference frames and sidereal time; and `provenance.py` builds the
VERIFIED/ASSUMPTION-carrying provenance blocks. The fixtures in `data/site_canso.json`,
`data/vehicles/cyclone4m.json`, `data/vehicles/cyclone4m_coast.json`, `data/tle_fixture.json`, and
`data/published_windows.json` are opened whenever a site, vehicle, traffic, or anchor number is questioned —
each row carries the flag that settles the question. The engine's own records `DONE.md` (the shipped-state
manifest), `README.md` (the module guide), and `progress.md` (the 723-line TDD log) are opened to check
current results state, to onboard onto the module structure, and to review the complete development narrative
respectively — with `progress.md` and `DONE.md` being the two files Section 6 requires re-checking before any
slide freeze.

### 11.4 Contract tests, prototype, pending paths, and context-only files

The contract tests in `hackathon_repo/tests/contract/` (8 schemas with 20 good and 43 bad examples) are opened
when modifying any API shape or diagnosing an integration rejection; the proof log
`hackathon_repo/docs/log/api.md` is opened to see the contract's verification evidence. The prototype `Canso
Launch Prototype.html` (1041 lines, with the `fromMock()` seam) is opened for all frontend work — as the
surface to wire rather than to rewrite. The not-started paths `hackathon_repo/backend/weather/`,
`hackathon_repo/backend/api/app.py`, `hackathon_repo/frontend/`, and
`hackathon_repo/scripts/integration_test.py` are where G2–G5 work lands; their current absence (with
`backend/api/` holding only `__init__.py`) is the baseline Section 6 reports. The landscape files
`F4_scientific_opportunity_landscape.md`, `mission-accepted-deep-research.md`,
`survey/mission-accepted-phase-3/question.md`, `THREE_DIRECTIONS.md`, `research-prompts/README.md`,
`OUR_DIRECTION_PHYSICS_RESEARCH.md`, and `TOP_5_PROBLEM_STATEMENTS.md` are context-only background: opened for
project-history curiosity, never for methodology-slide content, as established in Section 3.11.

---

## 12. Glossary

Every abbreviation, symbol, and piece of jargon used in this document is defined below on first-use terms,
with the explanation expanded so that a newcomer meets each term as a concept rather than as a decoding
exercise. Items carry their liftable numbers, identifiers, and file associations so the glossary doubles as a
slide-picker index.

- **45WS (45th Weather Squadron):** The United States Space Force weather unit responsible for launch commit
  criteria and day-of weather decisions at the Eastern and Western Ranges, and the owner of the
  Probability-of-Violation methodology our probabilistic layer extends. It appears here as the author of the
  per-constraint, day-of prior art (Section 3.6) that our forecast-horizon, orbit-coupled synthesis goes
  beyond.

- **Amax / Amin (corridor bounds, default 200 / 90 deg):** The maximum and minimum permitted launch azimuths
  defining the south-facing safety fan, currently an ASSUMPTION placeholder (Section 4.1) because the EA
  contains no numeric corridor. Every window solution's azimuth must fall inside this interval; the retirement
  path is tracked in Section 10.7.

- **AMU (Applied Meteorology Unit):** The research support unit behind much of the 45WS analysis, cited as the
  institutional source of the PoV and LLCC studies in our ledger.

- **APRA / PACER (MSFC climatological availability tools; AMS 2008 Paper133849; NTRS 20080013555):** Marshall
  Space Flight Center tools computing climatological probability of constraint violation by month and hour —
  the closest prior art to our availability climatology (Section 3.7), limited to internal, climatology-only,
  non-orbit-coupled operation, with conditional day-after probability named UNMET in a 2008 requirements
  document.

- **AUG (Ascent Unit Guidance; Cyclone-4M azimuths 118.5 / 180 / 181):** The guidance system of the Cyclone-4M
  vehicle whose programmed azimuths are VERIFIED site-vehicle facts (Section 3.5) used to cross-check our
  engine-computed headings.

- **BSS / BS (Brier Skill Score / Brier Score; BSS = 1 − BS/BS_ref):** The verification metrics of Section
  4.5: BS is the mean squared error of forecast probabilities against binary launch outcomes, BS_ref is the
  climatology reference score, and BSS above zero is conjecture C1 — the minimum evidence the probabilistic
  layer adds skill.

- **BSS reference (climatology):** The baseline forecast (historical month-hour success fraction) against
  which BSS is computed; beating it is the honest minimum claim, and the climatology module of G2 exists to
  produce it.

- **C4M (Cyclone-4M launch vehicle, Maritime Launch Services):** The medium-lift launcher intended for
  Spaceport Nova Scotia, whose User's Guide supplies pad coordinates, AUG azimuths, and the context for the
  540-second ascent assumption.

- **CARs 602.43 / 602.44 (Canadian Aviation Regulations governing launches; verified at
  laws-lois.justice.gc.ca):** The regulatory provisions authorising launches, cited from the primary statute
  source as part of the credibility discipline (Sections 1.2, 8.4).

- **CDS (Copernicus Data Store; ERA5 access; key held by Het):** The European data portal serving ERA5
  reanalysis, the key-held feed behind the climatology and hindcast-truth capability (Sections 3.9, 9.2).

- **CelesTrak (keyless TLE source for the SGP4 conjunction pre-screen):** The public orbital-element catalogue
  feeding our traffic screen today, with Space-Track as the one-line-switch upgrade (Sections 4.6, 9.1–9.2).

- **Climatology vs forecast (rule: FORECAST d ≤ 10, CLIMATOLOGY beyond):** The skill-horizon distinction of
  Section 3.8: forecasts carry information only inside ~10 days (Lorenz 1982; Tellus A 2013
  10.3402/tellusa.v65i0.19022; Buizza–Leutbecher 2015; ECMWF tau-at-71% ~9 d NH), and honest probabilities
  switch to historical averages beyond it.

- **CONJECTURE / SKETCHED / PROVED (claim tiers per spec II.9; venue Acta Astronautica):** The three
  evidentiary tiers of Section 5, marked in code so that no retelling can promote a prediction into a result.

- **Delta-v / plane-change delta-v (dv = 2·vc·sin(di/2); Canso 45.1 case 26.8 m/s at vc 7.67 km/s):** The
  propulsive cost of rotating the orbital plane, used to price the 45.1-degree refusal (Section 4.1) rather
  than merely reporting failure.

- **Dogleg (in-atmosphere plane-rotation manoeuvre):** The guided turn during ascent that achieves part of a
  required plane change at performance cost; our falsification (b) shows the 87.9-degree Canso target needs
  none.

- **DOL (Day-of-Launch; SLS DOL, NTRS 20205001580):** The launch-day update methodology for window solutions
  as final winds and targeting arrive — prior art we follow operationally (Section 3.3).

- **EA (Environmental Assessment; Class I, approved 4 Jun 2019; max 8 launches/yr; Registration Doc
  16-5903):** The regulatory instrument permitting Canso launches, searched by grep over ~9k/21k/6k lines with
  negative findings on fog, scrub, and corridor data (Sections 1.2, 2.1).

- **ECCC GeoMet / Datamart (`api.weather.gc.ca` / `dd.weather.gc.ca`; GDPS 15 km, 10 d; keyless, probed HTTP
  200):** The sovereign Canadian weather feeds in our platform (Sections 3.9, 9.1).

- **ENL (Effective-sample-size Number of Looks; Wishart, Provenance Guard):** The effective independent sample
  size after accounting for input correlation, from the Wishart precision model in the Provenance Guard face
  (Section 5.5).

- **EoT (Equation of Time; apparent-vs-mean Sun, up to 4 deg / 16 min):** The correction between the true Sun
  driving SSO lighting and the mean Sun driving clocks, validated to 0.005 degrees on equinox/solstice anchors
  (Sections 4.8, 6.5).

- **ERA5 (reanalysis climatology; 1940–, hourly, 0.25 deg):** The retrospective model-observation fusion
  atmosphere serving as climatology baseline and hindcast truth, via CDS (Sections 3.9, 9.2).

- **G0–G5 (integration gates: G0 contract frozen; G1 engine green; G2 weather; G3 API; G4 frontend; G5
  integration/validation):** The six acceptance milestones pacing the build, with G0 and G1 landed and G2–G5
  scheduled in Section 10.

- **G/Y/R (Green / Yellow / Red weather impact states for the Track 2 dashboard):** The three planner-facing
  weather lights driven by computed constraint probabilities through the HMM regime layer (Sections 1.4, 5.5),
  with the prototype's honest fourth state for beyond-horizon dates.

- **GDPS (Global Deterministic Prediction System; ECCC, 15 km, 10 d):** The Canadian global model behind the
  GeoMet/Datamart feeds.

- **GEFS (Global Ensemble Forecast System; fallback ensemble):** The American ensemble system held as the
  fallback uncertainty source (Section 3.9).

- **GMST (Greenwich Mean Sidereal Time; window equation GMST + lambda = Omega_t + delta):** Earth's rotation
  angle against the fixed stars, advancing 15.0411 degrees per hour — the clock hand of the window equation
  (Section 4.3).

- **Hindcast (retrospective forecast recomputed with only then-available inputs, scored against actuals):**
  The only honest validation of a forecasting system without waiting years (Section 2.2), implemented by the
  `hindcast()` seam and scored by BSS.

- **HMM (Hidden Markov Model; G/Y/R weather states):** The regime-tracking probabilistic model of Section 5.5
  in which hidden Green/Yellow/Red states evolve as a Markov chain and emit observable weather outputs.

- **J2 (Earth's oblateness coefficient; node rate dOmega/dt = −(3/2)·J2·n·(Re/p)²·cos(i); GDC Orbit Primer Oct
  2018):** The equatorial-bulge perturbation driving nodal precession (Section 3.2), with the Canso reference
  −5.14 deg/day at 600 km / 45.1 deg and the wrong 3.99 value grep-excluded.

- **LFA31A / 31B / 29 (Lobster Fishing Areas; hazard-cost KEEP item):** The commercial grounds under Canso
  ascent tracks whose closure cost our opportunity model prices — the most place-specific contribution
  (Section 2.5).

- **LLCC (Lightning Launch Commit Criteria; scrub ~5%, delay 35%, $150k–1M per delay cost band; AMS 103803):**
  The lightning rules motivating the delay-cost layer (Sections 3.6, 5.2).

- **LTAN (Local Time of Ascending Node; SSO coupling Omega_req = alpha_sun + 15·(TLT − 12 h); drift 6 min/yr
  per 0.01 deg):** The Sun-phasing condition defining SSO planes (Section 5.4), jointly satisfied with the
  altitude-specific inclination.

- **MLS (Maritime Launch Services; Spaceport Nova Scotia operator):** The spaceport operator and source of the
  verbatim 45.1 / 87.9 / 98.1 target inclinations (Sections 1.2–1.3).

- **NGBoost (Natural-gradient boosting; Wind-Band Student-t + conformal intervals):** The distributional
  regression method of the Wind-Band face fitting heavy-tailed wind distributions with calibrated coverage
  (Section 5.5).

- **NOTAM (Notice to Airmen; NavCanada; display-only screen):** The airspace notices shown to planners without
  automatic veto (Section 4.6).

- **NTRS (NASA Technical Reports Server; IDs 20205004470, 20205001580, 20140010795, 20160001318, 20100021378,
  20130010089, 20120015454, 20080013555, 20070013713, 20140017798):** The archive sourcing every NASA
  prior-art claim in Sections 3.3, 3.4, and 3.6.

- **PoV / POV (Probability of Violation; 45WS/AMU per-constraint metric):** The per-constraint violation
  probability our ensemble layer extends to forecast horizons with hindcast calibration (Sections 3.6, 5.5).

- **RAAN / Omega (Right Ascension of Ascending Node):** The celestial longitude of the northbound equator
  crossing, fixing the orbital plane's swivel — the central variable of all window analysis (Section 4.3).

- **SGP4 (Simplified General Perturbations propagator for TLE propagation):** The standard analytic propagator
  converting catalogue elements into positions for the conjunction screen (Section 4.6).

- **SSO (Sun-Synchronous Orbit; ~98.1 deg Canso target; rate +0.9856 deg/day = 360/365.2422):** The
  Sun-tracking retrograde family with its altitude-inclination curve 97.4–99.03 deg over 500–900 km (Sections
  1.3, 3.2).

- **TDD E0–E12 (engine test-driven development work items, all shipped; 723-line log):** The twelve gated
  engine build steps on branch `engine/issue-02` (Sections 4.8, 6.2, 7.3).

- **TLE (Two-Line Element set; 3 vendored fixtures: ISS 426.8 km, TIANQIN 591.5 km, SENTINEL-3A 814.4 km;
  fetched_utc 2026-10-03T22:29:12Z):** The catalogue format behind offline conjunction testing (Section 7.6).

- **Conformal (distribution-free coverage-guaranteed intervals under exchangeability):** The calibration
  framework behind Honest Orbits tubes and the Wind-Band top layer (Section 5.5).

- **Hierarchical Bayes (multi-level pooling with feed-specific biases; Provenance Guard):** The data-quality
  model yielding Wishart ENL trust weights (Section 5.5).

- **Opportunity process (Bernoulli thinning over dates; E[T_next], E[cost] with O'Neill 10.2514/1.a36618):**
  The stochastic model converting per-date probabilities into expected waits and dollar costs (Section 5.2).

- **Chance-constrained (|g| ≤ DeltaOmega, corridor, hazard = 1, P ≥ p* under
  exchangeability/stationarity/independence):** The stochastic optimisation framing of window selection
  (Section 5.2).

- **Banach fixed point (contraction q ≈ 0.017, verified 0.014024; relaxation map proved, bisection shipped):**
  The convergence guarantee for the injection solve (Section 5.1).








