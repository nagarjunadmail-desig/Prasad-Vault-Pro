[app]
title = Prasad Vault Pro
package.name = prasad_vault
package.domain = org.prasad
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 3.5
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,android,pyjnius
orientation = portrait
fullscreen = 1
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MODIFY_AUDIO_SETTINGS, MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.skip_update = False
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
