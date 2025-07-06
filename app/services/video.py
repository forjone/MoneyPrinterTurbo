import glob
import itertools
import os
import random
import gc
import shutil
from typing import List
from loguru import logger
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    afx,
    concatenate_videoclips,
)
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import ImageFont

from app.models import const
from app.models.schema import (
    MaterialInfo,
    VideoAspect,
    VideoConcatMode,
    VideoParams,
    VideoTransitionMode,
)
from app.services.utils import video_effects
from app.utils import utils

# 视频质量配置 - 可根据需要调整
class VideoQualityConfig:
    # 临时文件编码设置
    TEMP_BITRATE = "4000k"  # 临时文件码率
    TEMP_PRESET = "faster"  # 临时文件预设
    
    # 合并文件编码设置
    MERGE_BITRATE = "7000k"  # 合并文件码率
    MERGE_PRESET = "medium"  # 合并文件预设
    
    # 最终文件编码设置
    FINAL_BITRATE = "8000k"  # 最终文件码率
    FINAL_PRESET = "slow"  # 最终文件预设
    FINAL_CRF = "18"  # CRF值，18为高质量
    
    # 图片处理设置
    IMAGE_BITRATE = "6000k"  # 图片转视频码率
    IMAGE_PRESET = "medium"  # 图片转视频预设

# 视频质量诊断工具
def diagnose_video_quality(video_path: str):
    """
    诊断视频质量问题
    """
    try:
        clip = VideoFileClip(video_path)
        info = {
            "path": video_path,
            "duration": clip.duration,
            "fps": clip.fps,
            "size": clip.size,
            "bitrate": getattr(clip, 'bitrate', 'Unknown'),
            "codec": getattr(clip, 'codec', 'Unknown'),
        }
        clip.close()
        logger.info(f"视频质量诊断: {utils.to_json(info)}")
        return info
    except Exception as e:
        logger.error(f"视频质量诊断失败: {str(e)}")
        return None

class SubClippedVideoClip:
    def __init__(self, file_path, start_time=None, end_time=None, width=None, height=None, duration=None):
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time
        self.width = width
        self.height = height
        if duration is None:
            self.duration = end_time - start_time
        else:
            self.duration = duration

    def __str__(self):
        return f"SubClippedVideoClip(file_path={self.file_path}, start_time={self.start_time}, end_time={self.end_time}, duration={self.duration}, width={self.width}, height={self.height})"


audio_codec = "aac"
video_codec = "libx264"
fps = 30

def close_clip(clip):
    if clip is None:
        return
        
    try:
        # close main resources
        if hasattr(clip, 'reader') and clip.reader is not None:
            clip.reader.close()
            
        # close audio resources
        if hasattr(clip, 'audio') and clip.audio is not None:
            if hasattr(clip.audio, 'reader') and clip.audio.reader is not None:
                clip.audio.reader.close()
            del clip.audio
            
        # close mask resources
        if hasattr(clip, 'mask') and clip.mask is not None:
            if hasattr(clip.mask, 'reader') and clip.mask.reader is not None:
                clip.mask.reader.close()
            del clip.mask
            
        # handle child clips in composite clips
        if hasattr(clip, 'clips') and clip.clips:
            for child_clip in clip.clips:
                if child_clip is not clip:  # avoid possible circular references
                    close_clip(child_clip)
            
        # clear clip list
        if hasattr(clip, 'clips'):
            clip.clips = []
            
    except Exception as e:
        logger.error(f"failed to close clip: {str(e)}")
    
    del clip
    gc.collect()

def delete_files(files: List[str] | str):
    if isinstance(files, str):
        files = [files]
        
    for file in files:
        try:
            os.remove(file)
        except:
            pass

def get_bgm_file(bgm_type: str = "random", bgm_file: str = ""):
    if not bgm_type:
        return ""

    if bgm_file and os.path.exists(bgm_file):
        return bgm_file

    if bgm_type == "random":
        suffix = "*.mp3"
        song_dir = utils.song_dir()
        files = glob.glob(os.path.join(song_dir, suffix))
        return random.choice(files)

    return ""


