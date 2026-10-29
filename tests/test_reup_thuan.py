"""Reup Thuần: a single reup project attaches both download and publish.

These checks are intentionally text-level, like test_qml_menu.py, so they
run without a Qt runtime: they pin the wiring that makes one link flow
from download to publish without any translation/dubbing/subtitle step.
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QML_DIR = ROOT / "src" / "haizflow" / "desktop" / "qml"


class ReupThuanWiringTests(unittest.TestCase):
    def test_reup_is_a_project_type(self):
        store = (ROOT / "src" / "haizflow" / "services" / "project_store.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"reup"', store)
        self.assertIn('{"download", "reup"}', store)
        self.assertIn('{"publish", "reup"}', store)

    def test_reup_page_and_routes_are_exposed(self):
        main = (QML_DIR / "Main.qml").read_text(encoding="utf-8")
        route_host = (QML_DIR / "RouteHost.qml").read_text(encoding="utf-8")
        nav = (QML_DIR / "NavigationRail.qml").read_text(encoding="utf-8")
        page = (QML_DIR / "ReupThuanPage.qml").read_text(encoding="utf-8")
        self.assertIn('routeReupProjects: "reup-projects"', main)
        self.assertIn('routeReupWorkspace: "reup-workspace"', main)
        self.assertIn('AppController.reupProjectModel', route_host)
        self.assertIn('root.newProjectRequested("reup", "reup-projects")', route_host)
        self.assertIn('ReupThuanPage', route_host)
        self.assertIn('key: "reup"', nav)
        self.assertIn('AppController.reupThuan', page)
        self.assertIn('root.reup.start(', page)

    def test_reup_controller_orchestrates_without_processing(self):
        controller = (
            ROOT / "src" / "haizflow" / "desktop" / "reup_thuan_controller.py"
        ).read_text(encoding="utf-8")
        self.assertIn("downloadVideo", controller)
        self.assertIn("add_videos", controller)
        self.assertIn("publish_next", controller)
        # Pure reup: no processing pipeline is invoked from this controller.
        self.assertNotIn("translate_segments", controller)
        self.assertNotIn("process_video", controller)
        self.assertNotIn("start_video", controller)


if __name__ == "__main__":
    unittest.main()
