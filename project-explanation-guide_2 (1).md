# Project Explanation Guide — For Your College Guide Review

**Project:** Personalized AI-Based Narrative Content Creation and Voice Generation Using Generative AI
**Team:** 3–4 final-year CSE students | **Timeline:** under 3 months | **Budget:** zero
**Purpose of this document:** to let every team member confidently explain the *what*, the *why*, and the *risks* of this project to a guide or evaluator — starting from absolute zero knowledge.

---

# PART 0 — The One-Paragraph Version (memorize this)

> "Our project takes a person's worry — typed or spoken — and turns it into a short, personalized, encouraging story that is grounded in real psychology research, and then delivers that story as text, an image, and a spoken voice. The user speaks their worry, our system converts the speech to text, analyzes the emotion behind it, detects the negative thinking pattern inside it, looks up a scientifically-backed technique that applies to that pattern, generates a personalized narrative using that technique, creates a matching image and a voice narration, and saves the whole experience so the user can revisit it later."

If you can say that sentence clearly, you have already passed the first question every evaluator asks: *"So what does it actually do?"*

---

# PART 1 — The Complete Workflow, Step by Step

Below is exactly what happens from the moment a user opens the app to the moment they see the final result. Read it as a story. Nothing is skipped.

### Step 0 — The user opens the web page
A simple web page loads in the browser. It has a text box ("Type what's on your mind") and a microphone button ("Or say it out loud"). This page is built with HTML (the structure), CSS (the styling), and JavaScript (the behavior — recording audio, sending data, showing results).

### Step 1 — The user gives input
Two possible paths:
- **Typed:** the user types "I am scared I will fail my placement interviews. I don't think I'm good enough."
- **Spoken:** the user clicks the microphone, speaks the same sentence, and the browser records a short audio file.

### Step 2 — The input travels to our backend
JavaScript sends the text (or the audio file) to our Python program running on a server. That Python program is built with Flask. Flask's only job is to be the receptionist: it receives requests from the web page, passes them to the right internal function, and sends the answer back.

*Simple words:* the frontend is what the user sees; the backend is the brain that does the actual work; Flask is the messenger between them.

### Step 3 — Speech becomes text (only if the user spoke)
If audio was sent, Whisper converts the recording into written text. Output: a plain string of text.
If the user typed instead, this step is skipped entirely. **From this point on, every path is identical** — the rest of the system only ever deals with text.

*This is an important design point to tell your guide:* voice input is just an optional front door. It does not create a second pipeline.

### Step 4 — Language analysis
The text goes into spaCy, a text-analysis tool. It breaks the sentence into words, identifies which word is the subject, which is the verb, whether there is a negation ("don't", "never"), and identifies names of things (exams, interviews, family).

At the same time, our own hand-written rules scan for **negative thinking patterns** (psychologists call these "cognitive distortions"). Examples:
- Words like *always, never, every time* → "all-or-nothing thinking"
- Phrases like *I will fail, it's going to be a disaster* → "predicting the worst" (fortune-telling / catastrophizing)
- Phrases like *I'm not good enough, I'm useless* → "self-labeling"

**Output of this step:** `["fortune_telling", "self_labeling"]`

### Step 5 — Emotion detection
The same text goes into DistilBERT, a small AI model we train ourselves to recognize emotions.

**Output of this step:** `{"fear": 0.61, "sadness": 0.22, "anger": 0.04, ...}` — meaning "this text is mostly fear, with some sadness."

### Step 6 — The Context Engine builds a "Case Frame"
This is plain Python code — no AI. It simply collects everything we know so far into one neat package:

```
Case Frame:
  original text : "I am scared I will fail my placement interviews..."
  emotions      : fear (high), self-doubt (medium)
  distortions   : fortune_telling, self_labeling
  goal          : succeed in placement interviews / feel confident
  summary       : "fear of interview failure driven by low self-belief"
```

*Why this matters:* every later step reads only this one package. That means each team member can build their part separately, as long as everyone agrees on what this package looks like. This is the single most useful design decision in the whole project.

### Step 7 — Choosing the right psychological technique
We have built a small library of "concept cards" — about 15 files, each describing one evidence-backed psychological technique. Each card contains: what the technique is, the research paper it comes from, how strong the evidence is, when it applies, how to apply it, an example, and its limitations.

The system compares the Case Frame against these cards and picks the best matches.

For our example, it might pick:
- **Cognitive reframing** (primary) — because a distorted thought was detected
- **Self-efficacy building** (supporting) — because self-doubt is present
- **Implementation intentions** (behavioral step) — because the user needs a concrete next action

