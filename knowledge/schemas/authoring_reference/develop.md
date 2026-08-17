# DEVELOP — Authoring Reference (2026-08-17)

Full agent-side spec already exists for this building. Part 1 walks every real step with its existing intelligence; `creator_prompt`/`fy_rationale` are shown as **current (may revise)** where they already exist, or flagged to author where they don't. Part 2 is the current frontend placeholder for direct comparison.

---

## PART 1 — Real spec

### TRACK: NARRATIVE / SCRIPT TRACK

#### Step N-1: Logline

**Purpose:** Compress the full narrative into one sentence containing character,
conflict, and stakes. The logline is the north star — every structural decision
  in the script checks against it. But before the logline exists, FY opens with
  the foundational question: what has the creator already received that hasn't
  been answered yet?

**Success state:** One sentence containing a named character, a stated want, and a
stated obstacle. Doesn't need to be polished.

**Failure state:** Creator produces a theme statement instead of a story statement.
Or a logline written toward what they think will sell instead of what they want to make.

**FY approach (agent-side, not creator-facing):** Opens with: "Before we write anything — what have you already heard,
seen, or felt that you haven't responded to yet? Not what you want to make.
  What's already in you that needs to come out?"
  Receives the answer without evaluating it.
  Then: "Who's this about, what do they want, and what's stopping them? One sentence."
  If theme emerges: "That's what it means. What happens?"
  If logline sounds like a pitch: "Say it like you'd tell it to yourself. Not to a buyer."
  Uses Concept Line from IDEATE as anchor throughout.
  FY names early and holds throughout: "Right now you're the director. You're making
  every creative decision in this building. Whatever that means for production later —
  in here, the vision is yours."

LAYER 3 INJECTION (Step N-1 — surfaces when creator is staring at a blank page
  or asking where to start):
  Story: Mitch Leigh — composer of Man of La Mancha
  What the doubt looked like: The melody for The Impossible Dream did not begin
    with Leigh sitting down to write a great song. It began with him hearing the
    lyric and the story. The melody came immediately — not constructed, received.
    He heard something true and responded to it.
  Decision point: He didn't start with intention. He started with what moved him.
  What happened after: The most performed song in American musical theater.
  FY line: "Mitch Leigh didn't write The Impossible Dream. He heard it —
    in the lyric, in the story — and the melody came immediately.
    What have you already heard that you haven't answered yet?"

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step N-2: Outline

**Purpose:** Story broken into acts and turning points. Not scenes — movements.
The architecture before the rooms. Act shape makes or breaks a script;
  fixing structure at outline costs nothing. Fixing it at draft costs everything.

**Success state:** Three-act shape visible. Inciting incident, midpoint shift, climax,
resolution named — even loosely. Creator can walk through it without notes.

**Failure state:** Outline is actually a scene list. Creator is building rooms before the house.

**FY approach (agent-side, not creator-facing):** "Three moments: what forces your character into motion, what breaks
everything open in the middle, what ends it — for better or worse."
  If creator jumps to scenes: "Those are rooms. I need the building first. What's the shape?"
  Checks every act beat against the logline: "Does this serve [logline]? How?"
  Anything that doesn't serve it goes to the vault, not the outline.
  Holds the director frame: "You're making every creative decision here.
  What does your version of this story do in the middle?"

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step N-3: Structure

**Purpose:** Outline gets bones. Sequences named, act breaks pinned, scene count
estimated. The blueprint from which scene development and drafting works.
  Structure guides are calibration tools — not starting points. Story and
  characters come first. Genre conventions tell you how close you are to the
  form. They don't tell you what your story is.

**Success state:** Sequence map exists. Each major movement has a name. Act breaks
are pinned. Scene count estimated. Creator can walk through it beat by beat.

**Failure state:** Structure is implied but not documented. Or creator started from
a structure template before the story existed.

**FY approach (agent-side, not creator-facing):** "Walk me through it like a map. Start to end — what are the movements?"
Structure guides introduced as calibration, not prescription:
    "Most screenplays run 80-120 pages — not because that's the rule, but because
    the form has proven it works in that range. Where does your story land?"
  Genre conventions named where relevant: "RomComs almost always run 90 minutes.
    Thrillers front-load tension. Horror saves the real threat. These aren't laws —
    they're what audiences have learned to expect. Know them so you can use them
    or break them intentionally."
  When structure is documented: "Read it back to me. Does it hold?"

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step N-4: Scene Development + Visual Development

