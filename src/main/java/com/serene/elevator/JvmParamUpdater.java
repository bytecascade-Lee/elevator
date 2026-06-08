package com.serene.elevator;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.Instant;
import java.util.Objects;

/**
 * Description: JVM参数更新器
 * <p>
 * 负责将新的JVM参数应用到目标INI文件中，并备份旧文件。
 * 更新策略：先拷贝原文件到备份目录，再写入新内容；若写入失败则自动从备份恢复，保证数据安全。
 * </p>
 *
 * @author Serene Lee
 * @date 2026/5/24
 */
public class JvmParamUpdater {

    /** 备份文件夹名称 */
    private static final String BACKUP_FOLDER_NAME = "back";

    /** GUI模式INI文件名，通过系统属性 {@code vmoptions.gui} 配置 */
    private final String guiFileName;
    /** 控制台模式INI文件名，通过系统属性 {@code vmoptions.console} 配置 */
    private final String consoleFileName;
    /** 需要处理的目标文件名数组 */
    private final String[] targetFiles;

    /**
     * 创建更新器，从系统属性读取目标文件名配置
     *
     * @throws NullPointerException 如果 {@code vmoptions.gui} 或 {@code vmoptions.console} 系统属性未配置
     */
    public JvmParamUpdater() {
        this.guiFileName = System.getProperty("vmoptions.gui");
        this.consoleFileName = System.getProperty("vmoptions.console");

        Objects.requireNonNull(guiFileName, "系统属性 \"vmoptions.gui\" 未配置，无法确定GUI模式文件名");
        Objects.requireNonNull(consoleFileName, "系统属性 \"vmoptions.console\" 未配置，无法确定控制台模式文件名");

        this.targetFiles = new String[]{guiFileName, consoleFileName};
    }

    /**
     * 更新JVM参数
     *
     * @param newVmoptionsPath new.vmoptions文件的完整路径
     * @param targetFolderPath 目标文件夹路径（包含INI文件的目录）
     *
     * @return 是否所有文件均更新成功
     */
    public boolean updateJvmParameters(String newVmoptionsPath, String targetFolderPath) {
        Objects.requireNonNull(newVmoptionsPath, "newVmoptionsPath must not be null");
        Objects.requireNonNull(targetFolderPath, "targetFolderPath must not be null");

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
            for (String fileName : targetFiles) {
                if (!processSingleFile(targetFolderPath, fileName, backupDir, newContent)) {
                    allSuccess = false;
                    System.err.println("警告：处理文件 " + fileName + " 时失败，请检查备份文件");
                }
            }

            return allSuccess;

        } catch (Exception e) {
            System.err.println("更新过程中发生异常: " + e.getMessage());
            return false;
        }
    }

    /**
     * 读取new.vmoptions文件内容（UTF-8），自动去除BOM标记
     *
     * @param filePath 文件路径
     *
     * @return 文件内容，读取失败返回null
     */
    private String readNewVmoptionsContent(String filePath) {
        Path path = Paths.get(filePath);
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(Files.newInputStream(path), StandardCharsets.UTF_8))) {
            StringBuilder content = new StringBuilder(512);
            String line;
            boolean isFirstLine = true;
            while ((line = reader.readLine()) != null) {
                if (isFirstLine && !line.isEmpty() && line.charAt(0) == '﻿') {
                    // 去除BOM标记
                    line = line.substring(1);
                }
                isFirstLine = false;
                content.append(line).append(System.lineSeparator());
            }
            return content.toString();
        } catch (IOException e) {
            System.err.println("读取new.vmoptions文件失败: " + e.getMessage());
            return null;
        }
    }

    /**
     * 准备备份目录，如果不存在则创建
     *
     * @param targetFolderPath 目标文件夹路径
     *
     * @return 备份目录的Path对象
     *
     * @throws IOException 如果创建备份目录失败
     */
    private Path prepareBackupDirectory(String targetFolderPath) throws IOException {
        Path backupPath = Paths.get(targetFolderPath, BACKUP_FOLDER_NAME);
        if (Files.notExists(backupPath)) {
            Files.createDirectories(backupPath);
            System.out.println("创建备份目录: " + backupPath.toAbsolutePath());
        }
        return backupPath;
    }

    /**
     * 处理单个INI文件：先拷贝备份，再写入新内容，写入失败时自动从备份恢复
     * <p>
     * 流程：
     * <ol>
     *   <li>拷贝原文件到备份目录（原文件保留不变）</li>
     *   <li>写入新内容到原文件路径</li>
     *   <li>若写入成功 → 返回true（备份保留以供回滚）</li>
     *   <li>若写入失败 → 从备份恢复原文件，返回false</li>
     * </ol>
     * 这种策略避免了先move再write导致原文件丢失的风险。
     * </p>
     *
     * @param targetFolderPath 目标文件夹路径
     * @param fileName         目标文件名
     * @param backupDir        备份目录
     * @param newContent       新的文件内容
     *
     * @return 是否处理成功
     */
    private boolean processSingleFile(String targetFolderPath, String fileName,
                                      Path backupDir, String newContent) {
        Path targetFile = Paths.get(targetFolderPath, fileName);

        // 检查目标文件是否存在
        if (Files.notExists(targetFile)) {
            System.err.println("警告：目标文件不存在，跳过: " + targetFile);
            return false;
        }

        try {
            // 1. 生成备份文件名
            long timestamp = Instant.now().toEpochMilli();
            String suffix = guiFileName.equals(fileName) ? "" : "-console";
            String backupFileName = timestamp + suffix + ".vmoptions.bak";
            Path backupFile = backupDir.resolve(backupFileName);

            // 2. 拷贝原文件到备份目录（原文件保留不变）
            Files.copy(targetFile, backupFile, StandardCopyOption.REPLACE_EXISTING);
            System.out.println("已备份原文件: " + targetFile + " -> " + backupFile);

            // 3. 写入新内容到目标文件
            try {
                Files.writeString(targetFile, newContent, StandardCharsets.UTF_8);
                System.out.println("已写入新配置: " + targetFile);
                return true;
            } catch (IOException e) {
                // 写入失败，尝试从备份恢复
                System.err.println("写入新内容失败，正在从备份恢复: " + e.getMessage());
                try {
                    Files.copy(backupFile, targetFile, StandardCopyOption.REPLACE_EXISTING);
                    System.out.println("已从备份恢复: " + backupFile + " -> " + targetFile);
                } catch (IOException restoreEx) {
                    System.err.println("从备份恢复失败，请手动从以下位置恢复: " + backupFile);
                    System.err.println("恢复失败原因: " + restoreEx.getMessage());
                }
                return false;
            }

        } catch (IOException e) {
            System.err.println("处理文件 " + fileName + " 时发生IO错误: " + e.getMessage());
            return false;
        }
    }
}
