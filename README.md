# elevator

[English](README_en_US.md)

**elevator** 🛗 是一个 JVM 参数更新工具（JVM parameter updater），用于在 Windows 桌面应用程序中安全、原子地更新 JVM 启动参数。

## 设计初衷 💡

Launch4j 打包生成的 `.exe` 支持通过同目录下的 `.l4j.ini` 文件附加 JVM 启动参数。修改该文件即可调整 JVM 行为，但应用一旦被 Inno Setup 等安装工具安装到 `Program Files` 下，该目录受系统保护，**必须管理员权限才能修改** `.l4j.ini`。

然而 Windows 程序启动后 **不能「原地」提升权限**。解决方法是让主程序以其自身的管理员权限启动一个子进程来完成修改——**elevator 就是那个子进程**。

> 🎯 它的唯一职责：提权运行 → 执行更新 → 安全退出。不驻留、不常驻、用完即走。

## 工作原理 ⚙️

该工具将新的 `.vmoptions` 文件内容应用到目标目录中的 INI 配置文件上。它由其他应用程序内部调用，非用户直接使用。

更新流程 🔄：
1. 读取新的 `.vmoptions` 文件内容（支持 UTF-8 BOM）📖
2. 将目标 INI 文件复制到 `back/` 目录作为备份 📦
3. 将新内容写入目标 INI 文件 ✍️
4. 若写入失败，自动从备份恢复，确保数据安全 🔙🛡️

## 用法

```bash
java -jar elevator.jar <newVmoptionsFilePath> <targetFolderPath>
```

| 参数 | 说明 |
|------|------|
| `newVmoptionsFilePath` | `new.vmoptions` 文件的完整路径 |
| `targetFolderPath` | 目标文件夹路径（包含 INI 文件的目录） |

### 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 更新成功 |
| 1 | 参数不足 |
| 2 | 文件或目录不存在/不可读 |
| 3 | 更新失败（备份文件位于 `back/` 文件夹） |

## 构建

### 前提条件

- JDK 21
- Maven
- Python 3.13+（构建脚本）
- [uv](https://docs.astral.sh/uv/)（Python 包管理器）
- [Launch4j](https://launch4j.sourceforge.net/)（EXE 启动器生成）
- [Inno Setup](https://jrsoftware.org/isinfo.php)（可选，安装包构建）

### 构建步骤

```bash
# 1. 编译 JAR
mvn clean package

# 2. 同步 Python 环境
uv sync

# 3. 打包
uv run build/scripts/release.py -p   # 便携版 ZIP
uv run build/scripts/release.py -i   # 安装包
uv run build/scripts/release.py -b   # 两者都生成

# 交互式选择
uv run build/scripts/release.py
```

## 项目结构

```
src/main/java/com/serene/elevator/
├── Main.java              # 入口，参数校验与分发
└── JvmParamUpdater.java   # 核心：读取、备份、写入、自动恢复

build/
├── scripts/               # Python 打包脚本（uv 管理）
├── launch4j/              # Launch4j 配置文件模板
└── templates/             # Maven 过滤模板

.github/workflows/
└── release.yml            # CI/CD：标签推送触发自动发布
```

## 技术栈

- Java 21（零外部依赖）
- Maven（构建 + 模板过滤 + Git 信息注入）
- Python 3.13+ / uv（打包脚本）
- Launch4j（JAR → EXE 包装）
- Inno Setup（Windows 安装包构建）

## 许可

[MIT](LICENSE) © 2026 Serene Lee
