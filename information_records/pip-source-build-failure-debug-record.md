# Debug Record — `pip install -r requirements.txt` fails on `numpy==2.2.4` (`metadata-generation-failed`)

*Date: 2026-08-12*
*Recorded by: AI assistant during a live debugging session with the user*
*Project: BiliNote-analysis (backend, FastAPI)*

---

## 1. Symptom (what we saw)

Running `pip install -r requirements.txt` produced a long error ending in:

```
Collecting numpy==2.2.4 (from -r requirements.txt (line 66))
  Using cached https://pypi.tuna.tsinghua.edu.cn/.../numpy-2.2.4.tar.gz  (20.3 MB)
  ...
  Preparing metadata (pyproject.toml) ... error
  error: subprocess-exited-with-error

  × Preparing metadata (pyproject.toml) did not run successfully.
  │ exit code: 2
  ╰─> [540 lines of output]
      + D:\development-package\python\Python314\python.exe C:\Users\22509\AppData\Local\Temp\pip-install-...\numpy...\vendored-meson\meson\meson.py setup ...
error: metadata-generation-failed
```

Every other package in the same log installed fine (as `.whl` files). Only numpy failed.

---

## 2. The debugging mindset (read errors like a detective)

- **Error messages are layered.** The visible message is only the outermost layer; the real clue is buried in the middle. Read *both* the top (what pip fetched) and the bottom (what actually failed).
- **Distinguish "install a binary" from "build from source".** This single distinction explains 90% of pip failures on Windows.
  - `.whl` (wheel) = **prebuilt binary**, just unpacked and installed. Almost always succeeds.
  - `.tar.gz` / `.zip` of source = must be **compiled on your machine** (needs a C/C++ toolchain). Frequently fails.
- **Never change anything until you can name the root cause.** We did zero modifications during the trace below.

---

## 3. Step-by-step trace (what we actually did)

### Step 1 — Read the TOP of the log: notice the artifact type

Key line from the log:

```
Using cached .../numpy-2.2.4.tar.gz  (20.3 MB)
```

Compare with the lines around it:

```
Using cached .../multidict-6.4.3-py3-none-any.whl  (10 kB)
Using cached .../networkx-3.3-py3-none-any.whl  (1.7 MB)
```

- Almost every package was fetched as **`.whl`** — a prebuilt wheel.
- numpy was fetched as **`.tar.gz`** — **source code**.
- pip only falls back to the source tarball when it cannot find any compatible wheel for *this* interpreter/platform.

**First hypothesis**: "numpy has no prebuilt wheel for the interpreter that ran pip."

### Step 2 — Read the BOTTOM of the log: the actual failing action

The error is not a Python import error and not a version conflict — pip **started building numpy from source** and the build failed:

```
vendored-meson\meson\meson.py setup ...
```

- Modern numpy builds with **meson** (its new build backend).
- Building from source requires a full native toolchain (MSVC/CMake). It is usually absent on a typical Windows machine, so the build dies early — here during `Preparing metadata` (the first phase where the build system runs).

**Conclusion so far**: pip tried to *compile* numpy, and compilation failed. The remaining question: *why did pip have to compile at all?*

### Step 3 — Ask "why was there no wheel?" → identify the interpreter

Wheels are tagged for a specific combination of platform + Python version, e.g.:

- `numpy-2.2.4-cp311-cp311-win_amd64.whl` → Windows, 64-bit, **Python 3.11**
- `numpy-2.2.4-cp313-cp313-win_amd64.whl` → **Python 3.13**
- There is **no** `cp314` file for numpy 2.2.4.

Two commands answer "which interpreter did pip use / which do we have":

```powershell
# which interpreter was running (visible directly in the error log):
#   D:\development-package\python\Python314\python.exe   ← Python 3.14

# which Pythons exist on this machine:
py -0p
```

Result:

```
 -3.13-64       D:\development-package\python\Python313\python.exe
 -3.12-64       D:\development-package\python\Python312\python.exe
```

Plus the default `python` on PATH → **Python 3.14** (`D:\development-package\python\Python314\python.exe`).

**Refined hypothesis**: numpy 2.2.4 has wheels for cp311–cp313 but *not* for **cp314**, so under Python 3.14 pip is forced to build from source.

### Step 4 — Prove the tag mismatch with `pip debug --verbose`

pip can print the exact set of wheel tags your interpreter accepts:

```powershell
# Python 3.13 (the project's venv):
backend\.venv\Scripts\python.exe -m pip debug --verbose

# Python 3.14 (system default):
& "D:\development-package\python\Python314\python.exe" -m pip debug --verbose
```

Observed output (filtered to the interesting tags):

| Interpreter | Compatible tags (excerpt) |
|---|---|
| Python 3.13 venv | `cp313-cp313-win_amd64`, `cp313-abi3-win_amd64`, `cp313-none-win_amd64`, `py3-none-win_amd64` |
| Python 3.14 | `cp314-cp314-win_amd64`, `cp314-abi3-win_amd64`, `cp314-none-win_amd64`, `cp313-abi3-win_amd64`, `py3-none-win_amd64` |

