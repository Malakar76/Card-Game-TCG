[app]

title = Card Game TCG
package.name = cardgametcg
package.domain = org.cardgametcg

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,java
source.include_patterns = main.py,src/**/*.py,src/**/*.kv
source.exclude_dirs = tests,.venv,.git,.github,.ruff_cache,.pytest_cache,db/migrations,build,dist
source.exclude_patterns = buildozer.spec,pyproject.toml,alembic.ini,*.egg-info

version = 0.2.2

requirements = python3,kivy==2.3.0,sqlalchemy==2.0.36,pydantic==2.12.5,pydantic-settings,pydantic-core==2.41.5,annotated-types,typing-extensions,typing-inspection,python-dotenv,tcgdex-sdk,dacite,camera4kivy,gestures4kivy

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

# Local recipes override broken p4a sqlalchemy recipe (404 on PyPI URL for 2.x)
p4a.local_recipes = %(source.dir)s/p4a-recipes

# CameraX provider hook for camera4kivy on Android
p4a.hook = camerax_provider/gradle_options.py

android.permissions = INTERNET,CAMERA,READ_MEDIA_IMAGES,READ_EXTERNAL_STORAGE

android.enable_androidx = True
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.1,com.google.android.gms:play-services-tasks:18.0.2
android.gradle_repositories = mavenCentral(), maven { url 'https://maven.google.com' }

# Release signing (keystore decoded in CI, or placed locally for release builds)
android.keystore = ./release.keystore
android.keyalias = cardgametcg
android.release_artifact = apk

[buildozer]

log_level = 2
warn_on_root = 1
