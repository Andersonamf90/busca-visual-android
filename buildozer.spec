[app]
title = Busca Visual
package.name = buscavisual
package.domain = br.com.projeto
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,webp,sqlite3,md
version = 0.1.0
requirements = python3,kivy,requests,beautifulsoup4,pillow
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
