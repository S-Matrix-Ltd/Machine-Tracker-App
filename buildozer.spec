[app]
title = Machine Tracker
package.name = machinetracker
package.domain = org.smatrix
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
version = 1.0
requirements = hostpython3==3.11.9,python3==3.11.9,kivy==2.3.0,pyjnius,setuptools
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True
android.api = 33
android.minapi = 21
android.ndk = 25b
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