def combine_videos(
    combined_video_path: str,
    video_paths: List[str],
    audio_file: str,
    video_aspect: VideoAspect = VideoAspect.portrait,
    video_concat_mode: VideoConcatMode = VideoConcatMode.random,
    video_transition_mode: VideoTransitionMode = None,
    max_clip_duration: int = 5,
    threads: int = 2,
) -> str:
    audio_clip = AudioFileClip(audio_file)
    audio_duration = audio_clip.duration
    logger.info(f"audio duration: {audio_duration} seconds")
    # Required duration of each clip
    req_dur = audio_duration / len(video_paths)
    req_dur = max_clip_duration
    logger.info(f"maximum clip duration: {req_dur} seconds")
    output_dir = os.path.dirname(combined_video_path)

    aspect = VideoAspect(video_aspect)
    video_width, video_height = aspect.to_resolution()

    processed_clips = []
    subclipped_items = []
    video_duration = 0
    for video_path in video_paths:
        clip = VideoFileClip(video_path)
        clip_duration = clip.duration
        clip_w, clip_h = clip.size
        close_clip(clip)
        
        start_time = 0

        while start_time < clip_duration:
            end_time = min(start_time + max_clip_duration, clip_duration)            
            if clip_duration - start_time >= max_clip_duration:
                subclipped_items.append(SubClippedVideoClip(file_path= video_path, start_time=start_time, end_time=end_time, width=clip_w, height=clip_h))
            start_time = end_time    
            if video_concat_mode.value == VideoConcatMode.sequential.value:
                break

    # random subclipped_items order
    if video_concat_mode.value == VideoConcatMode.random.value:
        random.shuffle(subclipped_items)
        
    logger.debug(f"total subclipped items: {len(subclipped_items)}")
    
    # Add downloaded clips over and over until the duration of the audio (max_duration) has been reached
    for i, subclipped_item in enumerate(subclipped_items):
        if video_duration > audio_duration:
            break
        
        logger.debug(f"processing clip {i+1}: {subclipped_item.width}x{subclipped_item.height}, current duration: {video_duration:.2f}s, remaining: {audio_duration - video_duration:.2f}s")
        
        try:
            clip = VideoFileClip(subclipped_item.file_path).subclipped(subclipped_item.start_time, subclipped_item.end_time)
            clip_duration = clip.duration
            # Not all videos are same size, so we need to resize them
            clip_w, clip_h = clip.size
            if clip_w != video_width or clip_h != video_height:
                clip_ratio = clip.w / clip.h
                video_ratio = video_width / video_height
                logger.debug(f"resizing clip, source: {clip_w}x{clip_h}, ratio: {clip_ratio:.2f}, target: {video_width}x{video_height}, ratio: {video_ratio:.2f}")
                
                if clip_ratio == video_ratio:
                    clip = clip.resized(new_size=(video_width, video_height))
                else:
                    if clip_ratio > video_ratio:
                        scale_factor = video_width / clip_w
                    else:
                        scale_factor = video_height / clip_h

                    new_width = int(clip_w * scale_factor)
                    new_height = int(clip_h * scale_factor)

                    background = ColorClip(size=(video_width, video_height), color=(0, 0, 0)).with_duration(clip_duration)
                    clip_resized = clip.resized(new_size=(new_width, new_height)).with_position("center")
                    clip = CompositeVideoClip([background, clip_resized])
                    
            shuffle_side = random.choice(["left", "right", "top", "bottom"])
            if video_transition_mode.value == VideoTransitionMode.none.value:
                clip = clip
            elif video_transition_mode.value == VideoTransitionMode.fade_in.value:
                clip = video_effects.fadein_transition(clip, 1)
            elif video_transition_mode.value == VideoTransitionMode.fade_out.value:
                clip = video_effects.fadeout_transition(clip, 1)
            elif video_transition_mode.value == VideoTransitionMode.slide_in.value:
                clip = video_effects.slidein_transition(clip, 1, shuffle_side)
            elif video_transition_mode.value == VideoTransitionMode.slide_out.value:
                clip = video_effects.slideout_transition(clip, 1, shuffle_side)
            elif video_transition_mode.value == VideoTransitionMode.shuffle.value:
                transition_funcs = [
                    lambda c: video_effects.fadein_transition(c, 1),
                    lambda c: video_effects.fadeout_transition(c, 1),
                    lambda c: video_effects.slidein_transition(c, 1, shuffle_side),
                    lambda c: video_effects.slideout_transition(c, 1, shuffle_side),
                ]
                shuffle_transition = random.choice(transition_funcs)
                clip = shuffle_transition(clip)

            if clip.duration > max_clip_duration:
                clip = clip.subclipped(0, max_clip_duration)
                
            # wirte clip to temp file
            clip_file = f"{output_dir}/temp-clip-{i+1}.mp4"
            clip.write_videofile(
                clip_file, 
                logger=None, 
                fps=fps, 
                codec=video_codec, 
                bitrate=VideoQualityConfig.TEMP_BITRATE,  # 使用配置的临时文件码率
                preset=VideoQualityConfig.TEMP_PRESET,  # 使用配置的临时文件预设
                threads=threads
            )
            
            close_clip(clip)
        
            processed_clips.append(SubClippedVideoClip(file_path=clip_file, duration=clip.duration, width=clip_w, height=clip_h))
            video_duration += clip.duration
            
        except Exception as e:
            logger.error(f"failed to process clip: {str(e)}")
    
    # loop processed clips until the video duration matches or exceeds the audio duration.
    if video_duration < audio_duration:
        logger.warning(f"video duration ({video_duration:.2f}s) is shorter than audio duration ({audio_duration:.2f}s), looping clips to match audio length.")
        base_clips = processed_clips.copy()
        for clip in itertools.cycle(base_clips):
            if video_duration >= audio_duration:
                break
            processed_clips.append(clip)
            video_duration += clip.duration
        logger.info(f"video duration: {video_duration:.2f}s, audio duration: {audio_duration:.2f}s, looped {len(processed_clips)-len(base_clips)} clips")
     
    # 优化：使用一次性合并替代逐个合并，大幅提升性能
    logger.info("starting optimized clip merging process")
    if not processed_clips:
        logger.warning("no clips available for merging")
        return combined_video_path
    
    # if there is only one clip, use it directly
    if len(processed_clips) == 1:
        logger.info("using single clip directly")
        shutil.copy(processed_clips[0].file_path, combined_video_path)
        delete_files([processed_clips[0].file_path])
        logger.info("video combining completed")
        return combined_video_path
    
    # 一次性加载所有视频片段并合并
    logger.info(f"loading {len(processed_clips)} clips for batch merging")
    video_clips = []
    
    try:
        # 批量加载所有视频片段
        for i, clip_info in enumerate(processed_clips):
            logger.debug(f"loading clip {i+1}/{len(processed_clips)}: {clip_info.file_path}")
            clip = VideoFileClip(clip_info.file_path)
            video_clips.append(clip)
        
        # 一次性合并所有片段
        logger.info("concatenating all clips at once...")
        merged_clip = concatenate_videoclips(video_clips)
        
        # 写入最终合并结果
        merged_clip.write_videofile(
            filename=combined_video_path,
            threads=threads,
            logger=None,
            temp_audiofile_path=output_dir,
            audio_codec=audio_codec,
            fps=fps,
            bitrate=VideoQualityConfig.MERGE_BITRATE,  # 使用配置的合并文件码率
            preset=VideoQualityConfig.MERGE_PRESET,  # 使用配置的合并文件预设
        )
        
        # 清理资源
        for clip in video_clips:
            close_clip(clip)
        close_clip(merged_clip)
        
        logger.info("video combining completed successfully")
        
    except Exception as e:
        logger.error(f"failed to merge clips: {str(e)}")
        # 清理可能的残留资源
        for clip in video_clips:
            try:
                close_clip(clip)
            except:
                pass
        return None
    
    # 清理临时文件
    clip_files = [clip.file_path for clip in processed_clips]
    delete_files(clip_files)
            
    logger.info("video combining completed")
    return combined_video_path


