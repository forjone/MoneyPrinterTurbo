#!/usr/bin/env python3
"""
视频质量测试脚本
用于验证视频质量优化效果
"""

import os
import time
from pathlib import Path
from app.services.video import diagnose_video_quality, VideoQualityConfig
from app.services.task import start
from app.models.schema import VideoParams, MaterialInfo

def test_video_quality_optimization():
    """
    测试视频质量优化效果
    """
    print("🎬 开始视频质量测试...")
    
    # 测试配置
    test_configs = [
        {
            "name": "快速模式",
            "temp_bitrate": "3000k",
            "temp_preset": "faster",
            "final_bitrate": "6000k",
            "final_preset": "medium",
            "final_crf": "20"
        },
        {
            "name": "平衡模式（默认）",
            "temp_bitrate": "4000k",
            "temp_preset": "faster",
            "final_bitrate": "8000k",
            "final_preset": "slow",
            "final_crf": "18"
        },
        {
            "name": "高质量模式",
            "temp_bitrate": "6000k",
            "temp_preset": "medium",
            "final_bitrate": "10000k",
            "final_preset": "slower",
            "final_crf": "16"
        }
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n🧪 测试配置: {config['name']}")
        
        # 临时修改配置
        original_config = {
            "temp_bitrate": VideoQualityConfig.TEMP_BITRATE,
            "temp_preset": VideoQualityConfig.TEMP_PRESET,
            "final_bitrate": VideoQualityConfig.FINAL_BITRATE,
            "final_preset": VideoQualityConfig.FINAL_PRESET,
            "final_crf": VideoQualityConfig.FINAL_CRF
        }
        
        VideoQualityConfig.TEMP_BITRATE = config["temp_bitrate"]
        VideoQualityConfig.TEMP_PRESET = config["temp_preset"]
        VideoQualityConfig.FINAL_BITRATE = config["final_bitrate"]
        VideoQualityConfig.FINAL_PRESET = config["final_preset"]
        VideoQualityConfig.FINAL_CRF = config["final_crf"]
        
        try:
            # 测试开始时间
            start_time = time.time()
            
            # 创建测试任务
            task_id = f"quality_test_{config['name'].replace(' ', '_')}"
            
            # 使用测试素材
            test_materials = [
                MaterialInfo(url="test/resources/1.png"),
                MaterialInfo(url="test/resources/2.png"),
                MaterialInfo(url="test/resources/3.png")
            ]
            
            params = VideoParams(
                video_subject="视频质量测试",
                video_script="这是一个视频质量测试脚本，用于验证不同编码参数对视频质量的影响。",
                video_source="local",
                video_materials=test_materials,
                video_clip_duration=3,
                video_count=1,
                n_threads=4
            )
            
            # 只运行到视频生成步骤
            result = start(task_id, params, stop_at="video")
            
            # 测试结束时间
            end_time = time.time()
            processing_time = end_time - start_time
            
            # 分析生成的视频
            video_path = f"storage/tasks/{task_id}/final-1.mp4"
            if os.path.exists(video_path):
                video_info = diagnose_video_quality(video_path)
                file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
                
                test_result = {
                    "config": config["name"],
                    "processing_time": processing_time,
                    "file_size_mb": file_size,
                    "video_info": video_info,
                    "success": True
                }
                
                print(f"✅ 测试完成:")
                print(f"   处理时间: {processing_time:.2f}秒")
                print(f"   文件大小: {file_size:.2f}MB")
                print(f"   视频信息: {video_info}")
                
            else:
                test_result = {
                    "config": config["name"],
                    "processing_time": processing_time,
                    "success": False,
                    "error": "视频文件未生成"
                }
                print(f"❌ 测试失败: 视频文件未生成")
                
        except Exception as e:
            test_result = {
                "config": config["name"],
                "success": False,
                "error": str(e)
            }
            print(f"❌ 测试失败: {str(e)}")
            
        finally:
            # 恢复原始配置
            VideoQualityConfig.TEMP_BITRATE = original_config["temp_bitrate"]
            VideoQualityConfig.TEMP_PRESET = original_config["temp_preset"]
            VideoQualityConfig.FINAL_BITRATE = original_config["final_bitrate"]
            VideoQualityConfig.FINAL_PRESET = original_config["final_preset"]
            VideoQualityConfig.FINAL_CRF = original_config["final_crf"]
            
        results.append(test_result)
    
    # 生成测试报告
    print("\n📊 测试报告:")
    print("=" * 60)
    
    for result in results:
        if result["success"]:
            print(f"配置: {result['config']}")
            print(f"处理时间: {result['processing_time']:.2f}秒")
            print(f"文件大小: {result['file_size_mb']:.2f}MB")
            print("-" * 40)
        else:
            print(f"配置: {result['config']} - 失败: {result['error']}")
    
    return results

def compare_quality_metrics(video_path_1, video_path_2):
    """
    比较两个视频的质量指标
    """
    print(f"\n🔍 比较视频质量:")
    
    info1 = diagnose_video_quality(video_path_1)
    info2 = diagnose_video_quality(video_path_2)
    
    if info1 and info2:
        print(f"视频1: {info1}")
        print(f"视频2: {info2}")
        
        # 计算文件大小差异
        size1 = os.path.getsize(video_path_1) / (1024 * 1024)
        size2 = os.path.getsize(video_path_2) / (1024 * 1024)
        
        print(f"\n📏 文件大小比较:")
        print(f"视频1: {size1:.2f}MB")
        print(f"视频2: {size2:.2f}MB")
        print(f"差异: {((size2 - size1) / size1 * 100):.1f}%")
        
        return {
            "video1": info1,
            "video2": info2,
            "size_difference_percent": ((size2 - size1) / size1 * 100)
        }
    
    return None

if __name__ == "__main__":
    # 运行质量测试
    test_results = test_video_quality_optimization()
    
    # 如果有多个成功的测试结果，进行比较
    successful_results = [r for r in test_results if r["success"]]
    
    if len(successful_results) >= 2:
        print("\n🆚 质量比较分析:")
        for i in range(len(successful_results) - 1):
            result1 = successful_results[i]
            result2 = successful_results[i + 1]
            
            print(f"\n比较 {result1['config']} vs {result2['config']}:")
            print(f"处理时间: {result1['processing_time']:.2f}s vs {result2['processing_time']:.2f}s")
            print(f"文件大小: {result1['file_size_mb']:.2f}MB vs {result2['file_size_mb']:.2f}MB")
            
            time_diff = ((result2['processing_time'] - result1['processing_time']) / result1['processing_time'] * 100)
            size_diff = ((result2['file_size_mb'] - result1['file_size_mb']) / result1['file_size_mb'] * 100)
            
            print(f"时间差异: {time_diff:.1f}%")
            print(f"大小差异: {size_diff:.1f}%")
    
    print("\n🎯 建议:")
    print("1. 如果追求速度，选择快速模式")
    print("2. 如果需要平衡质量和速度，选择平衡模式（推荐）")
    print("3. 如果追求最佳质量，选择高质量模式")
    print("4. 可以根据具体需求调整 VideoQualityConfig 中的参数") 