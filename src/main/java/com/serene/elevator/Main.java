package com.serene.elevator;


import java.io.File;

/**
 * Description: JVM参数更新工具入口类
 * <p>
 * 用法: java -jar updater.jar <newVmoptionsFilePath> <targetFolderPath>
 * <ul>参数1: new.vmoptions文件的完整路径</ul>
 * <ul>参数2: 目标文件夹路径(包含starter.l4j.ini和starter-console.l4j.ini的目录)</ul>
 * </p>
 *
 * @author Serene Lee
 * @date 2026/5/24
 */
public class Main {

    public static void main(String[] args) {
        // 检查参数
        if (args.length < 2) {
            System.err.println("错误：参数不足");
            System.err.println("用法: java -jar updater.jar <newVmoptionsFilePath> <targetFolderPath>");
            System.err.println("示例: java -jar updater.jar D:\\temp\\new.vmoptions D:\\myapp\\config");
            System.exit(1);
        }

        String newVmoptionsPath = args[0];
        String targetFolderPath = args[1];

        // 验证文件是否存在
        File newVmoptionsFile = new File(newVmoptionsPath);
        if (!newVmoptionsFile.exists() || !newVmoptionsFile.isFile()) {
            System.err.println("错误：new.vmoptions文件不存在或不是文件: " + newVmoptionsPath);
            System.exit(1);
        }

        // 验证目标文件夹是否存在
        File targetFolder = new File(targetFolderPath);
        if (!targetFolder.exists() || !targetFolder.isDirectory()) {
            System.err.println("错误：目标文件夹不存在或不是目录: " + targetFolderPath);
            System.exit(1);
        }

        // 创建更新器并执行
        JvmParamUpdater updater = new JvmParamUpdater();
        boolean success = updater.updateJvmParameters(newVmoptionsPath, targetFolderPath);

        if (success) {
            System.out.println("JVM参数更新成功");
            System.exit(0);
        } else {
            System.err.println("JVM参数更新失败");
            System.exit(1);
        }
    }
}