**This is the smoking gun.** Python 3.14 accepts a wheel only if its tag contains `cp314` (or a universal `abi3`/`py3` tag). numpy 2.2.4 does **not** ship `cp314` wheels, so it is simply invisible to pip on 3.14 → source build.

### Step 5 — Verify against PyPI (cross-check the hypothesis)

- Open `https://pypi.org/project/numpy/2.2.4/#files` and look at the wheel filenames: the newest `cp` tag is `cp313`. No `cp314`.
- Reason about **dates**: numpy 2.2.4 was released **2025-03-17** (per PyPI); Python 3.14 was released **2025-10**. A package published *before* a Python release obviously cannot contain wheels for it.
- Rule of thumb: numpy supports a new CPython minor only from ~`2.3.x` onward (cp314 wheels start at numpy 2.3.2+).

Hypothesis confirmed: **numpy 2.2.4 ↔ Python 3.14 is an unsupported pairing.**

### Step 6 — Check what the project *expects* (don't fix in a vacuum)

The project documents its supported Python range:

- `CLAUDE.md`: *"Backend (Python 3.11 + FastAPI)"*
- `backend/Dockerfile`: `FROM .../python:3.11-slim`

`requirements.txt` is a **frozen snapshot** (every pin `==`) built for that era of Python. So the intended range is 3.11–3.13; 3.14 was never in scope. This also explains why **no other package** in the file had a problem on 3.13 but the whole file is fragile on 3.14 (av, tokenizers, onnxruntime, … are pinned to pre-3.14 releases too).

### Step 7 — Find the environment that already works (verify before acting)

The project already has a virtualenv:

```powershell
backend\.venv\Scripts\python.exe --version            # Python 3.13.3
backend\.venv\Scripts\python.exe -m pip list          # numpy==2.2.4 already present
backend\.venv\Scripts\python.exe -c "import numpy; print(numpy.__version__)"   # 2.2.4 ✓
backend\.venv\Scripts\python.exe -m pip check         # No broken requirements found.
```

Everything is already installed and healthy in the 3.13 venv.

---

## 4. Root cause (one paragraph)

The failed `pip install` was executed with **system Python 3.14** (`D:\development-package\python\Python314\python.exe`). `numpy==2.2.4` was released before Python 3.14 and ships **no `cp314` wheels**, so pip had to fall back to the source tarball and **compile numpy with meson**; without a native build toolchain that compilation fails during metadata preparation (`error: metadata-generation-failed`). This is **not** a numpy bug and not a `requirements.txt` bug — it is an **interpreter mismatch**: the install command used the wrong Python. The project's own venv (`backend\.venv`, Python 3.13.3) already contains a correct, working installation.

---

## 5. The fix

```powershell
cd backend
.\.venv\Scripts\python.exe main.py            # run with the venv interpreter
# or activate it first:
.\.venv\Scripts\Activate.ps1
python main.py
```

- Use the existing venv for both **running** and **installing**; never install with a bare `python` when the default on PATH is 3.14.
- If Python 3.14 must be used, `requirements.txt` would need pin upgrades (at least `numpy>=2.3.2`), and several other pins (av, tokenizers, onnxruntime, ctranslate2, …) would likely also need version bumps — a much larger, riskier change. **Not recommended.**

---

## 6. Prevention — general rules you can reuse anywhere

1. **`.whl` vs `.tar.gz` is the fastest diagnostic.** If pip downloads a tarball for a compiled package, it means "no prebuilt binary for your environment" — expect trouble.
2. **Whenever pip starts compiling, immediately check the interpreter:** `python --version` and `py -0p` to see what exists.
3. **`python -m pip debug --verbose` shows the wheel tags your interpreter can install.** Compare them with the package's `Download files` page on PyPI.
4. **A package released before a given Python version can never have wheels for it.** Check release dates when a pairing looks suspicious.
5. **Respect the project's declared Python range** (`CLAUDE.md`, `Dockerfile`, `.python-version`, `pyproject.toml` requires-python, docs). A frozen `requirements.txt` implies a specific Python era.
6. **Always work inside the project's venv** (`venv\Scripts\python.exe -m pip ...`, or activate it first). Fresh system interpreters are a different environment and silently pull different wheels.

---

## 7. Command cheat-sheet

| Goal | Command |
|---|---|
| List installed Pythons | `py -0p` |
| Current interpreter version | `python --version` |
| Wheel tags this interpreter accepts | `python -m pip debug --verbose` |
| List files (wheels) a PyPI version ships | `https://pypi.org/project/<pkg>/<version>/#files` |
| Check the venv health | `python -m pip check` |
| Import sanity check | `python -c "import numpy; print(numpy.__version__)"` |
| Run the backend with the venv | `backend\.venv\Scripts\python.exe main.py` |