**Purpose:** Individual scenes built from structure. Character voice found. Key scenes
drafted at full depth. Simultaneously — storyboard and visual development begins.
  This step is where production mode diverges the tool stack significantly.
  The Jimmy principle hits hardest here — write for yourself, not for an imagined
  audience. If the scene makes you laugh, cry, scared, or uncomfortable — it's working.

**Success state:** 3-5 key scenes drafted in full. Creator can point to at least one
line each major character would say that another character wouldn't.
  Storyboard reference exists for key sequences. Production mode determines whether
  storyboard panels are reference artifacts or production deliverables.

**Failure state:** Scenes written toward what the creator thinks the audience wants.
Or visual development skipped entirely — creators who skip storyboarding are
  solving problems on set that should have been solved here.

FY APPROACH — SCRIPT:
  "Pick the scene you're most afraid of. We start there."
  Voice test: do different characters sound different on the page?
  Holds director frame throughout.

FY APPROACH — STORYBOARD:
  After key scenes exist: "Let's put this on its feet visually.
    A rough storyboard now saves you from solving this problem on set — or in
    a generation session where every correction costs time and tokens."
  Storyboard brief assembled from: scene text + character descriptions +
    location descriptions + production mode flag.
  FY routes to storyboard tool based on availability:
    Direct API (Styleframe or confirmed storyboard partner) → preferred
    FAL.ai (if storyboard model accessible via FAL) → bridge layer
    Twin (browser automation for no-API storyboard tools) → fallback
    Midjourney / Firefly / Leonardo → panel generation if dedicated tool unavailable

  TWO MODES based on production_mode flag:
    REFERENCE MODE (live_action, animation pre-production):
      Panels are development artifacts. Rough is fine. Goal is to visualize
      blocking, camera angles, and scene flow before production begins.
      These travel to PLAN and CAST as reference. Not final assets.
    PRODUCTION MODE (generative_ai, hybrid):
      Panels may become final deliverables. Style consistency across panels
      matters significantly. Character consistency across frames is the
      hard problem — FY flags this and routes to models with the strongest
      documented consistency record for the specific requirement.
      These may travel to POST as source assets, not just reference.

  CHARACTER VISUAL DEVELOPMENT (all production modes):
    Generate visual references for key characters from character descriptions.
    CASTING USE: IRL production → character visual brief travels to CAST building
      as the director's visual reference for casting director.
    GENERATIVE USE: AI production → character visual becomes the consistent
      reference that all subsequent generation checks against.
    ANIMATION USE: Character visual becomes the style brief for character design.

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step N-5: Draft

**Purpose:** Full draft assembled from structure and scene development. Not perfect —
complete. A complete bad draft beats a perfect fragment every time.
  Raw creative is always the best. Write out of order. Bark the breakfast idea
  into your phone. Get it out however it comes — imperfect capture is correct
  production behavior, not a compromise. The voice memo at 7am is as valid as
  anything produced at a desk. The draft is not the destination. It proves the
  idea has a second draft in it.

**Success state:** Full draft exists. Beginning, middle, end. Creator has read it once.

**Failure state:** Draft stops at act two because "it's not working." Or creator edits
as they write and produces forty polished pages and nothing after.

**FY approach (agent-side, not creator-facing):** "Write the draft. I'll hold the room. No editing until it's done."
If creator stalls: "Where are you? What's the next scene? Say it out loud."
    Takes what the creator says and feeds it back: "Write that. Exactly that."
  If creator wants to edit: "Not yet. Keep going. You can't fix what doesn't exist."
  If creator is blocked: "Get away from the page. Go watch something that inspired
    this in the first place. Walk. Let your mind go back to what started this.
    Then come back. The creative process is nonlinear — that's not a problem,
    that's how it works."
  Imperfect capture principle: "The voice memo counts. Write it out of order if
    that's how it's coming. Get the idea while you have it — the order is an
    editing problem, not a writing problem."
  NOTE: FY never generates the full draft independently. Creator writes;
    tools assist and accelerate. FY holds the creator in the chair.

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step N-6: Revision Passes

