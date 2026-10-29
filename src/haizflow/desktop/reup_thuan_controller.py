"""Reup Thuần: one link in, original video downloaded, then posted as-is.

This controller does not duplicate downloading or posting. It only
orchestrates the two existing controllers in sequence inside a single
``reup`` project, where both controllers are attached at the same time:

1. ``MediaDownloadController.downloadVideo`` downloads the link.
2. When the downloader reports ``Saved to <path>``, the finished file is
   added to the publishing queue with
   ``SocialPublishController.add_videos``.
3. Once the import finishes, the queued item is published with
   ``SocialPublishController.publish_next``.

No translation, dubbing or subtitle processing runs in this flow: that
is what makes it "thuần" (pure reup). Starting a run is the user's
explicit consent to post that one downloaded video, so the controller
marks consent for this run only; it never turns on auto-posting for
videos imported later through the normal publishing page.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Property, QObject, Signal, Slot


class ReupThuanController(QObject):
    changed = Signal()

    def __init__(self, host, parent=None):
        super().__init__(parent)
        self._host = host
        self._phase = "idle"  # idle | downloading | importing | publishing | done | error
        self._status = ""
        self._url = ""
        self._caption = ""
        self._hashtags = ""
        self._downloaded_path = ""
        self._import_seen_busy = False
        self._publish_started = False
        self._posted_before = 0

    # -- QML properties -------------------------------------------------
    @Property(str, notify=changed)
    def phase(self):
        return self._phase

    @Property(str, notify=changed)
    def status(self):
        return self._status

    @Property(bool, notify=changed)
    def busy(self):
        return self._phase in {"downloading", "importing", "publishing"}

    @Property(str, notify=changed)
    def downloadedPath(self):
        return self._downloaded_path

    def _set(self, phase=None, status=None):
        if phase is not None:
            self._phase = phase
        if status is not None:
            self._status = status
        self.changed.emit()

    def _fail(self, message):
        self._set("error", message)

    # -- entry points called from QML -----------------------------------
    @Slot(str, str, str)
    def start(self, url, caption="", hashtags=""):
        host = self._host
        downloader = getattr(host, "_media_downloader", None)
        publisher = getattr(host, "_tiktok_publisher", None)
        if self.busy:
            return
        url = str(url or "").strip()
        if not url:
            self._fail("Dán liên kết video trước.")
            return
        if getattr(host, "_project_type", "") != "reup":
            self._fail("Mở một dự án Reup Thuần trước.")
            return
        if downloader is None or not downloader.videoOutputDirectory:
            self._fail("Dự án Reup Thuần chưa có thư mục tải xuống.")
            return
        if publisher is None or not publisher.api_key_configured:
            self._fail("Chưa có API key Zernio. Kết nối tài khoản đăng bài trước.")
            return
        if not publisher.account_ready:
            self._fail("Chưa chọn tài khoản đăng bài. Kết nối và chọn tài khoản trước.")
            return
        self._url = url
        self._caption = str(caption or "")
        self._hashtags = str(hashtags or "")
        self._downloaded_path = ""
        self._import_seen_busy = False
        self._publish_started = False
        self._posted_before = int(publisher.posted_count or 0)
        # Apply this run's caption/hashtags as the publishing defaults so
        # add_videos() picks them up for the imported item.
        try:
            publisher.save_defaults(self._caption, self._hashtags, False)
        except Exception:
            pass
        self._set("downloading", "Đang tải video…")
        downloader.downloadVideo(url)

    @Slot()
    def cancel(self):
        host = self._host
        downloader = getattr(host, "_media_downloader", None)
        publisher = getattr(host, "_tiktok_publisher", None)
        if downloader is not None:
            try:
                downloader.cancel()
            except Exception:
                pass
        if publisher is not None:
            try:
                publisher.cancel()
            except Exception:
                pass
        if self.busy:
            self._set("idle", "Đã hủy.")

    @Slot()
    def reset(self):
        if not self.busy:
            self._set("idle", "")

    # -- state machine, driven from QML Connections ---------------------
    # QML calls advance() whenever the downloader or the publisher changes.
    # Polling-free: both controllers already emit changed signals.
    @Slot()
    def advance(self):
        if self._phase not in {"downloading", "importing", "publishing"}:
            return
        host = self._host
        downloader = getattr(host, "_media_downloader", None)
        publisher = getattr(host, "_tiktok_publisher", None)
        if downloader is None or publisher is None:
            return

        if self._phase == "downloading":
            state = str(getattr(downloader, "state", "") or "")
            status = str(getattr(downloader, "status", "") or "")
            if state == "error":
                self._fail(status or "Tải video thất bại.")
                return
            if state == "done" and status.startswith("Saved to "):
                path = status[len("Saved to "):].strip()
                if not path or not os.path.isfile(path):
                    self._fail("Tải xong nhưng không tìm thấy file video.")
                    return
                self._downloaded_path = path
                self._set("importing", "Tải xong, đang đưa vào hàng chờ đăng…")
                if not publisher.add_videos([path]):
                    self._fail(publisher.status or "Không đưa được video vào hàng chờ đăng.")
                    return
                return
            if state in {"running", "queued"} or status:
                self._set("downloading", status or "Đang tải video…")
            return

        if self._phase == "importing":
            if publisher.import_busy:
                self._import_seen_busy = True
                return
            if not self._import_seen_busy:
                # Import is asynchronous; wait until it has actually started
                # before deciding it is finished, otherwise a fast check
                # right after add_videos() would skip straight to publish
                # with an empty queue.
                return
            if publisher.waiting_count <= 0:
                self._fail(publisher.status or "Không có video nào chờ đăng.")
                return
            self._set("publishing", "Đang đăng video…")
            # Explicit consent for this one run only.
            publisher.set_consent_confirmed(True)
            self._publish_started = True
            if not publisher.publish_next():
                self._fail(publisher.status or "Không đăng được video.")
            return

        if self._phase == "publishing":
            if publisher.busy:
                return
            if int(publisher.posted_count or 0) > self._posted_before:
                self._set("done", "Đã đăng xong.")
                return
            if publisher.waiting_count > 0:
                # Publish failed or was cancelled; surface the publisher's
                # own status instead of silently marking it done.
                self._fail(publisher.status or "Đăng video thất bại.")
                return
            if self._publish_started:
                self._set("done", "Đã đăng xong.")