def wrap_text(text, max_width, font="Arial", fontsize=60):
    # Create ImageFont
    font = ImageFont.truetype(font, fontsize)

    def get_text_size(inner_text):
        inner_text = inner_text.strip()
        left, top, right, bottom = font.getbbox(inner_text)
        return right - left, bottom - top

    width, height = get_text_size(text)
    if width <= max_width:
        return text, height

    processed = True

    _wrapped_lines_ = []
    words = text.split(" ")
    _txt_ = ""
    for word in words:
        _before = _txt_
        _txt_ += f"{word} "
        _width, _height = get_text_size(_txt_)
        if _width <= max_width:
            continue
        else:
            if _txt_.strip() == word.strip():
                processed = False
                break
            _wrapped_lines_.append(_before)
            _txt_ = f"{word} "
    _wrapped_lines_.append(_txt_)
    if processed:
        _wrapped_lines_ = [line.strip() for line in _wrapped_lines_]
        result = "\n".join(_wrapped_lines_).strip()
        height = len(_wrapped_lines_) * height
        return result, height

    _wrapped_lines_ = []
    chars = list(text)
    _txt_ = ""
    for word in chars:
        _txt_ += word
        _width, _height = get_text_size(_txt_)
        if _width <= max_width:
            continue
        else:
            _wrapped_lines_.append(_txt_)
            _txt_ = ""
    _wrapped_lines_.append(_txt_)
    result = "\n".join(_wrapped_lines_).strip()
    height = len(_wrapped_lines_) * height
    return result, height