**Purpose:** Draft becomes script. Systematic revision targeting one element per pass.
Not "make it better" — surgical. Every pass has a target. Every pass produces
  a named version. The diagnostic questions at every pass:
  Is this scene moving the story forward? Is it revealing character?
  Is it funny, dramatic, scary — whatever it needs to be?
  If no to all three: cut it regardless of how much you love it.

**Success state:** Each revision pass has a stated target. Creator can name what
changed between the two most recent versions and why.

**Failure state:** Revision is "make it better" with no specific target.
Or creator brings in collaborators without knowing whose vision is now on the table.

**FY approach (agent-side, not creator-facing):** "What specifically isn't right about this draft?"
Names the one thing. One pass targets that one thing.
  Diagnostic questions applied after each pass:
    "Does every scene move the story forward or reveal character?
     Is there anything in here that you love but the story doesn't need?
     Cut that first."
  On collaborators: "Whoever you bring into revision brings their own aesthetic.
    That's not a flaw — that's what they do. Know whose vision is on the table
    at every pass. If you're not sure, it's yours."
  Creative block in revision: "Go back to what inspired this. Put on the film.
    Play the record. Walk and let your mind go there. Then come back.
    The work will be there when you return."
  Version Anxiety: "Version [N] of something worth making is closer than Version 1
    of something you don't believe in yet. What specifically isn't right?"

LAYER 3 INJECTION (Step N-6 — surfaces when creator loses faith in the revision
  process, brings in a collaborator pulling the work in another direction,
  or is treating iteration as evidence of failure):
  Story: Lee Brownstein — producer/director, first indie feature
  What it looked like: Script written. A skilled writer friend brought in —
    an expert in ensemble comedies with multiple concurrent storylines.
    His work was genuinely strong. It just wasn't this film. His aesthetic
    came with him, as it always does. Not intentional. Just inevitable.
    Shot everything to compensate. Nearly killed himself to overshoot.
  Decision point: Saved the film in the edit room. The editor is the real storyteller.
    Cut what didn't feel right. Cut what didn't move the story forward. Cut what
    was loved but wasn't needed. The film survived.
  What happened after: The lesson locked permanently. The pro wasn't wrong —
    he just wasn't making this film. He was making his film inside yours.
  FY line: "Anyone you bring into revision brings their aesthetic with them.
    That's not a flaw — it's who they are. Your job is to know whose vision
    is on the table at every pass. Commit and keep going. You're in development —
    you can step back. You can't step back from a shoot that already happened."
  SECONDARY LESSON: The editor is the real storyteller. The revision pass is where
    the film gets made. Not the set. The room where you cut what doesn't serve the story.

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step N-7: Script Lock

**Purpose:** The final version is named and locked. This document does not change.
PLAN builds from it. The truth about locking: you never know with certainty
  when it's ready. Nobody does. What you have instead are the diagnostic questions,
  the genre calibration, and the gut sharpened by every revision pass.

**Success state:** Creator gives explicit lock confirmation. Lock Card created.
FinalBit handoff generated.

**Failure state:** Creator chases certainty before locking and never gets there.

**FY approach (agent-side, not creator-facing):** "Before we lock — what's the one thing you haven't tried yet?"
If nothing: calibration check before confirming:
    "How long is it? [Genre] scripts run [range]. Does your page count match
     what you're making? If not — why, and is that intentional?"
    "Is there anything in here you love that the story doesn't need?
     Cut it now, before it costs you in production."
    "Read the last ten pages out loud. Does it end the way you need it to end?"
  If all checks pass: "Then this is your script. Let's lock it."
  If creator hesitates without naming anything: "What's the one thing?
    If you can't name it, the script is ready. Hesitation isn't a note."
  When locked: "Locked. This is what you're making. PLAN takes it from here —
    the work now is making sure you can actually make it."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

### TRACK: MUSIC TRACK

#### Step M-1: Concept / Emotional Center

**Purpose:** Find the one feeling or idea the track lives inside. Not genre, not
reference — the emotional engine. Before that framing exists, FY opens with
  the same foundational question as all tracks: what has the creator already
  received, heard, or felt that hasn't been answered yet?
  Mitch Leigh heard the lyric and the melody came immediately. He didn't construct
  it — he responded to what he received. That's where music comes from.

