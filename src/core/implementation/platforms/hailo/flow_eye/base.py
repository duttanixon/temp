import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib, GObject
from dataclasses import dataclass

@dataclass
class GstContext:
    gst: Gst
    glib: GLib
    gobject: GObject

    @classmethod
    def initialize(cls) -> 'GstContext':
        """Initialize GStreamer and create context"""
        Gst.init(None)
        return cls(Gst, GLib, GObject)