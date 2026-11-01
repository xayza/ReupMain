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
        // previewPath la duong dan Windows thuan (C:\...), phai doi sang file:// URL
        // thi MediaPlayer moi mo duoc. Neu de nguyen, QML se hieu la duong dan tuong doi va khong phat ra tieng.
        source: root.voice && root.voice.previewPath.length > 0 ? "file:///" + root.voice.previewPath.replace("\\", "/") : ""
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

    function currentLanguage() {
        // "Tiếng Việt" -> "vi", "Tiếng Anh" -> "en". Khong ghi cung "vi" nua:
        // truoc day tab luon goi linkedVoices(provider) mac dinh "vi" nen
        // van ban tieng Anh qua OmniVoice van bi doc theo tieng Viet.
        return languageCombo.currentText && languageCombo.currentText.indexOf("Tiếng Anh") === 0 ? "en" : "vi"
    }

    function refreshVoices() {
        if (!providerCombo || !voiceCombo || !languageCombo || !root.voice)
            return
        var provider = providerCombo.currentValue ? providerCombo.currentValue : "edge"
        var options = root.voice.linkedVoices(provider, root.currentLanguage())
        packStatus.text = root.voice.linkedPackStatus(provider)
        voiceListModel.clear()
        for (var i = 0; i < options.length; i++) {
            voiceListModel.append({"label": options[i].label + (options[i].available ? "" : " (chưa cài)"), "voice": options[i].voice})
        }
        if (voiceListModel.count > 0)
            voiceCombo.currentIndex = 0
    }

    Component.onCompleted: root.refreshVoices()

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

                Text {
                    id: packStatus
                    Layout.fillWidth: true
                    text: qsTr("Đang liên kết với Gói tài nguyên của app...")
                    color: Theme.text
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.control
                    wrapMode: Text.WordWrap
                }

                Text {
                    Layout.fillWidth: true
                    text: qsTr("Chọn đúng ngôn ngữ của văn bản trước khi chọn giọng. Tiếng Việt thì dùng VieNeu, tiếng Anh thì dùng OmniVoice hoặc Edge en-US. Đừng chọn OmniVoice cho văn bản tiếng Việt, và đừng chọn VieNeu cho văn bản tiếng Anh. Danh sách giọng dưới đây lấy trực tiếp từ app chính theo ngôn ngữ đã chọn, không phải danh sách riêng của tab này — cài gói xong là giọng tự hiện, gỡ gói là giọng tự mất. Nếu VieNeu đang tải dở thì chưa chọn được, đợi tải xong.")
                    color: Theme.textMuted
                    font.family: Theme.fontFamily
                    font.pixelSize: TypeScale.control
                    wrapMode: Text.WordWrap
                }

                ComboBox {
                    id: languageCombo
                    Layout.fillWidth: true
                    model: [qsTr("Tiếng Việt"), qsTr("Tiếng Anh")]
                    onCurrentIndexChanged: root.refreshVoices()
                }

                ComboBox {
                    id: providerCombo
                    Layout.fillWidth: true
                    textRole: "label"
                    valueRole: "provider"
                    model: AppController.ttsProviderOptionsForLanguage("vi")
                    onCurrentIndexChanged: root.refreshVoices()
                }

                ListModel {
                    id: voiceListModel
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.space12
                    ComboBox {
                        id: voiceCombo
                        Layout.fillWidth: true
                        textRole: "label"
                        valueRole: "voice"
                        model: voiceListModel
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
                        onClicked: root.voice.generatePreviewWithProvider(voiceText.text, voiceCombo.currentValue ? voiceCombo.currentValue : "", providerCombo.currentValue ? providerCombo.currentValue : "edge", rateCombo.currentText, "+0Hz", "+0%", root.currentLanguage())
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

                // Thanh play ngay trong tab: tao xong la an nghe luon, khong can mo trinh phat ngoai.
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Theme.space8
                    visible: root.voice && root.voice.previewPath.length > 0

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Theme.space12
                        AppButton {
                            text: player.playbackState === MediaPlayer.PlayingState ? qsTr("Tạm dừng") : qsTr("▶ Nghe ngay tại đây")
                            onClicked: player.playbackState === MediaPlayer.PlayingState ? player.pause() : player.play()
                        }
                        AppButton {
                            text: qsTr("Dừng")
                            onClicked: player.stop()
                        }
                        Text {
                            text: player.playbackState === MediaPlayer.PlayingState ? qsTr("Đang phát...") : qsTr("Đã tạo xong, bấm Nghe ngay tại đây để nghe.")
                            color: Theme.textMuted
                            font.family: Theme.fontFamily
                            font.pixelSize: TypeScale.control
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Theme.space8
                        Text {
                            text: Math.floor(player.position / 60000) + ":" + (Math.floor(player.position / 1000) % 60 < 10 ? "0" : "") + (Math.floor(player.position / 1000) % 60)
                            color: Theme.textMuted
                            font.family: Theme.fontFamily
                            font.pixelSize: TypeScale.control
                        }
                        Slider {
                            Layout.fillWidth: true
                            from: 0
                            to: player.duration > 0 ? player.duration : 1
                            value: player.position
                            onMoved: player.setPosition(value)
                        }
                        Text {
                            text: Math.floor(player.duration / 60000) + ":" + (Math.floor(player.duration / 1000) % 60 < 10 ? "0" : "") + (Math.floor(player.duration / 1000) % 60)
                            color: Theme.textMuted
                            font.family: Theme.fontFamily
                            font.pixelSize: TypeScale.control
                        }
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
