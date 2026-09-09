# Getting Reframe Running On Your Own Laptop

A step-by-step guide for setting this up from scratch. No experience
needed — just follow each step in order, in a PowerShell window.

## Before you start

- **Windows 10 or 11**
- **At least 8GB RAM** (16GB is safer — the picture-generating feature
  needs free memory, and can crash on very low-RAM machines. It still
  works fine without pictures if that happens.)
- **About 6GB free disk space** (for the AI models, downloaded once)
- **Internet connection** — only needed for setup and the very first use
  of each feature; not needed after that
- **A free Hugging Face account** — needed once, for the picture-generating
  AI (sign up at huggingface.co, it's free)

Open **PowerShell**: click Start, type `PowerShell`, press Enter. Every
command below goes in that window, one at a time, pressing Enter after
each.

## Step 1 — Install Git (lets you download the project)

Download it from https://git-scm.com/downloads, run the installer,
click "Next" through everything with the defaults.

## Step 2 — Install Python 3.11

```powershell
winget install --id Python.Python.3.11 -e
```

Close PowerShell and open a new one after this finishes (so it picks up
the update).

## Step 3 — Install ffmpeg (needed for voice input)

```powershell
winget install --id Gyan.FFmpeg -e --source winget
```

Close and reopen PowerShell again after this one too.

## Step 4 — Download the project

Pick a folder to put it in (example uses `D:\`), then:

```powershell
cd D:\
git clone https://github.com/Monicasdesign01/reframe-Mindvision.git
cd reframe-Mindvision
```

## Step 5 — Create the app's own Python environment

This keeps its packages separate from anything else on your computer.

```powershell
py -3.11 -m venv venv
```

## Step 6 — Install everything the app needs

This takes a few minutes — that's normal, it's downloading a lot.

```powershell
venv\Scripts\python.exe -m pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m spacy download en_core_web_sm
```

## Step 7 — Log into Hugging Face (one-time)

This is needed because the picture-generating AI requires you to accept
its license first.

1. Make a free account at https://huggingface.co
2. Go to https://huggingface.co/stabilityai/sd-turbo and click **"Agree"**
3. Go to https://huggingface.co/settings/tokens → **"New token"** →
   copy the token it gives you
4. Run this, then paste your token when it asks:

```powershell
venv\Scripts\huggingface-cli.exe login
```

## Step 8 — Run the app

```powershell
venv\Scripts\python.exe -m app.main
```

Wait until you see this line — it can take 20-30 seconds:

```
Running on http://127.0.0.1:5000
```

## Step 9 — Use it

Open your browser and go to:

```
http://127.0.0.1:5000
```

Type a worry and submit it. The written response appears in 30-60
seconds (that's a real AI thinking, not a bug) — the picture takes a
little longer and loads in after.

## To stop the app

Click back into the PowerShell window and press `Ctrl+C`.

## To run it again later

You only do Steps 1-7 once. Every other time, just:

```powershell
cd D:\reframe-Mindvision
venv\Scripts\python.exe -m app.main
```

then open `http://127.0.0.1:5000` again.

## If something goes wrong

- **"running scripts is disabled"** — ignore it, you don't need
  `venv\Scripts\activate` at all; every command above already calls
  `venv\Scripts\python.exe` directly.
- **Picture generation crashes** — close other programs (especially your
  browser and any IDE) to free up RAM, then try submitting again.
- **Anything else** — copy the exact error text and ask whoever set this
  up originally.
