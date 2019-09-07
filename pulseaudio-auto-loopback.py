#!/usr/bin/python3

from gi.repository import GLib
import dbus
import dbus.mainloop.glib
import os
from subprocess import call
import time


# apt install projectm-pulseaudio 
# (out of date, just build it from https://github.com/projectM-visualizer/projectm)
# wget https://github.com/projectM-visualizer/projectm/releases/download/v3.1.0/projectM-3.1.0.tar.gz
# tar xf projectM-3.1.0.tar.gz
# cd projectM-3.1.0
# ./configure --enable-SDL

USE_PROJECTM = os.system('which projectM-pulseaudio > /dev/null') == 0
# pactl list sinks | grep Name
SINK = 'alsa_output.pci-0000_01_00.1.hdmi-surround'

def property_changed(iface_name, changed_props, invalid_props, path=None, interface=None):
    if path is None or "org.bluez.Device" not in iface_name:
        return

    for prop in changed_props:
        if prop == "Connected":
            bt_addr = "_".join(path.split('/')[-1].split('_')[1:])
            if changed_props[prop] == True:
                # This was happening too quickly
                time.sleep(7)
                cmd = "pactl load-module module-loopback source=bluez_source.{} sink={} > /dev/null 2>&1".format(bt_addr, SINK)
                retcode = call(cmd, shell=True)
                if retcode == 0:
                    print("Added bluetooth audio source: {0}".format(bt_addr))
                else:
                    print("Error adding device: {} ({})".format(bt_addr,retcode))
                if USE_PROJECTM:
                    os.system('/bin/bash -c "killall -9 projectM-pulseaudio; (projectM-pulseaudio 1>/dev/null 2>&1 &)"')
                    os.system('xdotool key Escape')
                    # If you are using a projectM version < 3.1, change %1 to %4
                    os.system('sleep 8; xdotool search --sync --name projectM key --window %1 f') 
            else:
                cmd = "for i in $(pactl list short modules | grep module-loopback | grep source=bluez_source.{} | cut -f 1); do pactl unload-module $i; done".format(bt_addr)
                retcode = call(cmd, shell=True)
                if retcode == 0:
                    print("Removed bluetooth audio source: {0}".format(bt_addr))
                else:
                    print("Error removing device: {} ({})".format(bt_addr,retcode))
                if USE_PROJECTM:
                    os.system('killall -9 projectM-pulseaudio')
    return
    

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    bus.add_signal_receiver(property_changed, bus_name="org.bluez", signal_name="PropertiesChanged", path_keyword="path", interface_keyword="interface")

    mainloop = GLib.MainLoop()
    mainloop.run()
