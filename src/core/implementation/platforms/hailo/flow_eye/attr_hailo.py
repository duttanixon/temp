from gsthailo import VideoFrame
from gi.repository import Gst
def run(video_frame: VideoFrame):
    return Gst.FlowReturn.OK

