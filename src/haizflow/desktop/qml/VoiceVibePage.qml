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
        title: qsTr("Chon cho de xuat file")
        fileMode: FileDialog.SaveFile
        nameFilters: ["MP3 (*.mp3)", "WAV (*.wav)"]
        onAccepted: root.voice.savePreview(selectedFile.toString().replace("file:///", ""))
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
            text: qsTr("Tab Text to Speech va Doi giong ngay trong app chinh: tao nghe thu, nghe thu trong app, nghe ok moi chon cho xuat file. Giong Edge chay ngay, giong local can goi tai nguyen HaizFlow hoac model da cai.")
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
                    title: qsTr("Text to Speech")
                }

                TextArea {
                    id: voiceText
                    Layout.fillWidth: true
                    Layout.preferredHeight: 140
                    placeholderText: qsTr("Nhap text can doc...")
                    wrapMode: TextArea.Wrap
                    enabled: root.voice && !root.voice.busy
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

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.space12
                    AppButton {
                        text: qsTr("Tao nghe thu")
                        enabled: root.voice && !root.voice.busy
                        onClicked: root.voice.generatePreview(voiceText.text, voiceCombo.currentText, rateCombo.currentText, "+0Hz", "+0%")
                    }
                    AppButton {
                        text: qsTr("Nghe thu trong app")
                        enabled: root.voice && root.voice.previewPath.length > 0
                        onClicked: player.play()
                    }
                    AppButton {
                        text: qsTr("Nghe ok roi, chon cho xuat file")
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
                    title: qsTr("Doi giong (can model da cai)")
                }

                Text {
                    Layout.fillWidth: true
                    text: qsTr("Seed-VC: dat code vao models/seed-vc. RVC: dat file .pth vao models/rvc-v2. Chua cai thi app se bao ro, khong tao file gia.")
                    color: Theme.textMuted
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.control
                    wrapMode: Text.WordWrap
                }

                AppTextField {
                    id: sourceField
                    Layout.fillWidth: true
                    placeholderText: qsTr("Duong dan file goc (wav/mp3)")
                }
                AppTextField {
                    id: referenceField
                    Layout.fillWidth: true
                    placeholderText: qsTr("Duong dan file giong mau (wav, 1-30 giay, sach)")
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
                        text: qsTr("Doi giong nghe thu")
                        enabled: root.voice && !root.voice.busy
                        onClicked: root.voice.convertPreview(sourceField.text, referenceField.text, vcModelCombo.currentText, vcModeCombo.currentText, false)
                    }
                }
            }
        }
    }
}
