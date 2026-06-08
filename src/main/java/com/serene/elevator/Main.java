package com.serene.elevator;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Description: JVM参数更新工具入口类
 * <p>
 * 用法: java -jar elevator.jar &lt;newVmoptionsFilePath&gt; &lt;targetFolderPath&gt;
 * <ul>
 *     <li>参数1: new.vmoptions文件的完整路径</li>
 *     <li>参数2: 目标文件夹路径（包含INI文件的目录）</li>
 * </ul>
 * 此工具被其他应用程序内部调用，非用户直接使用。
 * </p>
 *
 * @author Serene Lee
 * @date 2026/5/24
 */
public class Main {

    /** 成功退出码 */
    static final int EXIT_SUCCESS = 0;
    /** 参数不足退出码 */
    static final int EXIT_PARAM_ERROR = 1;
    /** 文件或目录不存在/不可读退出码 */
    static final int EXIT_FILE_INVALID = 2;
    /** 更新失败退出码 */
    static final int EXIT_UPDATE_FAILED = 3;

    public static void main(String[] args) {
        // 检查参数数量
        if (args.length < 2) {
            System.err.println("错误：参数不足");
            System.err.println("用法: java -jar elevator.jar <newVmoptionsFilePath> <targetFolderPath>");
            System.err.println("示例: java -jar elevator.jar D:\\temp\\new.vmoptions D:\\myapp\\config");
            System.exit(EXIT_PARAM_ERROR);
        }

        String newVmoptionsPath = args[0];
        String targetFolderPath = args[1];

        // 验证源文件存在且可读
        Path sourceFile = Paths.get(newVmoptionsPath);
        if (Files.notExists(sourceFile) || !Files.isRegularFile(sourceFile) || !Files.isReadable(sourceFile)) {
            System.err.println("错误：new.vmoptions文件不存在或不可读: " + newVmoptionsPath);
            System.exit(EXIT_FILE_INVALID);
        }

        // 验证目标文件夹存在且可写
        Path targetDir = Paths.get(targetFolderPath);
        if (Files.notExists(targetDir) || !Files.isDirectory(targetDir) || !Files.isWritable(targetDir)) {
            System.err.println("错误：目标文件夹不存在或不可写: " + targetFolderPath);
            System.exit(EXIT_FILE_INVALID);
        }

        // 创建更新器并执行
        JvmParamUpdater updater = new JvmParamUpdater();
        boolean success = updater.updateJvmParameters(newVmoptionsPath, targetFolderPath);

        if (success) {
            System.out.println("JVM参数更新成功");
            System.exit(EXIT_SUCCESS);
        } else {
            System.err.println("JVM参数更新失败，备份文件位于目标目录下的 back/ 文件夹中，请手动检查");
            System.exit(EXIT_UPDATE_FAILED);
        }
    }
}