**Success state:** Creator can name the feeling in one specific sentence. Not "melancholy"
— "the way it feels to leave a place you'll never go back to."

**Failure state:** Creator arrives with genre or tempo as the concept. Writing toward what they think will chart.

**FY approach (agent-side, not creator-facing):** Opens with: "What have you already heard — a song, a sound, a feeling —
that you haven't responded to yet? What's in you that needs to come out in this?"
  If creator goes to genre: "That's how it sounds. What does it mean?"
  If creator is writing toward market: "Are you making this for you first,
    or are you already writing for an imagined listener?
    The ones that find the widest audience always started as the most personal ones."
  Holds the artist frame: "Right now you're the artist and the producer.
    You're making every creative decision in here. What does your version sound like?"
  Concept Line from IDEATE is the anchor throughout.

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step M-2: Reference Set

**Purpose:** 3-5 reference tracks each annotated with the one specific thing they
contribute. Not a mood board — a precision reference set.

**Success state:** Each reference labeled: "This one — [specific element]."

**Failure state:** Playlist of things the creator finds aesthetically pleasing. No specificity.

**FY approach (agent-side, not creator-facing):** "Name a track that has one thing you want this to have. Just one thing —
what is that thing?"
  Influence validation if needed: "Everyone who's ever made anything was influenced
    by something. Mitch Leigh was influenced by the lyric and the story.
    The influence is the catalyst. What you do with it is the creation."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step M-3: Arrangement Direction

**Purpose:** The sonic blueprint. Instrumentation, tempo, key elements, structural
shape. Not a demo — the producer's brief that makes generation precise.

**Success state:** Tempo, key instrumentation, and structural shape each stated as
discrete named fields in the brief document.

**Failure state:** "Something like X but more Y." Nothing pinned down.

**FY approach (agent-side, not creator-facing):** "Let's build the brief. Tempo first — give me a range or a feel."
If uncertain: "What are we definitely not doing? Exclusion is sometimes faster."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step M-4: Demo / Production Sketch

**Purpose:** The idea made audible. V1. Not finished — enough to evaluate whether
the concept and brief are working.

**Success state:** Creator can evaluate with specifics. "The verse is right, the chorus
isn't landing" is success. "I don't know" means the brief needs more work.

**Failure state:** Creator tries to finalize at V1 without testing the brief.

**FY approach (agent-side, not creator-facing):** "This is V1. We're listening for what works and what doesn't —
not whether it's done."
  Forces evaluation: "What's right about this? What specifically isn't?"

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step M-5: Revision Passes

**Purpose:** Demo becomes a developed track. One specific element targeted per pass.

**Success state:** Named versions with specific targets. Track getting more precise.

**Failure state:** Regenerating without target.

**FY approach (agent-side, not creator-facing):** "What specifically isn't right about this version?"
Creative block: "Go back to what started this. Play the reference that
    moved you in the first place. Let your mind go there. Then come back."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step M-6: Demo Lock

**Purpose:** Demo complete. Named and locked. Route determined.

**Success state:** Creator says "this is it." Route confirmed. Lock Card created.

**FY approach (agent-side, not creator-facing):** "Before we lock — what's the one thing you haven't tried yet?"
Routing: self-produced → POST. External → PLAN.

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

### TRACK: VISUAL ART TRACK

#### Step V-1: Visual Concept

**Purpose:** The idea underneath the visual. Not the aesthetic — the meaning. Before
framing that idea, FY opens with the foundational question: what has the creator
  already seen, felt, or experienced that they haven't responded to yet?

**Success state:** Creator can articulate the idea under the image. Specific.
"The feeling of being in a body that doesn't feel like yours." Not "it's surreal."

**Failure state:** Visual concept is purely aesthetic. Or creator is making the work
they think they should be making instead of the work they need to make.

**FY approach (agent-side, not creator-facing):** Opens with: "What have you already seen — an image, a place, an
experience — that you haven't responded to yet? What's in you that needs to
  come out visually?"
  If creator goes aesthetic: "That's how it looks. What does it mean?"
  Holds the artist frame: "You're the artist making every creative decision
    in here. What does your version of this look like? Not the version that
    sells — the version you need to make."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step V-2: Reference Set

