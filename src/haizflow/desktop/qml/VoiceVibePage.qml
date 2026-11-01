pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Dialogs
import QtQuick.Layouts
import QtMultimedia
import "."

Item {
    id: root

    // qmllint disable stale-property-read
    readonly property var voice: AppController.voiceVibe
    // qmllint enable stale-property-read

    MediaPlayer {
        id: player
        audioOutput: AudioOutput {}
        source: root.voice ? root.voice.previewPath : ""
    }

    FileDialog {
        id: saveDialog
        title: qsTr("Chọn chỗ để xuất file")
        fileMode: FileDialog.SaveFile
        nameFilters: ["MP3 (*.mp3)", "WAV (*.wav)"]
        onAccepted: root.voice.savePreview(selectedFile.toString().replace("file:///", ""))
    }

    FileDialog {
        id: sourceDialog
        title: qsTr("Chọn file gốc cần đổi giọng")
        fileMode: FileDialog.OpenFile
        nameFilters: ["Âm thanh (*.wav *.mp3)"]
        onAccepted: sourceField.text = selectedFile.toString().replace("file:///", "")
    }

    FileDialog {
        id: referenceDialog
        title: qsTr("Chọn file giọng mẫu")
        fileMode: FileDialog.OpenFile
        nameFilters: ["Âm thanh (*.wav *.mp3)"]
        onAccepted: referenceField.text = selectedFile.toString().replace("file:///", "")
    }

    function label(text) {
        return text
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: UiMetrics.pageMargin
        spacing: Theme.space16

        PageHeader {
            Layout.fillWidth: true
            title: qsTr("VoiceVibe")
        }

        Text {
            Layout.fillWidth: true
            Layout.maximumWidth: 1120
            Layout.alignment: Qt.AlignHCenter
            text: qsTr("Tab chuyển văn bản thành giọng nói và đổi giọng ngay trong app chính. Làm theo 3 bước: 1) Nhập văn bản, 2) Bấm Tạo nghe thử, 3) Nghe thử trong app, nghe ưng rồi mới chọn chỗ xuất file.")
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
                    title: qsTr("Bước 1 — Nhập văn bản cần đọc")
                }

                TextArea {
                    id: voiceText
                    Layout.fillWidth: true
                    Layout.preferredHeight: 140
                    placeholderText: qsTr("Ví dụ: Xin chào, đây là bản nghe thử giọng đọc...")
                    wrapMode: TextArea.Wrap
                    enabled: root.voice && !root.voice.busy
                }

                Text {
                    Layout.fillWidth: true
                    text: qsTr("Bước 2 — Chọn giọng đọc")
                    color: Theme.text
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.control
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.space12
                    ComboBox {
                        id: voiceCombo
                        Layout.fillWidth: true
                        model: ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural", "en-US-JennyNeural", "en-US-GuyNeural", "zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"]
                    }
                    ComboBox {
                        id: rateCombo
                        model: ["-20%", "-10%", "+0%", "+10%", "+20%", "+30%"]
                        currentIndex: 2
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: qsTr("Bước 3 — Nghe thử rồi mới xuất file")
                    color: Theme.text
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.control
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.space12
                    AppButton {
                        text: qsTr("Tạo nghe thử")
                        enabled: root.voice && !root.voice.busy && voiceText.text.length > 0
                        onClicked: root.voice.generatePreview(voiceText.text, voiceCombo.currentText, rateCombo.currentText, "+0Hz", "+0%")
                    }
                    AppButton {
                        text: qsTr("Nghe thử trong app")
                        enabled: root.voice && root.voice.previewPath.length > 0
                        onClicked: player.play()
                    }
                    AppButton {
                        text: qsTr("Nghe ưng rồi, chọn chỗ xuất file")
                        enabled: root.voice && root.voice.previewPath.length > 0
                        onClicked: saveDialog.open()
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: root.voice ? root.voice.status : ""
                    color: Theme.textMuted
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.control
                    wrapMode: Text.WordWrap
                }

                SectionHeader {
                    Layout.fillWidth: true
                    title: qsTr("Đổi giọng (cần cài model trước)")
                }

                Text {
                    Layout.fillWidth: true
                    text: qsTr("Bấm nút Chọn file thay vì gõ đường dẫn tay. Seed-VC: đặt code vào models/seed-vc. RVC: đặt file .pth vào models/rvc-v2. Chưa cài thì app sẽ báo rõ, không tạo file giả.")
                    color: Theme.textMuted
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.control
                    wrapMode: Text.WordWrap
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.space12
                    AppTextField {
                        id: sourceField
                        Layout.fillWidth: true
                        placeholderText: qsTr("File gốc cần đổi giọng")
                    }
                    AppButton {
                        text: qsTr("Chọn file gốc")
                        onClicked: sourceDialog.open()
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.space12
                    AppTextField {
                        id: referenceField
                        Layout.fillWidth: true
                        placeholderText: qsTr("File giọng mẫu (1–30 giây, sạch, không nhạc)")
                    }
                    AppButton {
                        text: qsTr("Chọn giọng mẫu")
                        onClicked: referenceDialog.open()
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.space12
                    ComboBox {
                        id: vcModelCombo
                        model: ["seed-vc", "rvc-v2", "openvoice-v2"]
                    }
                    ComboBox {
                        id: vcModeCombo
                        model: ["light", "balanced", "quality"]
                    }
                    AppButton {
                        text: qsTr("Đổi giọng nghe thử")
                        enabled: root.voice && !root.voice.busy
                        onClicked: root.voice.convertPreview(sourceField.text, referenceField.text, vcModelCombo.currentText, vcModeCombo.currentText, false)
                    }
                }
            }
        }
    }
}
