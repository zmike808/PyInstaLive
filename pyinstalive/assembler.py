import os
import shutil
import re
import glob
import subprocess
import json
import sys

from moviepy.video.io.VideoFileClip import VideoFileClip

try:
    import pil
    import logger
    import helpers
except ImportError:
    from . import pil
    from . import logger
    from . import helpers

"""
The content of this file was originally written by https://github.com/taengstagram
The code has been edited for use in PyInstaLive.
"""


def _get_file_index(filename):
    """ Extract the numbered index in filename for sorting """
    mobj = re.match(r'.+\-(?P<idx>[0-9]+)\.[a-z]+', filename)
    if mobj:
        return int(mobj.group('idx'))
    return -1


def assemble():
    ass_json_file = pil.assemble_arg
    ass_mp4_file = os.path.join(pil.dl_path, os.path.basename(ass_json_file).replace("_downloads.json", ".mp4"))
    ass_segment_dir = pil.assemble_arg.split('.')[0]

    if not os.path.isfile(ass_json_file):
        logger.error('Broadcast json file does not exist: %s' % ass_json_file)
        logger.separator()
        sys.exit(1)
    if not os.path.exists(ass_segment_dir):
        logger.error('Segment directory does not exist: %s' % ass_segment_dir)
        if os.path.isfile(ass_json_file):
            logger.error("The segment directory must have the same name as the json file.")
        logger.separator()
        sys.exit(1)

    logger.info("Assembling video files from json file: {:s}".format(os.path.basename(pil.assemble_arg)))

    with open(ass_json_file) as info_file:
        broadcast_info = json.load(info_file)

    if broadcast_info.get('broadcast_status', '') == 'post_live':
        logger.error('Segments from replay downloads cannot be assembled.')
        sys.exit(1)

    stream_id = str(broadcast_info['id'])

    post_v034 = False
    segment_meta = broadcast_info.get('segments', {})
    if segment_meta:
        post_v034 = True
        all_segments = [
            os.path.join(ass_segment_dir, k)
            for k in broadcast_info['segments'].keys()]
    else:
        all_segments = list(filter(
            os.path.isfile,
            glob.glob(os.path.join(ass_segment_dir, '%s-*.m4v' % stream_id))))

    all_segments = sorted(all_segments, key=lambda x: _get_file_index(x))
    prev_res = ''
    sources = []
    audio_stream_format = 'assembled_source_{0}_{1}_mp4.tmp'
    video_stream_format = 'assembled_source_{0}_{1}_m4a.tmp'
    video_stream = ''
    audio_stream = ''

    pre_v034 = os.path.isfile(os.path.join(ass_segment_dir, '%s-init.m4v' % stream_id))

    for segment in all_segments:

        if not os.path.isfile(segment.replace('.m4v', '.m4a')):
            logger.warning('Audio segment not found: {0!s}'.format(segment.replace('.m4v', '.m4a')))
            continue

        if segment.endswith('-init.m4v'):
            logger.info('Replacing %s' % segment)
            segment = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), 'repair', 'init.m4v')

        if segment.endswith('-0.m4v') and not pre_v034:
            # From >= v0.3.4 onwards, the init segment is prepended to the m4v
            # so instead of patching the init bytes, we just skip the -0.m4v
            # since it's most likely the faulty one
            logger.info('Dropped %s' % segment)
            continue

        video_stream = os.path.join(
            ass_segment_dir, video_stream_format.format(stream_id, len(sources)))
        audio_stream = os.path.join(
            ass_segment_dir, audio_stream_format.format(stream_id, len(sources)))

        try:
            if pre_v034:
                # Don't try to probe with moviepy
                # Just do appending
                file_mode = 'ab'
            else:
                if not post_v034:
                    # no segments meta info
                    vidclip = VideoFileClip(segment)
                    vid_width, vid_height = vidclip.size
                    curr_res = '%sx%s' % (vid_width, vid_height)
                    if prev_res and prev_res != curr_res:
                        sources.append({'video': video_stream, 'audio': audio_stream})
                        video_stream = os.path.join(
                            ass_segment_dir, video_stream_format.format(stream_id, len(sources)))
                        audio_stream = os.path.join(
                            ass_segment_dir, audio_stream_format.format(stream_id, len(sources)))

                    # Fresh init segment
                    file_mode = 'wb'
                    prev_res = curr_res
                else:
                    # Use segments meta info
                    if prev_res and prev_res != segment_meta[os.path.basename(segment)]:
                        # resolution changed detected
                        sources.append({'video': video_stream, 'audio': audio_stream})
                        video_stream = os.path.join(
                            ass_segment_dir, video_stream_format.format(stream_id, len(sources)))
                        audio_stream = os.path.join(
                            ass_segment_dir, audio_stream_format.format(stream_id, len(sources)))
                        file_mode = 'wb'
                    else:
                        file_mode = 'ab'

                    prev_res = segment_meta[os.path.basename(segment)]

        except IOError:
            # Not a fresh init segment
            file_mode = 'ab'

        with open(video_stream, file_mode) as outfile,\
                open(segment, 'rb') as readfile:
            shutil.copyfileobj(readfile, outfile)
            # logger.info(
            #     'Assembling video stream {0!s} => {1!s}'.format(
            #         os.path.basename(segment), os.path.basename(video_stream)))

        with open(audio_stream, file_mode) as outfile,\
                open(segment.replace('.m4v', '.m4a'), 'rb') as readfile:
            shutil.copyfileobj(readfile, outfile)
            # logger.info(
            #     'Assembling audio stream {0!s} => {1!s}'.format(
            #         os.path.basename(segment), os.path.basename(audio_stream)))

    if audio_stream and video_stream:
        sources.append({'video': video_stream, 'audio': audio_stream})

    for n, source in enumerate(sources):
        ffmpeg_binary = os.getenv('FFMPEG_BINARY', 'ffmpeg')
        cmd = [
            ffmpeg_binary, '-loglevel', 'warning', '-y',
            '-i', source['audio'],
            '-i', source['video'],
            '-c:v', 'copy', '-c:a', 'copy', ass_mp4_file]
        fnull = open(os.devnull, 'w')
        exit_code = subprocess.call(cmd, stdout=fnull, stderr=subprocess.STDOUT)
        logger.warn("FFmpeg exit code not '0' but '{:d}'.".format(exit_code))
        logger.separator()
        logger.info('The video file has been generated: %s' % os.path.basename(ass_mp4_file))
        logger.separator()
