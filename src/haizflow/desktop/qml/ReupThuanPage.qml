pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import "."

Item {
    id: root

    // qmllint disable stale-property-read
    readonly property var reup: AppController.reupThuan
    readonly property var downloader: AppController.mediaDownloader
    // qmllint enable stale-property-read

    Connections {
        target: root.downloader
        function onChanged() { root.reup.advance() }
    }
    Connections {
        target: AppController
        function onSocialPublishStateChanged() { root.reup.advance() }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: UiMetrics.pageMargin
        spacing: Theme.space16

        PageHeader {
            Layout.fillWidth: true
            title: qsTr("Reup Thuần")

            ProjectHeaderActions {
                projectFolderText: qsTr("Mở thư mục dự án")
                deleteEnabled: !root.reup.busy
                onProjectFolderRequested: AppController.openProjectFolder()
                onDeleteRequested: AppController.deleteCurrentProject()
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.maximumWidth: 1120
            Layout.alignment: Qt.AlignHCenter
            text: qsTr("Dán link, app tự tải video nguyên gốc rồi đăng nguyên gốc lên luôn. Không dịch, không lồng tiếng, không làm phụ đề.")
            color: Theme.textMuted
            font.family: Theme.fontFamily
            font.pixelSize: TypeScale.control
            wrapMode: Text.WordWrap
            textFormat: Text.PlainText
        }

        AppSurface {
            Layout.fillWidth: true
            Layout.maximumWidth: 1120
            Layout.alignment: Qt.AlignHCenter
            padding: Theme.space16

            ColumnLayout {
                width: parent.width - Theme.space16 * 2
                spacing: Theme.space12

                SectionHeader {
                    Layout.fillWidth: true
                    title: qsTr("Liên kết video")
                }

                AppTextField {
                    id: videoLink
                    Layout.fillWidth: true
                    placeholderText: qsTr("Dán liên kết video")
                    selectByMouse: true
                    accessibleName: qsTr("Liên kết video")
                    enabled: !root.reup.busy
                }

                SectionHeader {
                    Layout.fillWidth: true
                    title: qsTr("Nội dung đăng (tùy chọn)")
                }

                AppTextField {
                    id: captionField
                    Layout.fillWidth: true
                    placeholderText: AppController.tiktokDefaultCaption.length > 0 ? AppController.tiktokDefaultCaption : qsTr("Caption")
                    selectByMouse: true
                    enabled: !root.reup.busy
                }

                AppTextField {
                    id: hashtagField
                    Layout.fillWidth: true
                    placeholderText: AppController.tiktokDefaultHashtags.length > 0 ? AppController.tiktokDefaultHashtags : qsTr("Hashtag")
                    selectByMouse: true
                    enabled: !root.reup.busy
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.space12

                    StudioButton {
                        text: root.reup.busy ? qsTr("Đang chạy…") : qsTr("Tải rồi đăng")
                        variant: "primary"
                        enabled: !root.reup.busy && videoLink.text.trim().length > 0
                        onClicked: root.reup.start(videoLink.text.trim(), captionField.text, hashtagField.text)
                    }

                    StudioButton {
                        text: qsTr("Hủy")
                        variant: "danger"
                        visible: root.reup.busy
                        onClicked: root.reup.cancel()
                    }

                    StudioButton {
                        text: qsTr("Làm lại")
                        variant: "secondary"
                        visible: root.reup.phase === "done" || root.reup.phase === "error"
                        onClicked: { root.reup.reset(); videoLink.clear() }
                    }

                    Item { Layout.fillWidth: true }
                }
            }
        }

        AppSurface {
            Layout.fillWidth: true
            Layout.maximumWidth: 1120
            Layout.alignment: Qt.AlignHCenter
            padding: Theme.space16

            ColumnLayout {
                width: parent.width - Theme.space16 * 2
                spacing: Theme.space8

                Text {
                    Layout.fillWidth: true
                    text: qsTr("Trạng thái")
                    color: Theme.text
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.control
                    font.weight: Font.DemiBold
                    textFormat: Text.PlainText
                }

                Text {
                    Layout.fillWidth: true
                    text: root.reup.status.length > 0 ? root.reup.status : (root.downloader.status.length > 0 ? root.downloader.status : qsTr("Chưa chạy."))
                    color: root.reup.phase === "error" ? Theme.danger : Theme.textMuted
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.label
                    wrapMode: Text.WordWrap
                    textFormat: Text.PlainText
                }

                Text {
                    Layout.fillWidth: true
                    visible: root.downloader.progress > 0 && root.reup.phase === "downloading"
                    text: qsTr("Tải: %1%").arg(root.downloader.progress)
                    color: Theme.textMuted
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.label
                    textFormat: Text.PlainText
                }

                Text {
                    Layout.fillWidth: true
                    visible: root.reup.downloadedPath.length > 0
                    text: root.reup.downloadedPath
                    color: Theme.textMuted
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.label
                    wrapMode: Text.WordWrap
                    elide: Text.ElideMiddle
                    textFormat: Text.PlainText
                }

                Text {
                    Layout.fillWidth: true
                    visible: AppController.tiktokWaitingCount > 0 || AppController.tiktokPostedCount > 0
                    text: qsTr("Chờ đăng: %1 · Đã đăng: %2").arg(AppController.tiktokWaitingCount).arg(AppController.tiktokPostedCount)
                    color: Theme.textMuted
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.label
                    textFormat: Text.PlainText
                }
            }
        }

        Text {
            Layout.fillWidth: true
            Layout.maximumWidth: 1120
            Layout.alignment: Qt.AlignHCenter
            text: qsTr("Lưu ý: bài đăng là công khai và khó thu hồi. Hãy chắc tài khoản, caption và video đã đúng trước khi bấm Tải rồi đăng.")
            color: Theme.textMuted
            font.family: Theme.fontFamily
            font.pixelSize: TypeScale.label
            wrapMode: Text.WordWrap
            textFormat: Text.PlainText
        }
    }
}
