# 📋 任务管理功能说明

## 🎯 功能概述

新增的任务管理功能允许您在WebUI中直接管理所有生成的视频任务，包括查看、播放、下载和删除任务。

## 🚀 功能特性

### 1. 任务列表
- **查看所有任务**: 在侧边栏中显示所有已生成的任务
- **任务搜索**: 根据任务ID搜索特定任务
- **任务统计**: 显示任务总数和文件数量

### 2. 任务详情
- **基本信息**: 显示任务ID、创建时间、文件数量
- **文件分类**: 自动分类显示不同类型的文件
  - 🎬 视频文件 (mp4, avi, mov, mkv, flv, webm)
  - 🎵 音频文件 (mp3, wav, flac, aac, m4a)
  - 📝 字幕文件 (srt, ass, vtt)
  - 📷 图片文件 (jpg, jpeg, png, gif, bmp)
  - 📄 其他文件 (txt, log等)

### 3. 文件操作
- **视频播放**: 直接在浏览器中播放视频文件
- **音频播放**: 直接在浏览器中播放音频文件
- **字幕查看**: 查看字幕文件内容
- **文件管理**: 在系统文件管理器中打开任务文件夹

### 4. 任务管理
- **删除任务**: 删除不需要的任务（需要二次确认）
- **刷新列表**: 手动刷新任务列表
- **详情切换**: 展开/折叠任务详情

## 🎮 使用方法

### 1. 访问任务管理
1. 打开WebUI页面
2. 在左侧侧边栏中找到"任务管理"部分
3. 系统会自动加载所有已生成的任务

### 2. 查看任务
1. 点击任务展开器（🎬 任务ID...）
2. 查看任务基本信息
3. 点击"显示详情"查看文件列表

### 3. 播放文件
1. 在任务详情中找到视频或音频文件
2. 点击"播放视频"或直接点击音频文件
3. 文件会在浏览器中直接播放

### 4. 管理任务
1. **打开文件夹**: 点击"在文件管理器中打开"
2. **删除任务**: 点击"删除任务"，确认后删除
3. **刷新列表**: 点击"刷新任务列表"更新显示

## 🔧 技术实现

### 新增函数
- `get_all_tasks()`: 获取所有任务列表
- `get_file_type()`: 根据文件扩展名判断文件类型
- `format_file_size()`: 格式化文件大小显示
- `delete_task()`: 删除指定任务

### 界面组件
- 侧边栏任务管理界面
- 任务展开器和详情面板
- 文件播放和查看组件
- 操作按钮和确认对话框

## 📁 文件结构

```
storage/
└── tasks/
    └── [任务ID]/
        ├── final_video.mp4    # 生成的视频文件
        ├── audio.mp3          # 音频文件
        ├── subtitle.srt       # 字幕文件
        ├── log.txt           # 日志文件
        └── ...               # 其他相关文件
```

## 🌍 多语言支持

- **中文**: 完整的中文界面
- **英文**: 完整的英文界面
- **其他语言**: 可扩展支持

## 🛠 故障排除

### 常见问题
1. **任务列表为空**: 确保 `storage/tasks/` 目录存在且有任务文件
2. **文件播放失败**: 检查文件是否存在且格式正确
3. **删除任务失败**: 检查文件权限和磁盘空间

### 调试方法
1. 查看浏览器控制台错误信息
2. 检查文件路径是否正确
3. 确认文件权限设置

## 📝 更新日志

### v1.0.0 (2024-01-06)
- ✨ 新增任务管理功能
- 🎬 支持视频文件播放
- 🎵 支持音频文件播放
- 📝 支持字幕文件查看
- 🗂 支持文件分类显示
- 🔍 支持任务搜索功能
- 🗑 支持任务删除功能
- 🌍 支持中英文界面

## 🤝 贡献

如果您发现任何问题或有改进建议，请通过GitHub Issues提交反馈。

## 📄 许可证

本功能遵循项目的开源许可证。 