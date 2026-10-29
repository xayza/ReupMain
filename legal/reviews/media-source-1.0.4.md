# HaizFlow 1.0.4 — scoped technical packaging review

Reviewer: Codex. Date: 2026-10-25 (Asia/Saigon). This is a scoped technical
packaging review, not independent legal, ownership or patent certification.

The owner directly requested building and publishing 1.0.4 with updates from
1.0.1. Preserve earlier releases and immutable assets; also provide direct
updates from 1.0.2 and 1.0.3. Reviewed application baseline is f9a4a7e plus
the Douyin media transport fix and release preparation in 2541f77. Final clean
release commit and actual packaged files are bound by BUILD-INFO and hashes.

Changes since 1.0.3 concern application-owned subtitle editing/voice identity,
preview cache identity, project deletion transactions, bounded TTS inactivity
watchdogs and short-audio checks, Douyin request-level transport selection,
and bounded parallel Core verification, Gemini guidance/style/source ownership,
Han subtitle language preflight and focused field synchronization. Security
updates are Pillow 13.0.0, certifi 2026.10.19, setuptools 84.1.0, filelock 4.2.1
and the coupled OpenTelemetry 1.45.1 / semantic-conventions 0.66b1 family.
Its upstream dependency graph adds Apache-2.0 OpenTelemetry exporter common
and HTTP transport packages 0.66b1, not a new application provider or service.
Regenerated hash locks preserve packages outside these dependency families.
The Edge TTS archive URL now uses GitHub's extension-bearing archive endpoint;
the full commit and downloaded SHA-256 remain identical to the reviewed source.
No checkpoint, voice preview, font, artwork, FFmpeg/Qt build or media recipe changes.

Installed wheel license texts retain Pillow's MIT-CMU plus bundled component
notices, certifi's MPL-2.0 certificate bundle, setuptools/filelock MIT and
OpenTelemetry Apache-2.0. Copy complete installed wheel license inventories,
including Pillow's bundled FreeType and image library notices, into every
affected artifact. Existing corresponding-source closures apply to unchanged
FFmpeg/Qt components, not a claim that those sources describe Pillow's new DLLs.

Existing application-scope, owner-asset/OmniVoice noncommercial and Qt
replacement clearances retain all limitations. The pinned ThirdPartySources
1.0.0 archive continues to provide the unchanged FFmpeg CLI/engine, Qt/PySide,
compiler, recipes and library source closures at its original public URL.
Keep all required notices and source access. Do not redistribute user media,
projects, cookies, API keys or private diagnostic audio.

Rebuild CPU 17, CUDA 19 and vision 9 so worker fixes and security updates reach
users. Pin only actual archive bytes, sizes and SHA-256
at new immutable 1.0.4 URLs. Engine protocol 1, runtime contract 7, model
formats and update protocol remain compatible. Rebuild bootstrap and Core
from the same final clean commit; old launchers are not silently replaced by
Core-only updates. Explain the Setup path for the launcher optimization.

Require strict legal/resource/dependency audits, complete source/QML tests,
real frozen CPU/CUDA smoke, packaged Douyin transport validation, installer
acceptance, actual frozen Full/Delta health/rollback/data-preservation tests
from 1.0.1 onward, and public release asset digest/download checks. These are
publication conditions, not assertions of completed tests at review time.
Local acceptance is not an all-machine benchmark or Windows certification.
The owner-selected unsigned distribution caveat and OmniVoice noncommercial
restriction remain visible; no gate, license restriction or blocker is waived.