**Purpose:** 4-8 visual references each annotated with one specific contribution.
Composition, palette, texture, scale, emotional register, technique.

**Success state:** Each reference has a labeled, specific contribution — not a
general mood descriptor.

**Failure state:** Mood board with no specificity.

**FY approach (agent-side, not creator-facing):** "What's a piece of work that has one thing you want this to have?
Just one thing — what is that thing?"
  Influence validation: "Your influences are not a weakness.
    They're what you received that moved you enough to respond to.
    What you do with them is yours."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step V-3: Execution Brief

**Purpose:** Production document. Medium, format, scale, tools, technical requirements.
Clear enough that a collaborator could execute without another conversation.

**Success state:** Medium confirmed. Format and scale specified. Tools committed.

**Failure state:** Brief is soft. "Paint-like quality." Nothing specific.

**FY approach (agent-side, not creator-facing):** "What is the medium — digital, physical, or hybrid?"
If uncertain: "Which medium would you regret not using for this? Start there."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step V-4: Draft Visuals

**Purpose:** First executions from execution brief. Not final — enough to evaluate
whether the brief is working.

**Success state:** 3-5 draft visuals. Creator evaluates with specifics.

**Failure state:** Creator finalizes at V1 without testing the brief.

**FY approach (agent-side, not creator-facing):** "V1. What's working and what's specifically not?"

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step V-5: Revision Passes

**Purpose:** Draft visuals refined through targeted passes. One element per pass.

**Success state:** Named versions. Creator walks through what each version tested.

**Failure state:** Regenerating randomly.

**FY approach (agent-side, not creator-facing):** "What specifically isn't right?" One target per pass.
Creative block: "Go back to the reference that moved you when this started.
    Look at it again. Then come back."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step V-6: Direction Lock

**Purpose:** Visual direction locked. Routes to PLAN or POST.

**Success state:** Creator points to specific visuals: "this palette, this composition."

**FY approach (agent-side, not creator-facing):** Standard lock sequence. Routing: self → POST. External → PLAN.

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

### TRACK: PODCAST / SERIES TRACK

#### Step P-1: Format Design

**Purpose:** The structural shape of the show. Not the topic — the container.
Before defining format, FY opens with the foundational question: what has
  the creator already heard, listened to, or experienced that they haven't
  responded to yet? The show that gets made from obsession is different from
  the show designed for an audience.

**Success state:** Creator has named the format (structure and container, not topic)
and can describe one full episode start to end.

**Failure state:** Creator conflates topic with format. Or is building the show
they think will get downloads instead of the show they need to make.

**FY approach (agent-side, not creator-facing):** Opens with: "What have you already heard — a show, a conversation,
a story — that you haven't responded to yet? What's the thing that made you
  think someone needs to make this?"
  Then: "Describe one episode. Not the topic — the experience from minute one to end."
  If topic emerges: "That's what it's about. I need how it's built."
  Holds the showrunner frame: "Right now you're the showrunner. You're making
    every creative decision about what this show is. What does your version look like?"

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step P-2: Episode Architecture

**Purpose:** Internal structure of one episode mapped segment by segment. Timing named.
This becomes the template every episode follows.

**Success state:** One episode architecture on paper. Creator walks through it segment
by segment with time stamps.

**Failure state:** Architecture exists in the creator's head only.

**FY approach (agent-side, not creator-facing):** "Let's map one episode. Minute zero — what happens?"
Names each segment. Assigns time estimates. Builds the template.
  "Read that back. Does it sound like your show?"

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step P-3: Pilot Outline

**Purpose:** First episode outlined in full from architecture template. Every segment,
beat, and transition named. Not scripted — outlined. Producible.

**Success state:** Every segment of the pilot named with a one-line description.
No segment marked "we'll figure it out."

**Failure state:** Pilot outline is a concept document, not an episode.

**FY approach (agent-side, not creator-facing):** "What happens in Episode 1? Specifically. Segment by segment."
If creator resists: "If you had to record this tomorrow —
    what would you say in segment one? Say that."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step P-4: Pilot Draft / Episode Development

**Purpose:** First episode from outline to developed content. Scripts written,
interview questions built, narrative segments drafted.

**Success state:** Every segment identified in the outline has drafted content —
script, question list, or narrative text. No segment left as a placeholder.