def generate_video(
    video_path: str,
    audio_path: str,
    subtitle_path: str,
    output_file: str,
    params: VideoParams,
):
    aspect = VideoAspect(params.video_aspect)
    video_width, video_height = aspect.to_resolution()

    logger.info(f"generating video: {video_width} x {video_height}")
    logger.info(f"  ① video: {video_path}")
    logger.info(f"  ② audio: {audio_path}")
    logger.info(f"  ③ subtitle: {subtitle_path}")
    logger.info(f"  ④ output: {output_file}")

    # https://github.com/harry0703/MoneyPrinterTurbo/issues/217
    # PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'final-1.mp4.tempTEMP_MPY_wvf_snd.mp3'
    # write into the same directory as the output file
    output_dir = os.path.dirname(output_file)

    font_path = ""
    if params.subtitle_enabled:
        if not params.font_name:
            params.font_name = "STHeitiMedium.ttc"
        font_path = os.path.join(utils.font_dir(), params.font_name)
        if os.name == "nt":
            font_path = font_path.replace("\\", "/")

        logger.info(f"  ⑤ font: {font_path}")

    def create_text_clip(subtitle_item):
        params.font_size = int(params.font_size)
        params.stroke_width = int(params.stroke_width)
        phrase = subtitle_item[1]
        max_width = video_width * 0.9
        wrapped_txt, txt_height = wrap_text(
            phrase, max_width=max_width, font=font_path, fontsize=params.font_size
        )
        interline = int(params.font_size * 0.25)
        size=(int(max_width), int(txt_height + params.font_size * 0.25 + (interline * (wrapped_txt.count("\n") + 1))))

        _clip = TextClip(
            text=wrapped_txt,
            font=font_path,
            font_size=params.font_size,
            color=params.text_fore_color,
            bg_color=params.text_background_color,
            stroke_color=params.stroke_color,
            stroke_width=params.stroke_width,
            # interline=interline,
            # size=size,
        )
        duration = subtitle_item[0][1] - subtitle_item[0][0]
        _clip = _clip.with_start(subtitle_item[0][0])
        _clip = _clip.with_end(subtitle_item[0][1])
        _clip = _clip.with_duration(duration)
        if params.subtitle_position == "bottom":
            _clip = _clip.with_position(("center", video_height * 0.95 - _clip.h))
        elif params.subtitle_position == "top":
            _clip = _clip.with_position(("center", video_height * 0.05))
        elif params.subtitle_position == "custom":
            # Ensure the subtitle is fully within the screen bounds
            margin = 10  # Additional margin, in pixels
            max_y = video_height - _clip.h - margin
            min_y = margin
            custom_y = (video_height - _clip.h) * (params.custom_position / 100)
            custom_y = max(
                min_y, min(custom_y, max_y)
            )  # Constrain the y value within the valid range
            _clip = _clip.with_position(("center", custom_y))
        else:  # center
            _clip = _clip.with_position(("center", "center"))
        return _clip

    video_clip = VideoFileClip(video_path).without_audio()
    audio_clip = AudioFileClip(audio_path).with_effects(
        [afx.MultiplyVolume(params.voice_volume)]
    )

    def make_textclip(text):
        return TextClip(
            text=text,
            font=font_path,
            font_size=params.font_size,
        )

    if subtitle_path and os.path.exists(subtitle_path):
        sub = SubtitlesClip(
            subtitles=subtitle_path, encoding="utf-8", make_textclip=make_textclip
        )
        text_clips = []
        for item in sub.subtitles:
            clip = create_text_clip(subtitle_item=item)
            text_clips.append(clip)
        video_clip = CompositeVideoClip([video_clip, *text_clips])

    bgm_file = get_bgm_file(bgm_type=params.bgm_type, bgm_file=params.bgm_file)
    if bgm_file:
        try:
            bgm_clip = AudioFileClip(bgm_file).with_effects(
                [
                    afx.MultiplyVolume(params.bgm_volume),
                    afx.AudioFadeOut(3),
                    afx.AudioLoop(duration=video_clip.duration),
                ]
            )
            audio_clip = CompositeAudioClip([audio_clip, bgm_clip])
        except Exception as e:
            logger.error(f"failed to add bgm: {str(e)}")

    video_clip = video_clip.with_audio(audio_clip)
    video_clip.write_videofile(
        output_file,
        audio_codec=audio_codec,
        temp_audiofile_path=output_dir,
        threads=params.n_threads or 2,
        logger=None,
        fps=fps,
        bitrate=VideoQualityConfig.FINAL_BITRATE,  # 使用配置的最终文件码率
        preset=VideoQualityConfig.FINAL_PRESET,  # 使用配置的最终文件预设
        # 添加更多质量控制参数
        ffmpeg_params=[
            "-crf", VideoQualityConfig.FINAL_CRF,  # 使用配置的CRF值
            "-profile:v", "high",  # 使用高质量配置文件
            "-level", "4.1",  # 设置编码级别
            "-pix_fmt", "yuv420p",  # 确保兼容性
            "-movflags", "+faststart",  # 支持流式播放
        ]
    )
    video_clip.close()
    del video_clip