**Output — a "Reframe Plan":** the Case Frame + the chosen techniques + the narrative structure to follow.

*This step is the actual heart of the project.* Without it, we would just be a motivational quote generator. With it, every single output can be traced back to a named psychological principle and a real research citation. Say this sentence in your review — it is your strongest point.

### Step 8 — Generating the personalized narrative
The Reframe Plan is turned into a structured instruction and given to FLAN-T5, a text-generation model we adapt for our task. It writes a short narrative following a fixed structure:

1. **Current reality** — acknowledge the worry honestly, without dismissing it
2. **Reframe** — offer a more accurate and balanced way to see it
3. **Desired future** — describe the outcome the user actually wants
4. **Behavioral direction** — one concrete, small, doable next action

**Critical rule:** the system must never say "Don't worry, you will definitely succeed." That is an empty promise. It should say something closer to: *"You have prepared for six months. Feeling nervous before an interview is your body preparing, not a prediction of failure. Tomorrow evening, you will do one mock interview with a friend."*

### Step 9 — Generating the image
A short visual description is extracted from the "desired future" part of the narrative and given to Stable Diffusion, which produces one image representing that hopeful scene.

### Step 10 — Generating the voice
The narrative text is given to Kokoro, which reads it aloud in a calm, natural voice and produces an audio file.

### Step 11 — Saving everything
Everything — the original input, the Case Frame, the chosen techniques, the narrative text, the image file path, and the audio file path — is saved into SQLite, a simple file-based database.

### Step 12 — Showing the result
Flask sends the results back to the web page. The user now sees the narrative text, the generated image, and a play button for the voice narration.

### Step 13 — Revisiting past sessions
A "My Journey" page lists all previous entries from the database. The user can reopen any past narrative, image, and audio. Over time, the system also notices recurring themes ("you have raised career confidence three times") and mentions them in future narratives — this is our personalization.

---

# PART 2 — Every Technology Explained (in the exact format your guide asked for)

## 2.1 — HTML, CSS, JavaScript

**What it does:** HTML builds the structure of a web page (boxes, buttons, text). CSS makes it look good (colors, spacing, fonts). JavaScript makes it react (record audio, send data, update the screen without reloading).

**Where it fits:** The visible app — the input page, the results page, the history page.

**Why we chose it:** It is the absolute foundation of all web development. There is nothing to install, nothing to compile, and every browser understands it directly. For a beginner team, you can see the effect of a change instantly.

**Why not another similar option:** React, Vue, or Angular are popular frontend frameworks. We are not using them because they add a whole extra layer — Node.js, npm packages, a build step, and a new mental model — before you can display a single button. Our pages are simple (three screens). A framework would cost us two weeks and buy us nothing.

**Possible drawback:** As the page grows, plain JavaScript can become messy and hard to organize.

**How we handle it:** Keep it to three small pages. Split JavaScript into separate files by purpose (`recorder.js`, `results.js`, `history.js`). Since our screens are simple, the code never grows large enough to become a problem.

---

## 2.2 — Python

**What it does:** The programming language our entire backend and all AI work is written in.

**Where it fits:** Everything on the server side.

**Why we chose it:** Every AI/ML library in the world is written for Python first. Whisper, spaCy, DistilBERT, FLAN-T5, Stable Diffusion, and Kokoro all ship as Python libraries. Choosing anything else would mean losing access to all of them.

**Why not another similar option:** Java or C++ are faster at raw computation, but almost no AI model releases a ready-to-use library for them. You would spend the whole project on plumbing instead of on AI.

**Possible drawback:** Python is slower than compiled languages.

**How we handle it:** It does not matter here. In our project, 99% of the time is spent inside the AI models (which are written in optimized C++ under the hood), not in our Python code. Our Python is just directing traffic.

---

## 2.3 — Flask (backend framework)

**What it does:** Lets a Python program listen for requests from a web browser and send answers back.

**Where it fits:** Step 2 and Step 12 — receiving user input and returning results.

**Why we chose it:** It is small enough that you can understand *all of it*. A working Flask server is about 10 lines of code. When your evaluator asks "explain your backend," you can explain every line honestly.

**Why not another similar option:**
- **Django** is far more powerful, but it forces a large project structure with many folders and concepts (apps, models, migrations, admin, ORM) that we simply do not need. We are not building an admin panel or a user-management system.
- **FastAPI** is modern and slightly faster, and would be a defensible choice. But it introduces async programming and type annotations — extra concepts for a beginner team, for a speed benefit we will never notice, because our bottleneck is the AI models, not the web layer.