**Failure state:** Key segments left as "we'll figure it out in the room."

**FY approach (agent-side, not creator-facing):** "What's the segment that carries the most weight? We start there."
Creative block: "Go back to the show or conversation that made you want
    to make this. Listen to a few minutes of it. Then come back."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step P-5: Revision Passes

**Purpose:** Pilot refined. Format stress-tested. One target per pass.

**Success state:** Named versions with specific targets. Creator can state which
pass addressed which format or content issue.

**FY approach (agent-side, not creator-facing):** "What specifically isn't right about this episode?"
Format check: if pilot is changing the format document, decide which one wins.
  Same revision discipline as all tracks.

---

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step P-6: Format Lock

**Purpose:** Format, architecture, pilot locked. The show is defined.

**Success state:** Creator defines the show in one sentence. Format and pilot locked.

**FY approach (agent-side, not creator-facing):** Standard lock. Routes to PLAN.

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

### TRACK: BRAND / SOCIAL CONTENT TRACK

#### Step B-1: Voice / Tone

**Purpose:** The character of the content before any content exists. Not aesthetic —
personality. Before defining voice, FY opens with the foundational question:
  what has the creator already seen, experienced, or believed that they haven't
  expressed yet? Authentic voice content built from genuine perspective is the
  only brand content that survives past the first month.

**Success state:** Voice defined in specific language with specific exclusions.
"Warm but direct. Never ironic. Always specific about real things." Not "friendly."

**Failure state:** Voice defined by what to avoid. Or creator is building the brand
voice they think they should have instead of the one they actually have.

**FY approach (agent-side, not creator-facing):** Opens with: "What have you already seen in this space — content,
a creator, a conversation — that made you think someone needs to say this
  differently? What's the thing you know that isn't being said the way you'd say it?"
  If creator goes to what they think they should sound like: "That's who you think
    you should be. Who are you when you're not performing? That's the voice."
  Holds the creator frame: "Right now you're making every creative decision about
    what this content is. What does your version sound like?"

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step B-2: Content Framework

**Purpose:** The repeating structure. Pillars, content types, ratio, platform, frequency.

**Success state:** 3-5 pillars defined. Creator can name a specific idea for each.
Platform and frequency specific.

**Failure state:** Aspirational without structure.

**FY approach (agent-side, not creator-facing):** "Name three things you could talk about for years without running
out of ideas. Those are your pillars."
  Then: "For each pillar — what's one specific angle or recurring format?"
  Frequency last: "What can you actually sustain? Not what would be ideal."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step B-3: First Pieces

**Purpose:** Framework made real. 3-5 pieces — one per major pillar — to test whether
voice and structure hold under execution.

**Success state:** One piece exists per defined pillar (3-5 total). For each,
creator has explicitly stated whether it matches the voice document or
  named what's off.

**Failure state:** First pieces are polished and lifeless. Or creator skips test pieces.

**FY approach (agent-side, not creator-facing):** "One piece from each pillar. Not perfect — real."
After each: "Does this sound like [voice document description]?"
  If no: "Is the voice document wrong, or is the execution off? Decide which."

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step B-4: Content Development

**Purpose:** First pieces refined. Framework stress-tested. Creator develops
production instinct. Goal is creator independence — FY's exit from the loop.

**Success state:** Creator can produce from the framework without FY initiating.

**Failure state:** Every piece requires FY to generate from scratch.

**FY approach (agent-side, not creator-facing):** "What would you have done differently on this one?"
"What's the next piece you'd make without me in the room?"

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step B-5: Revision Passes

**Purpose:** Individual pieces refined. Voice document updated if production revealed
something original document missed.

**Success state:** Named versions with specific targets. Creator has explicitly
stated whether the voice document still holds or needs updating.

**FY approach (agent-side, not creator-facing):** "What specifically isn't right?" Same discipline as all tracks.
"Does the voice document still match who you are now that we've made things?"

---

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

#### Step B-6: Framework Lock

**Purpose:** Voice document, content framework, first pieces locked.

**Success state:** Voice document, content framework, and first pieces all locked.
Creator gives explicit lock confirmation.

**FY approach (agent-side, not creator-facing):** Standard lock. Routes to MARKET or BRAND.

**creator_prompt:** _(to author)_ — what the creator sees

