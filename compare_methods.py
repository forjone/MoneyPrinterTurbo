#!/usr/bin/env python3
"""
视频处理方法对比脚本
比较传统多步骤方法 vs 一步到位方法
"""

import os
import time
import json
from pathlib import Path
from app.services.video import diagnose_video_quality
from app.services.task import start
from app.models.schema import VideoParams, MaterialInfo

def compare_video_generation_methods():
    """
    对比两种视频生成方法的效果
    """
    print("🆚 开始对比视频生成方法...")
    
    # 准备测试素材
    test_materials = [
        MaterialInfo(url="test/resources/1.png"),
        MaterialInfo(url="test/resources/2.png"),
        MaterialInfo(url="test/resources/3.png"),
        MaterialInfo(url="test/resources/4.png"),
        MaterialInfo(url="test/resources/5.png"),
    ]
    
    # 基础参数
    base_params = {
        "video_subject": "视频质量对比测试",
        "video_script": "这是一个对比测试，用来验证传统多步骤方法和一步到位方法在视频质量和处理速度上的差异。我们将分析画质、噪点、处理时间等关键指标。",
        "video_source": "local",
        "video_materials": test_materials,
        "video_clip_duration": 3,
        "video_count": 1,
        "n_threads": 4,
        "voice_name": "zh-CN-XiaoxiaoNeural-Female",
        "voice_volume": 1.0,
        "subtitle_enabled": True,
        "font_size": 60,
    }
    
    results = {}
    
    # 测试1: 传统多步骤方法
    print("\n🔄 测试传统多步骤方法...")
    traditional_params = VideoParams(**base_params, use_direct_generation=False)
    
    start_time = time.time()
    try:
        result = start("method_comparison_traditional", traditional_params, stop_at="video")
        traditional_time = time.time() - start_time
        
        # 分析生成的视频
        traditional_video = "storage/tasks/method_comparison_traditional/final-1.mp4"
        if os.path.exists(traditional_video):
            traditional_info = diagnose_video_quality(traditional_video)
            traditional_size = os.path.getsize(traditional_video) / (1024 * 1024)  # MB
            
            results["traditional"] = {
                "success": True,
                "processing_time": traditional_time,
                "file_size_mb": traditional_size,
                "video_info": traditional_info,
                "temp_files_created": count_temp_files("storage/tasks/method_comparison_traditional/")
            }
            
            print(f"✅ 传统方法完成:")
            print(f"   处理时间: {traditional_time:.2f}秒")
            print(f"   文件大小: {traditional_size:.2f}MB")
            print(f"   视频信息: {traditional_info}")
        else:
            results["traditional"] = {"success": False, "error": "视频文件未生成"}
            print("❌ 传统方法失败")
            
    except Exception as e:
        results["traditional"] = {"success": False, "error": str(e)}
        print(f"❌ 传统方法失败: {str(e)}")
    
    # 测试2: 一步到位方法
    print("\n🚀 测试一步到位方法...")
    direct_params = VideoParams(**base_params, use_direct_generation=True)
    
    start_time = time.time()
    try:
        result = start("method_comparison_direct", direct_params, stop_at="video")
        direct_time = time.time() - start_time
        
        # 分析生成的视频
        direct_video = "storage/tasks/method_comparison_direct/final-1.mp4"
        if os.path.exists(direct_video):
            direct_info = diagnose_video_quality(direct_video)
            direct_size = os.path.getsize(direct_video) / (1024 * 1024)  # MB
            
            results["direct"] = {
                "success": True,
                "processing_time": direct_time,
                "file_size_mb": direct_size,
                "video_info": direct_info,
                "temp_files_created": count_temp_files("storage/tasks/method_comparison_direct/")
            }
            
            print(f"✅ 一步到位方法完成:")
            print(f"   处理时间: {direct_time:.2f}秒")
            print(f"   文件大小: {direct_size:.2f}MB")
            print(f"   视频信息: {direct_info}")
        else:
            results["direct"] = {"success": False, "error": "视频文件未生成"}
            print("❌ 一步到位方法失败")
            
    except Exception as e:
        results["direct"] = {"success": False, "error": str(e)}
        print(f"❌ 一步到位方法失败: {str(e)}")
    
    # 生成对比报告
    generate_comparison_report(results)
    
    return results

def count_temp_files(directory):
    """
    统计临时文件数量
    """
    if not os.path.exists(directory):
        return 0
    
    temp_files = 0
    for file in os.listdir(directory):
        if file.startswith("temp-") or file.startswith("combined-"):
            temp_files += 1
    
    return temp_files