**Possible drawback:** Flask handles one request at a time by default. If two users click "Generate" at the same moment, the second one waits.

**How we handle it:** For a college demo with one user at a time, this is a non-issue. If you want to be thorough, mention in your report that a production version would use a proper server (Gunicorn) with multiple workers, or a background task queue. Knowing the limitation and its solution earns marks; solving it now wastes time.

---

## 2.4 — SQLite (database)

**What it does:** Stores our data in an organized way so we can retrieve it later. It is a database that lives inside a single file on disk.

**Where it fits:** Step 11 (saving) and Step 13 (revisiting history).

**Why we chose it:** Zero setup. No server to install, no username, no password, no configuration. Python has it built in — `import sqlite3` and you are done. The entire database is one file you can copy, back up, or email.

**Why not another similar option:**
- **MySQL / PostgreSQL** require installing and running a separate database server, creating users and permissions, and configuring connections. That is a real installation burden on four different laptops, and a real source of "it works on my machine" problems.
- **MongoDB** stores flexible documents, which sounds convenient, but our data is highly structured (users, sessions, narratives) and relational. SQL fits it better, and SQL is what you have already studied in your DBMS course — you can explain it confidently.

**Possible drawback:** SQLite is not designed for many people writing to it at the same time.

**How we handle it:** We have one user at a time in a demo. Non-issue. Mention in the report that migrating to PostgreSQL would be the first step if the app were deployed publicly — the code change is small because we will write our database access in one file (`crud.py`).

---

## 2.5 — Whisper (speech-to-text)

**What it does:** Listens to an audio recording and writes down what was said.

**Where it fits:** Step 3 — only when the user speaks instead of typing.

**Why we chose it:** It is free, runs entirely on our own laptop with no internet and no API key, handles Indian-accented English noticeably better than most older tools, and it is genuinely the best open speech model available at this quality level.

**Why not another similar option:**
- **Google Speech-to-Text API / Azure Speech** are accurate but are paid cloud services requiring a credit card. Our project constraint is zero paid APIs.
- **Vosk / CMU Sphinx** run offline and are much lighter, but their accuracy on accented, emotional, conversational speech is clearly worse — and our whole pipeline depends on getting the user's words right.

**Possible drawback:** The larger Whisper models are slow on a laptop without a graphics card. `whisper-medium` on a CPU can take a minute or more for a 30-second clip. That would kill a live demo.

**How we handle it:** Use `whisper-base` or `whisper-small` (not medium or large), and run them through a library called `faster-whisper`, which does the same job several times faster on a CPU. Also cap recordings at 30 seconds in the browser. And always keep the text box available — if the microphone or the model misbehaves during your demo, you type instead and the demo continues perfectly.

---

## 2.6 — spaCy (language analysis)

**What it does:** Breaks a sentence into its grammatical parts — words, subjects, verbs, negations, named things.

**Where it fits:** Step 4 — understanding the structure of what the user wrote, and hosting our negative-thinking-pattern rules.

**Why we chose it:** It is fast, well-documented, easy to install, and gives us exactly what our rules need. It also has a built-in pattern-matching tool that is perfect for detecting thinking patterns.

**Why not another similar option:**
- **NLTK** is more of a teaching/research toolkit — it needs a lot more manual assembly to do the same job, and is slower.
- **Using a large AI model for this instead** would be overkill: it would be slower, harder to explain, and would make our system's decisions invisible. Rules are transparent — you can point at exactly why a pattern was flagged.

**Possible drawback:** Rules are rigid. They will miss ways of expressing a thought that we did not anticipate.

**How we handle it:** Accept it openly. Collect a test set of about 100–150 example sentences, measure how many patterns the rules correctly catch, and report that number honestly in your evaluation. Showing a measured 70% recall with an honest analysis is *far* stronger in a review than claiming a vague "it works well." Also always include a safe default: if no pattern is detected, fall back to a general reframing technique rather than crashing.

---

## 2.7 — DistilBERT (emotion detection) — **one of our two real AI training tasks**

**What it does:** Reads a sentence and predicts which emotions it expresses.

**Where it fits:** Step 5.

**Why we chose it:** DistilBERT is a compressed version of BERT — about 40% smaller and 60% faster, while keeping around 97% of the accuracy. That trade is perfect for us: we can actually train it on a free Google Colab GPU in under an hour, and run it on a plain laptop afterwards.

