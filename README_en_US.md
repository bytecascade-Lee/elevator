# elevator

[中文](README.md)

**elevator** 🛗 is a JVM parameter updater tool that safely and atomically updates JVM startup parameters for Windows desktop applications.

## Design Rationale 💡

Launch4j-packaged `.exe` files support a co-located `.l4j.ini` file to supply additional JVM arguments at startup. Modifying this file lets you tune JVM behavior — but once the app is installed to `Program Files` (via Inno Setup or similar), the directory is system-protected and **admin privileges are required** to edit `.l4j.ini`.

The catch: a Windows process **cannot elevate itself "in-place"** after launch. The solution is for the main app to spawn a child process running with its own admin privileges to do the update — **elevator is that child process**.

> 🎯 Its sole job: run elevated → perform the update → exit cleanly. No daemon, no residency, no lingering.

## How It Works ⚙️

The tool applies the contents of a new `.vmoptions` file to INI configuration files in a target directory. It is called internally by other applications, not intended for direct end-user use.

Update flow 🔄:
1. Read the new `.vmoptions` file content (UTF-8 BOM aware) 📖
2. Copy the target INI file to `back/` as a backup 📦
3. Write the new content to the target INI file ✍️
4. Automatically restore from backup on write failure, ensuring data safety 🔙🛡️

## Usage

```bash
java -jar elevator.jar <newVmoptionsFilePath> <targetFolderPath>
```

| Parameter | Description |
|-----------|-------------|
| `newVmoptionsFilePath` | Full path to the `new.vmoptions` file |
| `targetFolderPath` | Path to the target folder (containing INI files) |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Update successful |
| 1 | Insufficient parameters |
| 2 | File or directory not found / not readable |
| 3 | Update failed (backup files are in the `back/` folder) |

## Build

### Prerequisites

- JDK 21
- Maven
- Python 3.13+ (build scripts)
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Launch4j](https://launch4j.sourceforge.net/) (EXE wrapper generator)
- [Inno Setup](https://jrsoftware.org/isinfo.php) (optional, for installer builds)

### Build Steps

```bash
# 1. Compile JAR
mvn clean package

# 2. Sync Python environment
uv sync

# 3. Package
uv run build/scripts/release.py -p   # Portable ZIP
uv run build/scripts/release.py -i   # Installer
uv run build/scripts/release.py -b   # Both

# Interactive mode
uv run build/scripts/release.py
```

## Project Structure

```
src/main/java/com/serene/elevator/
├── Main.java              # Entry point, argument validation and dispatch
└── JvmParamUpdater.java   # Core logic: read, backup, write, auto-restore

build/
├── scripts/               # Python packaging scripts (managed by uv)
├── launch4j/              # Launch4j config template
└── templates/             # Maven-filterable templates

.github/workflows/
└── release.yml            # CI/CD: automatic release on tag push
```

## Tech Stack

- Java 21 (zero external dependencies)
- Maven (build, template filtering, git info injection)
- Python 3.13+ / uv (packaging scripts)
- Launch4j (JAR to EXE wrapper)
- Inno Setup (Windows installer)

## License

[MIT](LICENSE) © 2026 Serene Lee