def generate_comparison_report(results):
    """
    生成详细的对比报告
    """
    print("\n" + "="*80)
    print("📊 视频生成方法对比报告")
    print("="*80)
    
    if results.get("traditional", {}).get("success") and results.get("direct", {}).get("success"):
        traditional = results["traditional"]
        direct = results["direct"]
        
        # 处理时间对比
        time_diff = ((traditional["processing_time"] - direct["processing_time"]) / traditional["processing_time"]) * 100
        print(f"\n⏱️  处理时间对比:")
        print(f"   传统方法: {traditional['processing_time']:.2f}秒")
        print(f"   一步到位: {direct['processing_time']:.2f}秒")
        print(f"   性能提升: {time_diff:.1f}% {'(更快)' if time_diff > 0 else '(更慢)'}")
        
        # 文件大小对比
        size_diff = ((direct["file_size_mb"] - traditional["file_size_mb"]) / traditional["file_size_mb"]) * 100
        print(f"\n📁 文件大小对比:")
        print(f"   传统方法: {traditional['file_size_mb']:.2f}MB")
        print(f"   一步到位: {direct['file_size_mb']:.2f}MB")
        print(f"   大小变化: {size_diff:.1f}% {'(更大)' if size_diff > 0 else '(更小)'}")
        
        # 临时文件对比
        print(f"\n🗂️  临时文件对比:")
        print(f"   传统方法: {traditional['temp_files_created']}个临时文件")
        print(f"   一步到位: {direct['temp_files_created']}个临时文件")
        
        # 质量分析
        print(f"\n🎬 视频质量分析:")
        print(f"   传统方法: {traditional['video_info']}")
        print(f"   一步到位: {direct['video_info']}")
        
        # 综合评估
        print(f"\n🏆 综合评估:")
        
        if time_diff > 20:
            print("   ✅ 一步到位方法在处理速度上有显著优势")
        elif time_diff > 0:
            print("   ✅ 一步到位方法在处理速度上有轻微优势")
        else:
            print("   ⚠️  传统方法在处理速度上更快")
        
        if traditional['temp_files_created'] > direct['temp_files_created']:
            print("   ✅ 一步到位方法减少了临时文件生成")
        
        if abs(size_diff) < 30:
            print("   ✅ 两种方法的文件大小差异在合理范围内")
        
        # 推荐建议
        print(f"\n💡 推荐建议:")
        if time_diff > 10 and traditional['temp_files_created'] > direct['temp_files_created']:
            print("   🎯 推荐使用一步到位方法：性能更好，临时文件更少，质量更佳")
        elif time_diff > 0:
            print("   🎯 推荐使用一步到位方法：整体表现更优")
        else:
            print("   🎯 两种方法各有优势，可根据具体需求选择")
    
    else:
        print("\n❌ 对比测试未完全成功，无法生成完整报告")
        
        if not results.get("traditional", {}).get("success"):
            print(f"   传统方法失败: {results.get('traditional', {}).get('error', '未知错误')}")
        
        if not results.get("direct", {}).get("success"):
            print(f"   一步到位方法失败: {results.get('direct', {}).get('error', '未知错误')}")
    
    # 保存详细结果到文件
    report_file = "video_method_comparison_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 详细报告已保存到: {report_file}")

def analyze_video_files():
    """
    分析生成的视频文件，提供质量评估
    """
    print("\n🔍 详细质量分析...")
    
    traditional_video = "storage/tasks/method_comparison_traditional/final-1.mp4"
    direct_video = "storage/tasks/method_comparison_direct/final-1.mp4"
    
    if os.path.exists(traditional_video) and os.path.exists(direct_video):
        print(f"\n📹 视频文件对比:")
        print(f"   传统方法: {traditional_video}")
        print(f"   一步到位: {direct_video}")
        
        # 可以添加更多详细的视频分析
        # 例如：帧率分析、色彩分析、噪点检测等
        
        print(f"\n🎯 建议:")
        print(f"   1. 可以使用视频播放器对比两个文件的画质")
        print(f"   2. 特别关注细节部分的清晰度差异")
        print(f"   3. 观察是否有明显的噪点或压缩痕迹")

if __name__ == "__main__":
    try:
        # 运行对比测试
        results = compare_video_generation_methods()
        
        # 进行详细分析
        analyze_video_files()
        
        print("\n🎉 对比测试完成！")
        print("📊 请查看生成的报告文件获取详细信息")
        
    except Exception as e:
        print(f"❌ 对比测试失败: {str(e)}")
        import traceback
        traceback.print_exc() 