**Why not another similar option:**
- **Full BERT or RoBERTa** are slightly more accurate but noticeably heavier to train and run — not worth it for a small accuracy gain we cannot even measure meaningfully.
- **VADER or TextBlob** are simple word-list-based sentiment tools. They only tell you positive/negative/neutral. We need actual emotions (fear vs. sadness vs. anger) because different emotions require different psychological responses. They also completely fail on sarcasm and context.
- **A large language model** would work but cannot be trained or run on our hardware.

**Possible drawback:** The public dataset we will train on (GoEmotions — 58,000 labeled Reddit comments, free) does not contain a label for "self-doubt," which is central to our project.

**How we handle it:** Be honest and explicit about this. We train the model on the emotions the dataset genuinely contains (fear, sadness, anger, joy, etc.), and we derive "self-doubt" separately as a documented rule combining detected emotions with specific phrases ("not good enough", "I can't", "I'm useless"). Write this down in your dataset documentation. Claiming your model detects a label it was never trained on is the kind of thing a sharp evaluator will catch — describing the limitation and your workaround is the kind of thing that earns respect.

---

## 2.8 — FLAN-T5 (narrative generation) — **our second real AI training task, and our biggest risk**

**What it does:** Takes an instruction and writes text in response.

**Where it fits:** Step 8 — writing the actual personalized narrative.

**Why we chose it:** FLAN-T5 is already trained to follow instructions, it is free and open, and the `base` size (250 million parameters) is small enough to adapt on a free Colab GPU and then run on a normal laptop.

**Why not another similar option:**
- **GPT-2** is older and was never trained to follow instructions — it just continues text, so it drifts off-topic quickly.
- **LLaMA / Mistral (7 billion parameters)** would produce much better writing, but need a serious graphics card to run at usable speed. They are not realistic for us.
- **Paid APIs (GPT-4, Claude, Gemini)** would produce the best writing by far — but they violate our zero-paid-API constraint, they require internet during the demo, and, most importantly, they would reduce our project to writing a clever prompt. There would be no ML contribution of our own to defend in the review.

**Possible drawback — read this one carefully, it is the single biggest threat to your project:** FLAN-T5-base is a *small* model. Out of the box it tends to produce short, flat, generic sentences. It is not going to write beautiful, emotionally moving prose. If you build your entire narrative on raw FLAN-T5 output and demo it, there is a real chance it looks disappointing.

**How we handle it — the hybrid approach (this is important):**
Do not ask the model to invent the whole narrative from nothing. Instead:
1. The **structure** comes from our knowledge base — a proven four-beat skeleton (current reality → reframe → desired future → concrete action), with sentence frames drawn from the chosen psychological technique's card.
2. The **personalization** comes from FLAN-T5 — it rewrites each beat using the user's actual words, their specific situation, and their emotional state.

This means the worst case is a slightly stiff but always correct, always relevant, always well-structured narrative — never gibberish. And the best case is genuinely personal writing. This hybrid design also makes the system *far* easier to explain and defend than a black box, because you can show exactly which part of the output came from which source.

Additionally: train with LoRA (a technique that trains a few small extra layers instead of the entire model — dramatically cheaper, only a few megabytes to save), and build a training set of 300–600 example pairs yourself. Keep `flan-t5-small` ready as a fallback if `base` proves too slow on your demo laptop.

---

## 2.9 — Stable Diffusion (image generation) — **your biggest practical/hardware risk**

**What it does:** Creates an image from a text description.

**Where it fits:** Step 9.

**Why we chose it:** It is the only genuinely free, open, locally-runnable image generator of good quality.

**Why not another similar option:** DALL·E and Midjourney are paid cloud services — both violate our constraints and require internet.

**Possible drawbacks — there are three, and they are all serious:**
1. **Size:** the model download is roughly 4 GB.
2. **Speed:** standard Stable Diffusion 1.5 on a laptop *without* a graphics card takes **2 to 5 minutes per image**. In a live demo, that is unacceptable — you cannot stand in silence for four minutes.
3. **Memory:** running it alongside all your other loaded models will exhaust an 8 GB laptop.

