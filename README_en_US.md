# elevator 🛗

[中文](README.md)

**elevator** is a lightweight JVM parameter updater for Windows desktop applications. It safely and atomically updates JVM startup parameters (`.l4j.ini` files).

## Design Rationale 💡

Launch4j-packaged `.exe` files support a co-located `.l4j.ini` file to supply additional JVM arguments at startup. Modifying this file lets you tune JVM behavior — but once the app is installed to `Program Files`, the directory is system-protected and **admin privileges are required** to edit `.l4j.ini`.

The catch: a Windows process **cannot elevate itself "in-place"** after launch. The solution is for the main app to spawn a child process running with admin privileges to do the update — **elevator is that child process** 🎯

> Its sole job: run elevated → perform the update → exit cleanly. No daemon, no residency, no lingering.

## How It Works ⚙️

The tool applies the contents of a new `.vmoptions` file to INI configuration files in a target directory. It is called internally by other applications, not intended for direct end-user use.

Update flow 🔄:
1. Read the new `.vmoptions` file content (UTF-8 BOM aware) 📖
2. Copy the target INI file to `back/` as a backup 📦
3. Write the new content to the target INI file ✍️
4. Automatically restore from backup on write failure, ensuring data safety 🔙🛡️

## Installation 📥

**No need to build from source.** Download the latest release from the [Releases](https://github.com/bytecascade-Lee/elevator/releases) page.

### File Layout

Extract the downloaded package into your main application's installation directory:

```
<App Install Dir>/
├── bin/
│   ├── <YourApp>.exe          # Your main application
│   ├── <YourApp>.l4j.ini       # Your app's JVM config
│   └── elevator.exe            # This tool
│   └── elevator.l4j.ini        # This tool's JVM config
├── lib/
│   ├── <YourApp>.jar
│   └── elevator.jar            # This tool's JAR
```

### Critical Configuration ⚠️

In `elevator.l4j.ini`, two system properties **must** be set to match your main application's name:

```ini
-Dvmoptions.gui=<YourAppName>
-Dvmoptions.console=<YourAppName>-console
```

These tell elevator which `.l4j.ini` files to update in the target directory. For example, if your main executable is `MyApp.exe`:

```ini
-Dvmoptions.gui=MyApp
-Dvmoptions.console=MyApp-console
```

With this configuration, when elevator receives new `.vmoptions` content, it will update `MyApp.l4j.ini` and `MyApp-console.l4j.ini` in the `bin/` directory.

## Usage 🚀

Your main application should launch `elevator.exe` with administrator privileges, passing two arguments:

```bash
elevator.exe <newVmoptionsFilePath> <targetFolderPath>
```

| Parameter              | Description                                                        |
|------------------------|--------------------------------------------------------------------|
| `newVmoptionsFilePath` | Full path to the `new.vmoptions` file                              |
| `targetFolderPath`     | Path to the target folder (containing INI files, typically `bin/`) |

### Example

If your main app `MyApp.exe` is installed at `C:\Program Files\MyApp`, your app would call:

```bash
elevator.exe "C:\Users\user\AppData\Local\Temp\new.vmoptions" "C:\Program Files\MyApp\bin"
```

### Exit Codes

| Code | Meaning                                                               |
|------|-----------------------------------------------------------------------|
| 0 ✅  | Update successful                                                     |
| 1 ❌  | Insufficient parameters                                               |
| 2 ❌  | File or directory not found / not readable                            |
| 3 ❌  | Update failed (backup files are in `back/`, can be restored manually) |

## Project Structure 📁

```
src/main/java/com/serene/elevator/
├── Main.java              # Entry point, argument validation and dispatch
└── JvmParamUpdater.java   # Core logic: read, backup, write, auto-restore

build/scripts/             # Release packaging scripts
.github/workflows/         # CI/CD: automatic release on tag push
```

## Tech Stack 🛠️

- **Java 21** — zero external dependencies
- **Maven** — build
- **Launch4j** — JAR to EXE wrapper
- **Python 3.13+ / uv** — packaging scripts

## License 📄

[MIT](LICENSE) © 2026 Serene Lee
