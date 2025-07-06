#!/usr/bin/env python3
"""
任务管理功能测试脚本
"""
import os
import sys
import time
import uuid

# 添加项目根目录到系统路径
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

def create_test_tasks():
    """创建测试任务"""
    print("🚀 创建测试任务...")
    
    # 确保存储目录存在
    storage_dir = os.path.join(root_dir, "storage", "tasks")
    os.makedirs(storage_dir, exist_ok=True)
    
    # 创建多个测试任务
    test_tasks = [
        {
            "id": f"test-task-{uuid.uuid4().hex[:8]}",
            "files": {
                "final_video.mp4": "这是测试视频文件",
                "audio.mp3": "这是测试音频文件",
                "subtitle.srt": "1\n00:00:00,000 --> 00:00:05,000\n这是测试字幕内容\n\n2\n00:00:05,000 --> 00:00:10,000\n欢迎使用任务管理功能",
                "log.txt": f"任务生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n任务状态: 完成\n文件数量: 4",
                "config.json": '{"subject": "测试任务", "duration": 10, "quality": "high"}'
            }
        },
        {
            "id": f"demo-task-{uuid.uuid4().hex[:8]}",
            "files": {
                "output.mp4": "这是演示视频文件",
                "voice.mp3": "这是演示音频文件",
                "captions.srt": "1\n00:00:00,000 --> 00:00:03,000\n演示任务内容\n\n2\n00:00:03,000 --> 00:00:06,000\n任务管理功能测试",
                "debug.log": f"演示任务生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n状态: 成功\n类型: 演示"
            }
        },
        {
            "id": f"sample-task-{uuid.uuid4().hex[:8]}",
            "files": {
                "video.mp4": "这是样例视频文件",
                "background.mp3": "这是样例背景音乐",
                "subtitles.srt": "1\n00:00:00,000 --> 00:00:04,000\n样例任务演示\n\n2\n00:00:04,000 --> 00:00:08,000\n功能测试完成",
                "task_info.txt": f"样例任务信息\n创建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n状态: 完成\n类型: 样例"
            }
        }
    ]
    
    # 创建任务文件夹和文件
    for task in test_tasks:
        task_dir = os.path.join(storage_dir, task["id"])
        os.makedirs(task_dir, exist_ok=True)
        
        for filename, content in task["files"].items():
            file_path = os.path.join(task_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        print(f"✅ 创建测试任务: {task['id']}")
    
    print(f"🎉 成功创建了 {len(test_tasks)} 个测试任务")

def list_tasks():
    """列出所有任务"""
    print("\n📋 当前任务列表:")
    storage_dir = os.path.join(root_dir, "storage", "tasks")
    
    if not os.path.exists(storage_dir):
        print("❌ 任务目录不存在")
        return
    
    tasks = [d for d in os.listdir(storage_dir) if os.path.isdir(os.path.join(storage_dir, d))]
    
    if not tasks:
        print("📭 暂无任务")
        return
    
    for i, task_id in enumerate(tasks, 1):
        task_dir = os.path.join(storage_dir, task_id)
        files = [f for f in os.listdir(task_dir) if os.path.isfile(os.path.join(task_dir, f))]
        create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(task_dir)))
        
        print(f"  {i}. 🎬 {task_id}")
        print(f"     📅 创建时间: {create_time}")
        print(f"     📁 文件数量: {len(files)}")
        print(f"     📋 文件列表: {', '.join(files)}")

def cleanup_test_tasks():
    """清理测试任务"""
    print("\n🧹 清理测试任务...")
    storage_dir = os.path.join(root_dir, "storage", "tasks")
    
    if not os.path.exists(storage_dir):
        print("❌ 任务目录不存在")
        return
    
    import shutil
    tasks = [d for d in os.listdir(storage_dir) if os.path.isdir(os.path.join(storage_dir, d))]
    test_tasks = [t for t in tasks if t.startswith(('test-task-', 'demo-task-', 'sample-task-'))]
    
    if not test_tasks:
        print("📭 没有找到测试任务")
        return
    
    for task_id in test_tasks:
        task_dir = os.path.join(storage_dir, task_id)
        try:
            shutil.rmtree(task_dir)
            print(f"✅ 删除测试任务: {task_id}")
        except Exception as e:
            print(f"❌ 删除失败 {task_id}: {str(e)}")
    
    print(f"🎉 成功清理了 {len(test_tasks)} 个测试任务")

def main():
    """主函数"""
    print("🔧 任务管理功能测试脚本")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 创建测试任务")
        print("2. 列出所有任务")
        print("3. 清理测试任务")
        print("4. 启动WebUI (需要手动运行)")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == "1":
            create_test_tasks()
        elif choice == "2":
            list_tasks()
        elif choice == "3":
            cleanup_test_tasks()
        elif choice == "4":
            print("\n🚀 启动WebUI...")
            print("请在新的终端窗口中运行以下命令:")
            print(f"cd {root_dir}")
            print("python -m streamlit run webui/Main.py")
            print("\n然后在浏览器中打开 http://localhost:8501")
            print("在左侧侧边栏中可以看到任务管理功能")
        elif choice == "5":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    main() 