**How we handle it — use all four of these together:**
1. **Use SD-Turbo or an LCM model instead of standard SD 1.5.** These are variants specifically designed to produce an image in 1–4 processing steps instead of 50. This is a 10–20× speedup and is the single most important fix. This is not changing your stack — it is still Stable Diffusion, just a faster released version of it.
2. **Generate the image in the background.** Show the narrative text immediately, start the voice playing, and let the image appear when ready. The user is never staring at a blank screen.
3. **Pre-generate a small fallback library.** Before your demo, generate 15–20 good images covering your common themes (career, exams, family, confidence, health). If live generation fails or is slow on demo day, the system shows a matching pre-made image and the demo continues smoothly. Document this fallback in your report as a deliberate reliability feature — because that is exactly what it is.
4. **Never load Stable Diffusion at the same time as everything else** (see the RAM problem in Part 3).

---

## 2.10 — Kokoro-82M (voice generation)

**What it does:** Converts written text into natural-sounding spoken audio.

**Where it fits:** Step 10.

**Why we chose it:** At 82 million parameters it is remarkably small — it runs on a plain CPU at roughly real-time — while sounding dramatically more natural than traditional robotic text-to-speech. For a project whose entire goal is emotional comfort, a robotic voice would undermine the experience.

**Why not another similar option:**
- **gTTS** requires an internet connection (it calls Google's servers) and sounds flat.
- **pyttsx3** works fully offline and is extremely easy, but sounds robotic.
- **Coqui TTS** is good but heavier and its project maintenance has been uncertain.
- **ElevenLabs** sounds the best but is a paid API.

**Possible drawback:** Installation can be fiddly. Kokoro relies on a text-to-phoneme step that typically needs a system-level tool (`espeak-ng`) installed separately, which is a classic beginner-blocking error.

**How we handle it:** Install and verify Kokoro on all team laptops in **Week 1**, before you build anything around it. Do not leave it to Week 7. Write down the exact installation commands that worked in your README. Keep `pyttsx3` wired in as a one-line fallback — if Kokoro fails on demo day, audio still plays.

---

## 2.11 — Docker (containerization)

**What it does:** Packages your application and everything it needs into a box that runs identically on any computer.

**Where it fits:** Deployment and submission — not in the user's workflow at all.

**Why we chose it:** It looks professional in a report and solves "it works on my laptop but not yours."

**Why not another similar option:** A plain Python virtual environment plus a `requirements.txt` file achieves 90% of the same benefit with 5% of the effort.

**Possible drawback — be realistic:** For a beginner team, Docker is a genuine time sink. And your project has roughly 5–6 GB of AI models. Putting those inside a Docker image makes it enormous and slow to build; keeping them outside means learning about volume mounts. Either way it is an extra concept to learn while you are already learning eight others.

**How we handle it:** **Do Docker last, in the final week, and treat it as optional.** Build and demo your project using a normal Python virtual environment. If time remains at the end, containerize it. If time does not remain, write in your report that a `requirements.txt` plus documented setup steps provides reproducibility, and that containerization is planned future work. No evaluator will fail you for that. Many will fail you for a project that does not run because you spent Week 4 fighting Docker.

---

# PART 3 — Problems Nobody Warns Beginners About (find these now, not in Week 10)

These are the failures that actually sink student projects. Each one has a simple fix.

### Problem 1 — Your laptop runs out of memory. (Highest technical risk.)
Whisper (~150 MB) + DistilBERT (~250 MB) + FLAN-T5-base (~1 GB) + Stable Diffusion (~4 GB) + Kokoro (~350 MB) is around 6 GB of models. If your code loads all of them into memory when the server starts, an 8 GB laptop will freeze or crash.

**Solution:** Load each model **only when it is needed**, and release it afterwards. Write one small file called `model_manager.py` that owns this. Better still, generate the image in a **separate process** so its memory is fully released the moment it finishes. Test this on your *weakest* team laptop in Week 2 — not on the best one.

### Problem 2 — The demo is too slow and feels broken.
Add up the worst case: Whisper 15s + emotion 1s + narrative 10s + image 180s + voice 10s = over three minutes of silence.

**Solution:** Three fixes together. (a) Use SD-Turbo for images. (b) Stream results as they are ready — show the text the moment it exists, then the audio, then the image. (c) Show a progress indicator that names the current step ("Understanding your emotions…", "Choosing a technique…"). A user who can see progress perceives the same wait as far shorter. Target: text in under 15 seconds, everything complete in under 45.

### Problem 3 — You have no mental-health safety handling. (Highest *evaluation* risk.)
Your system takes emotional input from real people. Someone will eventually type something about serious distress or self-harm — during testing, or worse, during your demo. **Your evaluator will almost certainly ask about this.** Having no answer looks careless; having a good answer looks mature and professional.

**Solution — build this in Week 2, it is one small file:**
- A crisis-keyword detector that runs **before** anything else in the pipeline.
- If triggered, the system **skips the entire generation pipeline** and displays a calm, caring message with real helpline information (for India: Tele-MANAS 14416, KIRAN 1800-599-0019). It does not try to generate a narrative.
- A permanent, visible disclaimer on the app: *"This is a self-reflection tool, not therapy or medical advice."*
- A rule that the system never diagnoses, never uses clinical labels about the user, and never promises outcomes.

This is perhaps 60 lines of code and it will meaningfully improve how your project is received.

### Problem 4 — Building the FLAN-T5 training data takes far longer than you think.
Hand-writing 300–600 high-quality input/output examples is the most time-consuming task in the entire project — and it is not "coding," so teams put it off. Then Week 6 arrives and there is no data to train on.

**Solution:** Start in **Week 2**, not Week 5. Split it: each member writes 15–20 seed scenarios in their own words. Then expand each seed into 3–6 variations. Use a simple template to generate first drafts of the target narratives from your concept cards, then **hand-edit every one** for quality. Treat this as a scheduled deliverable with a deadline, not as background work.

### Problem 5 — Everyone works separately and nothing fits together.
The classic 4-person project failure: four modules that each work alone and none of which connect, discovered in Week 9.

**Solution:** In **Week 1**, build a fake end-to-end version. Every step is a stub function that returns hardcoded output. The web page sends text, receives a hardcoded narrative, a placeholder image, and a beep sound. It is useless — and it is the most valuable thing you will build, because now every member simply replaces one fake function with a real one, and the system is *never* broken. This one practice prevents more project failures than any other.

### Problem 6 — Free Colab disconnects and you lose your training.
Free Colab sessions time out, and disconnect if you are idle.

**Solution:** Save a checkpoint after every epoch directly to Google Drive. Train in short runs. Keep Kaggle (30 free GPU hours per week, more stable sessions) as your backup. Your jobs are small — DistilBERT is under an hour, FLAN-T5 LoRA is 1–3 hours — so this is manageable if you checkpoint.

### Problem 7 — "Did you actually build AI, or just call libraries?"
Expect this question. Most of your components are pretrained models you are using as-is.

**Solution — prepare this answer now:** *"We use pretrained models for the standard, solved sub-tasks — speech recognition, image generation, and voice synthesis — because reinventing those is neither realistic nor valuable. Our own machine-learning contribution is in two places: we fine-tuned DistilBERT for emotion classification on a mapped GoEmotions dataset and evaluated it with macro-F1, and we fine-tuned FLAN-T5 using LoRA on a 500-example dataset we constructed ourselves. Our system-design contribution is the context engine and the evidence-based principle selector, which is what makes the output grounded rather than generic."*

That is an honest, specific, confident answer. Do not overclaim — overclaiming is what gets torn apart in a viva.

### Problem 8 — Nobody can explain the parts they did not build.
Evaluators ask individual members about modules they did not write.

**Solution:** Hold a 30-minute "teach-back" session every week where each member explains their module to the others. By the review, every member can explain the whole system. This costs 30 minutes a week and is the difference between a good grade and a great one.

### Problem 9 — First-time installation failures burn a whole week.
Version conflicts between PyTorch, Transformers, spaCy, and the audio libraries are extremely common and extremely demoralizing.

**Solution:** In Week 1, one person gets everything installed and working, then **freezes the exact versions** (`pip freeze > requirements.txt`) and commits it. Everyone else installs from that file. Pin versions with `==`, never leave them open.

### Problem 10 — Scope creep.
User accounts, login systems, mobile apps, chat history, cloud deployment, analytics dashboards — all tempting, none required.

**Solution:** For your timeline, skip authentication entirely. Use a simple browser-stored user ID. Every hour spent on login is an hour not spent on the AI, which is what you are actually being evaluated on.

---

# PART 4 — Your Five Final Answers

## 1. Final Recommended Workflow

1. User opens the web page and either types a worry or records it by voice.
2. If it was voice, Whisper converts the recording into text. If typed, this is skipped.
3. **A safety check runs first** — if the text signals a crisis, the system stops here and shows helpline information instead of generating anything.
4. spaCy analyzes the sentence structure, and our rules detect negative thinking patterns.
5. DistilBERT (which we fine-tuned) detects the emotions present.
6. The Context Engine combines all of it into one "Case Frame" — the user's words, emotions, thinking patterns, goal, and a one-line summary.
7. The Principle Selector matches the Case Frame against our library of evidence-backed psychological concept cards and picks the most applicable techniques.
8. FLAN-T5 (which we fine-tuned with LoRA) writes a personalized four-part narrative — current reality, reframe, desired future, concrete next step — using the structure from the chosen technique.
9. The narrative text is shown to the user **immediately**, without waiting for the image or audio.
10. Kokoro converts the narrative into natural spoken audio and it begins playing.
11. Stable Diffusion (Turbo variant) generates a matching image in the background and it appears when ready; a pre-generated fallback image is used if generation fails.
12. Everything is saved into SQLite — input, analysis, chosen techniques, narrative, image path, audio path.
13. The user can revisit any past session from the "My Journey" page, and their recurring themes make future narratives more personalized.

## 2. Final Recommended Tech Stack

**Keep everything you planned** — your stack is genuinely well-chosen for your constraints. With three specific adjustments:

| Layer | Technology | Note |
|---|---|---|
| Frontend | HTML, CSS, JavaScript | As planned |
| Backend | Python + Flask | As planned |
| Speech-to-text | Whisper **base/small** via `faster-whisper` | Adjusted: small sizes + faster runtime |
| Language analysis | spaCy (`en_core_web_sm`) + your own rules | As planned |
| Emotion detection | DistilBERT, fine-tuned by you | As planned — this is real ML work |
| Context & principle selection | Plain Python + your concept-card library | The heart of the project |
| Narrative generation | FLAN-T5-base + LoRA, **hybrid with templates** | Adjusted: structure from templates, personalization from the model |
| Image generation | Stable Diffusion — **Turbo/LCM variant** | Adjusted: 10–20× faster, essential for demos |
| Voice generation | Kokoro-82M | As planned — install and verify in Week 1 |
| Database | SQLite | As planned |
| Version control | Git + GitHub | As planned |
| Containerization | Docker | **Final week only, optional** |

## 3. What We Should NOT Use

- **React, Vue, or Angular** — weeks of learning for three simple pages.
- **MySQL, PostgreSQL, or MongoDB** — installation and configuration burden for zero benefit at this scale.
- **Any paid API** (OpenAI, Gemini, Claude, ElevenLabs, Google Speech) — violates your constraints and removes your ML contribution.
- **Large models (LLaMA, Mistral, 7B+)** — will not run on student hardware.
- **Whisper medium or large** — too slow on a CPU for a live demo.
- **Standard Stable Diffusion 1.5 with 50 steps** — minutes per image; use the Turbo variant.
- **Login and authentication systems** — pure scope creep; use a browser-stored ID.
- **Cloud deployment (AWS, GCP, Azure)** — costs money and time; demo from a laptop.
- **Docker as an early task** — do it last or not at all.
- **Training any model from scratch** — always fine-tune an existing one. Training from zero needs data and compute you do not have.
- **Kubernetes, microservices, message queues, Redis, Celery** — if anyone suggests these, the answer is no.

## 4. Why This Stack Is Suitable for Us (say this to your guide)

> "We selected every component against four constraints: it must be free and open-source, it must run on ordinary student laptops without a dedicated graphics card, it must be small enough for us to genuinely understand and explain, and it must leave room for real machine-learning work of our own rather than just calling an API.
>
> Each choice reflects that. Flask over Django because we can explain every line of it. SQLite over MySQL because it needs no server setup on four different machines. DistilBERT over full BERT because it trains in under an hour on a free Colab GPU while keeping about 97% of BERT's accuracy. FLAN-T5-base over a 7-billion-parameter model because it is the largest instruction-following model we can actually fine-tune and run on our hardware. Kokoro at 82 million parameters because it gives natural-sounding speech at CPU speed, which matters for a tool meant to feel comforting.
>
> We deliberately use pretrained models for the solved problems — speech recognition, image generation, voice synthesis — and concentrate our own machine-learning effort where the project's actual contribution lies: fine-tuning an emotion classifier, fine-tuning a narrative generator on a dataset we built ourselves, and designing the context engine that grounds every output in a documented, evidence-backed psychological principle.
>
> The result is a system that runs entirely offline, costs nothing, that we can each explain end to end, and that we can realistically finish and demonstrate within our timeline."

## 5. Implementation Order (build in exactly this order)

**Never build everything at once. Each stage below produces something that runs.**

**Stage 1 — Week 1: Make it work end to end while doing nothing.**
Set up Git, one shared Python environment with frozen versions, and a Flask app with one page. Every pipeline step is a fake function returning hardcoded output. Type a sentence → get a hardcoded narrative, a placeholder image, and a beep. It is useless and it is your most important milestone: the skeleton now exists and can never break. Also this week: install and verify Kokoro and Whisper on every laptop.

**Stage 2 — Week 2: Make it real but simple, and make it safe.**
Replace the fake narrative with a template-based one — pure Python, no AI. Detect a few thinking patterns with simple keyword rules and fill in a pre-written narrative template. Build the crisis-safety check. Create your SQLite database and save every session. **You now have a genuinely working project.** Everything after this is improvement, not survival. Start writing your training scenarios this week.

**Stage 3 — Week 3: Add real understanding.**
Add spaCy and your proper rule-based pattern detection. Fine-tune DistilBERT on GoEmotions in Colab and plug in real emotion detection. Build your first 10 concept cards. Your Case Frame is now real.

**Stage 4 — Week 4: Add real intelligence.**
Complete all 15 concept cards. Build the Principle Selector so the system genuinely chooses a technique based on the Case Frame. Narratives are still template-based, but now they are *correctly chosen and grounded*. This is the point where your project stops being a toy.

**Stage 5 — Week 5: Build the training data.**
All hands. Expand seeds to 300–600 input/output pairs. Hand-edit for quality. Split into train/validation/test.

**Stage 6 — Week 6: Add real generation.**
Fine-tune FLAN-T5 with LoRA in Colab. Wire it into the hybrid setup — template structure, model personalization. Compare against your Stage-2 templates and keep whichever is better per beat. Keep the template path permanently as a fallback.

**Stage 7 — Week 7: Add the media.**
Wire in Kokoro for voice. Wire in SD-Turbo for images, running in the background, with your pre-generated fallback library ready.

**Stage 8 — Week 8: Make it look and feel finished.**
Polish the three pages. Add the progress indicator with named steps. Build the "My Journey" history page. Add simple personalization from past sessions.

**Stage 9 — Week 9: Test everything properly.**
Full end-to-end testing. Test on your weakest laptop. Fix memory and speed problems. Verify every fallback path actually works by deliberately breaking things.

**Stage 10 — Week 10: Measure it.**
Run your evaluation: emotion classifier accuracy and macro-F1, pattern-detection precision and recall on your labeled test sentences, and a human rating of 20–30 narratives scored by your team plus 10–15 other students. Real numbers in your report are worth a great deal.

**Stage 11 — Week 11: Improve and document.**
Fix what evaluation revealed. Write the report, the dataset documentation, and the README. Optionally Docker.

**Stage 12 — Week 12: Prepare the demo.**
Write a demo script with three prepared example inputs you have tested many times. **Record a backup video of a perfect run** — if anything fails live, you play the video and keep talking. Practice the teach-back so every member can answer questions about every module. Prepare answers to the questions in Part 3.

---

# PART 5 — The Five Questions You Will Be Asked (and your answers)

**"How is this different from ChatGPT?"**
> "ChatGPT generates a response from a general-purpose model with no defined method. Our system follows an explicit, traceable pipeline: it identifies the specific negative thinking pattern, selects a documented psychological technique with a real research citation attached, and generates the narrative according to that technique's structure. Every output can be traced back to a named principle and its source. It also runs entirely offline with no paid API, and delivers text, image, and voice as one experience."

**"Is manifestation scientific?"**
> "We do not claim it is. We treat manifestation as the theme, not the mechanism. Our knowledge base only contains techniques with genuine research support — cognitive reframing, self-efficacy, implementation intentions, mental contrasting, goal setting — and every concept card records how strong that evidence is, along with the technique's limitations. We explicitly exclude law-of-attraction and any claim that thoughts alter external reality."

**"What did you actually build?"**
> Use the answer prepared in Problem 7 above.

**"What if someone in real distress uses this?"**
> Use the safety system from Problem 3 — the crisis check, the helpline routing, the disclaimer, and the rule that the system never diagnoses.

**"What are the limitations?"**
> "English only. FLAN-T5-base is small, so narrative variety is limited compared to a large model. Our thinking-pattern rules are hand-written and miss unusual phrasings — we measured this and report the actual recall. Our narrative training set is a few hundred examples, which is small. We evaluated with a user panel of about a dozen people, not a clinical study. And we make no therapeutic claims."

Knowing your limitations precisely is a sign of engineering maturity. Prepare this answer as carefully as the others.