def preprocess_video(materials: List[MaterialInfo], clip_duration=4):
    for material in materials:
        if not material.url:
            continue

        ext = utils.parse_extension(material.url)
        try:
            clip = VideoFileClip(material.url)
        except Exception:
            clip = ImageClip(material.url)

        width = clip.size[0]
        height = clip.size[1]
        if width < 480 or height < 480:
            logger.warning(f"low resolution material: {width}x{height}, minimum 480x480 required")
            continue

        if ext in const.FILE_TYPE_IMAGES:
            logger.info(f"processing image: {material.url}")
            # Create an image clip and set its duration to 3 seconds
            clip = (
                ImageClip(material.url)
                .with_duration(clip_duration)
                .with_position("center")
            )
            # Apply a zoom effect using the resize method.
            # A lambda function is used to make the zoom effect dynamic over time.
            # The zoom effect starts from the original size and gradually scales up to 120%.
            # t represents the current time, and clip.duration is the total duration of the clip (3 seconds).
            # Note: 1 represents 100% size, so 1.2 represents 120% size.
            zoom_clip = clip.resized(
                lambda t: 1 + (clip_duration * 0.03) * (t / clip.duration)
            )

            # Optionally, create a composite video clip containing the zoomed clip.
            # This is useful when you want to add other elements to the video.
            final_clip = CompositeVideoClip([zoom_clip])

            # Output the video to a file.
            video_file = f"{material.url}.mp4"
            final_clip.write_videofile(video_file, fps=30, logger=None, bitrate=VideoQualityConfig.IMAGE_BITRATE, preset=VideoQualityConfig.IMAGE_PRESET)  # 使用配置的图片转视频质量
            close_clip(clip)
            material.url = video_file
            logger.success(f"image processed: {video_file}")
    return materials

