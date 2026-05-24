package com.serene.elevator;


import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.Instant;


/**
 * Description:JVM参数更新器
 * <p>
 * 负责将新的JVM参数应用到目标INI文件中，并备份旧文件
 *
 * @author Serene Lee
 * @date 2026/5/24
 */
public class JvmParamUpdater {
    /**
     * 定义需要处理的文件名
     */
    private static final String GUI = System.getProperty("vmoptions.gui");
    private static final String CONSOLE = System.getProperty("vmoptions.console");

    private static final String[] TARGET_FILES = {GUI, CONSOLE};

    /**
     * 备份文件夹名称
     */
    private static final String BACKUP_FOLDER_NAME = "back";

    /**
     * 更新JVM参数
     *
     * @param newVmoptionsPath new.vmoptions文件的完整路径
     * @param targetFolderPath 目标文件夹路径（包含INI文件的目录）
     *
     * @return 是否更新成功
     */
    public boolean updateJvmParameters(String newVmoptionsPath, String targetFolderPath) {
        try {
            // 1. 读取新参数内容
            String newContent = readNewVmoptionsContent(newVmoptionsPath);
            if (newContent == null || newContent.trim().isEmpty()) {
                System.err.println("错误：new.vmoptions文件内容为空");
                return false;
            }

            // 2. 准备备份目录
            Path backupDir = prepareBackupDirectory(targetFolderPath);

            // 3. 处理每个目标文件
            boolean allSuccess = true;
            for (String fileName : TARGET_FILES) {
                boolean success = processSingleFile(
                        targetFolderPath,
                        fileName,
                        backupDir,
                        newContent
                );
                if (!success) {
                    allSuccess = false;
                    System.err.println("警告：处理文件 " + fileName + " 时失败");
                }
            }

            return allSuccess;

        } catch (Exception e) {
            System.err.println("更新过程中发生异常: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }

    /**
     * 读取new.vmoptions文件内容
     */
    private String readNewVmoptionsContent(String filePath) {
        StringBuilder content = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(new FileInputStream(filePath), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                // 去除BOM标记(如果存在)
                if (content.isEmpty() && !line.isEmpty() && line.charAt(0) == '\uFEFF') {
                    line = line.substring(1);
                }
                content.append(line).append(System.lineSeparator());
            }
            return content.toString();
        } catch (IOException e) {
            System.err.println("读取new.vmoptions文件失败: " + e.getMessage());
            return null;
        }
    }

    /**
     * 准备备份目录
     *
     * @return 备份目录的Path对象
     */
    private Path prepareBackupDirectory(String targetFolderPath) throws IOException {
        Path targetPath = Paths.get(targetFolderPath);
        Path backupPath = targetPath.resolve(BACKUP_FOLDER_NAME);

        // 如果备份目录不存在，创建它
        if (!Files.exists(backupPath)) {
            Files.createDirectories(backupPath);
            System.out.println("创建备份目录: " + backupPath.toAbsolutePath());
        }

        return backupPath;
    }

    /**
     * 处理单个INI文件
     *
     * @param targetFolderPath 目标文件夹路径
     * @param fileName         文件名
     * @param backupDir        备份目录
     * @param newContent       新的文件内容
     *
     * @return 是否处理成功
     */
    private boolean processSingleFile(String targetFolderPath, String fileName,
                                      Path backupDir, String newContent) {
        Path targetFile = Paths.get(targetFolderPath, fileName);

        // 检查目标文件是否存在
        if (!Files.exists(targetFile)) {
            System.err.println("警告：目标文件不存在，跳过: " + targetFile);
            return false;
        }

        try {
            // 1. 生成备份文件名: gui -> 1734567890123.vmoptions.bak
            long timestamp = Instant.now().toEpochMilli();
            String backupFileName;
            if (GUI.equals(fileName)) {
                backupFileName = timestamp + ".vmoptions.bak";
            } else if (CONSOLE.equals(fileName)) {
                backupFileName = timestamp + "-console.vmoptions.bak";
            } else {
                backupFileName = timestamp + "-unkonwn" + fileName + ".bak";
            }

            Path backupFile = backupDir.resolve(backupFileName);

            // 2. 移动原文件到备份目录
            Files.move(targetFile, backupFile, StandardCopyOption.REPLACE_EXISTING);
            System.out.println("备份原文件: " + targetFile + " -> " + backupFile);

            // 3. 写入新内容到目标文件
            Files.writeString(targetFile, newContent);
            System.out.println("写入新配置: " + targetFile);

            return true;

        } catch (IOException e) {
            System.err.println("处理文件 " + fileName + " 时发生IO错误: " + e.getMessage());
            return false;
        }
    }
}
