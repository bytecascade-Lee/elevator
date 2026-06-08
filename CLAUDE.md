# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Build the JAR
mvn clean package

# Sync Python environment (for packaging scripts)
uv sync

# Package as portable ZIP (-p), installer (-i), or both (-b)
uv run build/scripts/release.py -p
uv run build/scripts/release.py -i
uv run build/scripts/release.py -b --include-jre

# Interactive build (prompts for mode)
uv run build/scripts/release.py

# Generate SHA256 hash of Maven dependencies (for CI caching)
uv run build/scripts/sha_jar_deps.py

# Move Maven staging files to expected locations
uv run build/scripts/move_staging_files.py
```

IntelliJ run configurations are available under `.idea/runConfigurations/`.

**CI:** GitHub Actions on `v*` tag push builds the JAR (Ubuntu), packages Windows artifacts with Launch4j, then creates a
GitHub Release.

## What This Project Does

**elevator** is a JVM parameter update utility for Windows desktop applications. It reads a `.vmoptions` file and atomically
updates target `.l4j.ini` config files (GUI + console) with backup-and-restore safety. It is called by other applications
internally — not a user-facing tool.

## Architecture

### Java App (`src/main/java/com/serene/elevator/`)

Two classes, zero external dependencies:

- **`Main.java`** — CLI entry point. Validates args (new vmoptions path + target folder path), delegates to
  `JvmParamUpdater`, exits with status codes (0=success, 1=param error, 2=file invalid, 3=update failed).
- **`JvmParamUpdater.java`** — Core logic. Reads new vmoptions content via `BufferedReader` (with UTF-8 BOM stripping),
  copies each target INI file to `back/` folder, writes new content, auto-restores from backup on write failure. Target
  filenames are configured via system properties `vmoptions.gui` and `vmoptions.console`.

### Build Pipeline (two-stage: Maven → Python)

**Stage 1 — Maven** (`pom.xml`):

- Compiles Java 21 source
- Copies+filtertemplates from `build/templates/` (Python scripts, Launch4j XML, Inno Setup .iss) into `staging/`
- Copies JAR dependencies to `dists/lib/`
- Injects git commit info via `git-commit-id-plugin`
- Outputs: JAR in `staging/`, filtered scripts/templates in `staging/`

**Stage 2 — Python packaging** (`build/scripts/`, managed by `uv`):

- `release.py` — Entry point. Interactive or CLI-driven (`-p`/`-i`/`-b`). Orchestrates all phases:
    1. `prepare_for_building.py` — Generates `gui.exe` + `console.exe` via Launch4j from `launch4j.xml` template; initializes
       `dist/bin`, `dist/lib`, `dist/help`, `dist/license`; optionally copies bundled JRE
    2. `prepare_bin_for_mode()` — Generates `.l4j.ini` files from `.vmoptions` template (replacing `{{MODE}}` placeholder);
       copies and renames EXEs to `dist/bin/`
    3. `build_portable.py` / `build_install.py` — Package as ZIP or Inno Setup installer
    4. `cleanup_temp()` — Cleans `temp/` directory
- `move_staging_files.py` — Copies Maven staging outputs (JAR, filtered templates) to expected locations in `build/` and
  `dist/` (used in CI after downloading JAR artifact)
- `sha_jar_deps.py` — Runs `mvn dependency:list`, parses/deduplicates dependencies, computes SHA256 for Maven cache key in CI

### CI/CD (`.github/workflows/release.yml`)

Three-job pipeline triggered by `v*` tags:

1. **build-jar** (Ubuntu) — Compiles JAR, uploads staging as artifact
2. **build-windows** (Windows, needs build-jar) — Downloads JAR artifact, runs `move_staging_files.py`, generates Launch4j
   EXEs, builds portable package (`-p --include-jre`)
3. **create-release** (Ubuntu, needs build-windows) — Creates a GitHub Release with the packaged artifacts

### Key Config Files

- `.vmoptions` — Template for `.l4j.ini` files; defines `vmoptions.gui`, `vmoptions.console` system properties and `app.env`
  placeholder. Updated by this tool.
- `build/launch4j/launch4j.xml` — Launch4j config template with `{{HEAD-TYPE}}` and `{{APPLICATION-NAME}}` placeholders.
  Wraps JAR into EXE with JRE 21 requirement, mutex-based single-instance, Chinese error messages.

### Output Layout

```
dist/
  bin/        — EXE + .l4j.ini pairs (per mode: install/portable)
  lib/        — Application JAR + dependencies
  jre/        — Bundled JRE (optional)
staging/      — Maven build output (JAR, filtered templates)
release/      — Final packages (.zip, .exe installer)
temp/         — Intermediate EXEs from Launch4j
```