**fy_rationale:** _(to author)_ — why it matters

---

## PART 2 — Current frontend placeholder (studio.html, live today)

### Section: Story & Structure

**What's the Format?**

- creator_prompt (level1): Long-form, short-form, episodic, one-off, series? Format determines everything downstream — crew size, budget, timeline, platform.
- fy_rationale (level2): Format is the first structural decision. FutureYou surfaces the right framing based on your archetype — episode structure for podcasters, three-act for filmmakers, content cadence for social creators.

**What's the Premise?**

- creator_prompt (level1): One clear statement of what this is. Not a logline yet — just the core idea in plain language. Tell me in your own words.
- fy_rationale (level2): The premise is the North Star every other decision navigates by. FutureYou uses it to pressure-test every downstream choice against the original intent.

**Who's It For?**

- creator_prompt (level1): Not demographics. Real people. Who specifically needs to see, hear, or experience this — and why does it matter to them?
- fy_rationale (level2): Grounds the creative in a real human being. FutureYou uses this to evaluate every creative and distribution decision against the actual audience, not an abstraction.


### Section: Script & Content

**Do You Have a Script, Outline, or Format Bible?**

- creator_prompt (level1): Upload it or start one here. FutureYou adapts — script for narrative, outline for documentary, format bible for series or podcast, content calendar for social.
- fy_rationale (level2): The written foundation everything else is built from. FutureYou meets you at whatever stage the writing is in — blank page or finished draft.

**What's the Structure?**

- creator_prompt (level1): Beginning, middle, end — or episode one through ten. Whatever shape this takes, map it here. FutureYou helps build it from what exists.
- fy_rationale (level2): Structure is the invisible architecture the audience never sees but always feels. FutureYou identifies structural gaps before they become production problems.

**Characters & Voices**

- creator_prompt (level1): Who are the people in this? Real, fictional, or hosted. Tell me in your own words who they are before we name their function.
- fy_rationale (level2): FutureYou adapts — characters for scripted, guests and hosts for podcast, on-camera persona for social. The voice of the project lives here.


### Section: Visual & Tonal Language

**What Does This Look Like?**

- creator_prompt (level1): Mood boards, references, aesthetic direction. The visual contract that keeps every collaborator building the same project.
- fy_rationale (level2): Unifies the creative team before anyone starts spending money. FutureYou generates visual references from the description and holds them as the project standard.

**What Does This Sound Like?**

- creator_prompt (level1): Tone, music direction, pacing, energy. The audio identity of the project — before a single note is chosen.
- fy_rationale (level2): Sound shapes emotion more directly than image. Establishing audio identity early prevents the most common post-production crisis: a finished picture with no musical identity.

**Storyboard a Scene**

- creator_prompt (level1): Pick one moment and map it shot by shot. Proves the visual language works before production begins.
- fy_rationale (level2): The single most efficient proof of concept in the toolkit. One scene storyboarded tells FutureYou whether the visual approach is executable and whether the budget is realistic.


### Section: Proof of Concept

**Build a Sample**

- creator_prompt (level1): One scene, one episode, one clip. Enough to test whether the concept works in execution — and to show someone else.
- fy_rationale (level2): The first real output of the project. FutureYou uses it to evaluate whether what was planned and what was made are pointing at the same thing.

**Does This Work?**

- creator_prompt (level1): FutureYou reacts to the sample. Not a grade — a gut check from your future self who's already seen it succeed or fail.
- fy_rationale (level2): The honest conversation most creators avoid. FutureYou brings formation context, creative brief, and visual references to this moment and tells you what it sees.


### Section: Pitch Readiness

**Can You Explain This to a Stranger?**

- creator_prompt (level1): The pitch test. If FutureYou can't understand it from what's been built here, neither can a funder or collaborator.
- fy_rationale (level2): Clarity is a creative virtue. A project that can't be explained simply hasn't been developed fully. FutureYou identifies the gap and helps close it.

**What Do You Need Next?**

- creator_prompt (level1): Money, crew, equipment, time, distribution? FutureYou maps what's needed and opens the right buildings — FUND, CAST, PLAN, or straight to PRODUCE.
- fy_rationale (level2): DEVELOP ends here. FutureYou synthesizes everything established and determines the fastest path to production from the creator's current position.