# 一步到位的视频处理函数
def generate_video_directly(
    video_paths: List[str],
    audio_file: str,
    subtitle_path: str,
    output_file: str,
    params: VideoParams,
    video_aspect: VideoAspect = VideoAspect.portrait,
    video_concat_mode: VideoConcatMode = VideoConcatMode.random,
    video_transition_mode: VideoTransitionMode = None,
    max_clip_duration: int = 5,
    threads: int = 2,
) -> str:
    """
    一步到位生成最终视频，避免多次编码造成的质量损失
    
    Args:
        video_paths: 视频文件路径列表
        audio_file: 音频文件路径
        subtitle_path: 字幕文件路径
        output_file: 输出文件路径
        params: 视频参数
        video_aspect: 视频比例
        video_concat_mode: 视频拼接模式
        video_transition_mode: 视频转场模式
        max_clip_duration: 最大片段时长
        threads: 线程数
    
    Returns:
        生成的视频文件路径
    """
    logger.info("🚀 开始一步到位视频生成流程")
    
    # 1. 准备音频和字幕
    audio_clip = AudioFileClip(audio_file)
    audio_duration = audio_clip.duration
    
    # 调整音频音量
    audio_clip = audio_clip.with_effects([afx.MultiplyVolume(params.voice_volume)])
    
    # 2. 准备视频尺寸
    aspect = VideoAspect(video_aspect)
    video_width, video_height = aspect.to_resolution()
    
    # 3. 处理视频片段（内存中处理，不保存临时文件）
    logger.info("📹 直接处理视频片段（跳过临时文件）")
    processed_clips = []
    video_duration = 0
    
    # 准备子片段列表
    subclipped_items = []
    for video_path in video_paths:
        clip = VideoFileClip(video_path)
        clip_duration = clip.duration
        clip_w, clip_h = clip.size
        close_clip(clip)
        
        start_time = 0
        while start_time < clip_duration:
            end_time = min(start_time + max_clip_duration, clip_duration)
            if clip_duration - start_time >= max_clip_duration:
                subclipped_items.append(SubClippedVideoClip(
                    file_path=video_path, 
                    start_time=start_time, 
                    end_time=end_time, 
                    width=clip_w, 
                    height=clip_h
                ))
            start_time = end_time
            if video_concat_mode.value == VideoConcatMode.sequential.value:
                break
    
    # 随机排序
    if video_concat_mode.value == VideoConcatMode.random.value:
        random.shuffle(subclipped_items)
    
    # 4. 直接处理成最终可用的视频片段
    video_clips = []
    for i, subclipped_item in enumerate(subclipped_items):
        if video_duration > audio_duration:
            break
            
        logger.debug(f"直接处理片段 {i+1}: {subclipped_item.file_path}")
        
        try:
            # 加载和处理片段
            clip = VideoFileClip(subclipped_item.file_path).subclipped(
                subclipped_item.start_time, subclipped_item.end_time
            )
            
            # 调整尺寸
            if clip.size != (video_width, video_height):
                clip_ratio = clip.w / clip.h
                video_ratio = video_width / video_height
                
                if clip_ratio == video_ratio:
                    clip = clip.resized(new_size=(video_width, video_height))
                else:
                    if clip_ratio > video_ratio:
                        scale_factor = video_width / clip.w
                    else:
                        scale_factor = video_height / clip.h
                    
                    new_width = int(clip.w * scale_factor)
                    new_height = int(clip.h * scale_factor)
                    
                    background = ColorClip(size=(video_width, video_height), color=(0, 0, 0)).with_duration(clip.duration)
                    clip_resized = clip.resized(new_size=(new_width, new_height)).with_position("center")
                    clip = CompositeVideoClip([background, clip_resized])
            
            # 添加转场效果
            if video_transition_mode and video_transition_mode.value != VideoTransitionMode.none.value:
                shuffle_side = random.choice(["left", "right", "top", "bottom"])
                if video_transition_mode.value == VideoTransitionMode.fade_in.value:
                    clip = video_effects.fadein_transition(clip, 1)
                elif video_transition_mode.value == VideoTransitionMode.fade_out.value:
                    clip = video_effects.fadeout_transition(clip, 1)
                elif video_transition_mode.value == VideoTransitionMode.slide_in.value:
                    clip = video_effects.slidein_transition(clip, 1, shuffle_side)
                elif video_transition_mode.value == VideoTransitionMode.slide_out.value:
                    clip = video_effects.slideout_transition(clip, 1, shuffle_side)
                elif video_transition_mode.value == VideoTransitionMode.shuffle.value:
                    transition_funcs = [
                        lambda c: video_effects.fadein_transition(c, 1),
                        lambda c: video_effects.fadeout_transition(c, 1),
                        lambda c: video_effects.slidein_transition(c, 1, shuffle_side),
                        lambda c: video_effects.slideout_transition(c, 1, shuffle_side),
                    ]
                    shuffle_transition = random.choice(transition_funcs)
                    clip = shuffle_transition(clip)
            
            # 限制片段时长
            if clip.duration > max_clip_duration:
                clip = clip.subclipped(0, max_clip_duration)
            
            video_clips.append(clip)
            video_duration += clip.duration
            
        except Exception as e:
            logger.error(f"处理片段失败: {str(e)}")
            continue
    
    # 5. 如果视频时长不够，循环使用片段
    if video_duration < audio_duration:
        logger.info(f"视频时长不够，循环使用片段: {video_duration:.2f}s < {audio_duration:.2f}s")
        base_clips = video_clips.copy()
        import itertools
        for clip in itertools.cycle(base_clips):
            if video_duration >= audio_duration:
                break
            video_clips.append(clip)
            video_duration += clip.duration
    
    # 6. 合并所有视频片段
    logger.info("🎬 合并所有视频片段")
    if not video_clips:
        logger.error("没有可用的视频片段")
        return None
    
    # 合并视频
    if len(video_clips) == 1:
        video_clip = video_clips[0]
    else:
        video_clip = concatenate_videoclips(video_clips)
    
    # 7. 添加字幕
    if subtitle_path and os.path.exists(subtitle_path) and params.subtitle_enabled:
        logger.info("📝 添加字幕")
        
        # 准备字体路径
        font_path = ""
        if not params.font_name:
            params.font_name = "STHeitiMedium.ttc"
        font_path = os.path.join(utils.font_dir(), params.font_name)
        if os.name == "nt":
            font_path = font_path.replace("\\", "/")
        
        def create_text_clip(subtitle_item):
            params.font_size = int(params.font_size)
            params.stroke_width = int(params.stroke_width)
            phrase = subtitle_item[1]
            max_width = video_width * 0.9
            wrapped_txt, txt_height = wrap_text(
                phrase, max_width=max_width, font=font_path, fontsize=params.font_size
            )
            
            _clip = TextClip(
                text=wrapped_txt,
                font=font_path,
                font_size=params.font_size,
                color=params.text_fore_color,
                bg_color=params.text_background_color,
                stroke_color=params.stroke_color,
                stroke_width=params.stroke_width,
            )
            
            duration = subtitle_item[0][1] - subtitle_item[0][0]
            _clip = _clip.with_start(subtitle_item[0][0]).with_end(subtitle_item[0][1]).with_duration(duration)
            
            if params.subtitle_position == "bottom":
                _clip = _clip.with_position(("center", video_height * 0.95 - _clip.h))
            elif params.subtitle_position == "top":
                _clip = _clip.with_position(("center", video_height * 0.05))
            elif params.subtitle_position == "custom":
                margin = 10
                max_y = video_height - _clip.h - margin
                min_y = margin
                custom_y = (video_height - _clip.h) * (params.custom_position / 100)
                custom_y = max(min_y, min(custom_y, max_y))
                _clip = _clip.with_position(("center", custom_y))
            else:
                _clip = _clip.with_position(("center", "center"))
            
            return _clip
        
        def make_textclip(text):
            return TextClip(text=text, font=font_path, font_size=params.font_size)
        
        sub = SubtitlesClip(subtitles=subtitle_path, encoding="utf-8", make_textclip=make_textclip)
        text_clips = []
        for item in sub.subtitles:
            clip = create_text_clip(subtitle_item=item)
            text_clips.append(clip)
        
        video_clip = CompositeVideoClip([video_clip, *text_clips])
    
    # 8. 添加背景音乐
    final_audio = audio_clip
    bgm_file = get_bgm_file(bgm_type=params.bgm_type, bgm_file=params.bgm_file)
    if bgm_file:
        logger.info("🎵 添加背景音乐")
        try:
            bgm_clip = AudioFileClip(bgm_file).with_effects([
                afx.MultiplyVolume(params.bgm_volume),
                afx.AudioFadeOut(3),
                afx.AudioLoop(duration=video_clip.duration),
            ])
            final_audio = CompositeAudioClip([audio_clip, bgm_clip])
        except Exception as e:
            logger.error(f"添加背景音乐失败: {str(e)}")
    
    # 9. 合成最终视频
    video_clip = video_clip.with_audio(final_audio)
    
    # 10. 一次性输出最终视频（只编码一次！）
    logger.info("💾 一次性输出最终视频")
    output_dir = os.path.dirname(output_file)
    
    video_clip.write_videofile(
        output_file,
        audio_codec=audio_codec,
        temp_audiofile_path=output_dir,
        threads=threads,
        logger=None,
        fps=fps,
        bitrate=VideoQualityConfig.FINAL_BITRATE,
        preset=VideoQualityConfig.FINAL_PRESET,
        ffmpeg_params=[
            "-crf", VideoQualityConfig.FINAL_CRF,
            "-profile:v", "high",
            "-level", "4.1",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
        ]
    )
    
    # 11. 清理资源
    for clip in video_clips:
        close_clip(clip)
    close_clip(video_clip)
    close_clip(audio_clip)
    if 'bgm_clip' in locals():
        close_clip(bgm_clip)
    
    logger.success("✅ 一步到位视频生成完成")
    return output_file