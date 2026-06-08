# elevator 🛗

[English](README_en_US.md)

**elevator** 是一个轻量 JVM 参数更新工具，用于在 Windows 桌面应用中安全、原子地更新 JVM 启动参数。

## 设计初衷 💡

Launch4j 打包生成的 `.exe` 支持通过同目录下的 `.l4j.ini` 文件附加 JVM 启动参数。修改该文件即可调整 JVM 行为，但应用一旦被安装到 `Program Files` 下，该目录受系统保护，**必须管理员权限才能修改** `.l4j.ini`。

然而 Windows 程序启动后 **不能「原地」提升权限**。解决方法是让主程序以管理员权限启动一个子进程来完成修改——**elevator 就是那个子进程** 🎯

> 它的唯一职责：提权运行 → 执行更新 → 安全退出。

## 工作原理 ⚙️

该工具将新的 `.vmoptions` 文件内容应用到目标目录中的 INI 配置文件上。它由其他应用程序内部调用，非用户直接使用。

更新流程 🔄：
1. 读取新的 `.vmoptions` 文件内容（支持 UTF-8 BOM）📖
2. 将目标 INI 文件复制到 `back/` 目录作为备份 📦
3. 将新内容写入目标 INI 文件 ✍️
4. 若写入失败，自动从备份恢复，确保数据安全 🔙🛡️

## 安装 📥

**无需自行构建。** 直接从 [Releases](https://github.com/bytecascade-Lee/elevator/releases) 下载最新发布包。

### 文件布局

将下载的发布包解压到主应用的安装目录下，目录结构如下：

```
<主应用安装目录>/
├── bin/
│   ├── <主应用>.exe          # 主程序（由你提供）
│   ├── <主应用>.l4j.ini       # 主应用的 JVM 配置
│   └── elevator.exe           # 本工具（附带）
│   └── elevator.l4j.ini       # 本工具的 JVM 配置（附带）
├── lib/
│   ├── <主应用>.jar
│   └── elevator.jar           # 本工具的 JAR
```

### 关键配置 ⚠️

`elevator.l4j.ini` 中有两个关键系统属性，**必须**修改为你的主应用名：

```ini
-Dvmoptions.gui=<主应用名>
-Dvmoptions.console=<主应用名>-console
```

这些属性决定了 elevator 会去更新目标目录下的哪个 `.l4j.ini` 文件。例如你的主程序是 `MyApp.exe`，则：

```ini
-Dvmoptions.gui=MyApp
-Dvmoptions.console=MyApp-console
```

这样 elevator 在收到新的 `.vmoptions` 内容后，会更新 `bin/` 目录下的 `MyApp.l4j.ini` 和 `MyApp-console.l4j.ini` 文件。

## 用法 🚀

在主应用中，以管理员权限启动 `elevator.exe` 并传入两个参数：

```bash
elevator.exe <newVmoptionsFilePath> <targetFolderPath>
```

| 参数                     | 说明                               |
|------------------------|----------------------------------|
| `newVmoptionsFilePath` | `new.vmoptions` 文件的完整路径          |
| `targetFolderPath`     | 目标文件夹路径（包含 INI 文件的目录，通常是 `bin/`） |

### 示例

假如主应用 `MyApp.exe` 安装于 `C:\Program Files\MyApp`，则主应用需这样调用：

```bash
elevator.exe "C:\Users\user\AppData\Local\Temp\new.vmoptions" "C:\Program Files\MyApp\bin"
```

### 退出码

| 退出码 | 含义                            |
|-----|-------------------------------|
| 0 ✅ | 更新成功                          |
| 1 ❌ | 参数不足                          |
| 2 ❌ | 文件或目录不存在/不可读                  |
| 3 ❌ | 更新失败（备份文件位于 `back/` 文件夹，自动恢复） |

## 项目结构 📁

```
src/main/java/com/serene/elevator/
├── Main.java              # 入口：参数校验与分发
└── JvmParamUpdater.java   # 核心：读取、备份、写入、自动恢复

build/scripts/             # 打包发布脚本
.github/workflows/         # CI/CD：tag 推送自动发布
```

## 技术栈 🛠️

- **Java 21** — 零外部依赖
- **Maven** — 构建
- **Launch4j** — JAR → EXE 包装
- **Python 3.13+ / uv** — 打包脚本

## 许可 📄

[MIT](LICENSE) © 2026 Serene Lee
