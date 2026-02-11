import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    Layout.fillWidth: true
    Layout.fillHeight: true

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 16

        GroupBox {
            title: "Créer une carte"
            Layout.fillWidth: true

            GridLayout {
                anchors.fill: parent
                columns: 2
                columnSpacing: 12
                rowSpacing: 8

                Label { text: "Nom *" }
                TextField { id: nameField; Layout.fillWidth: true }

                Label { text: "Description" }
                TextArea { id: descriptionField; Layout.fillWidth: true }

                Label { text: "Attaque" }
                SpinBox { id: attackSpin; from: 0; to: 99; editable: true }

                Label { text: "Défense" }
                SpinBox { id: defenseSpin; from: 0; to: 99; editable: true }

                Label { text: "Coût" }
                SpinBox { id: costSpin; from: 0; to: 99; editable: true }
            }
        }

        Button {
            text: "Créer"
            enabled: nameField.text.trim().length > 0
            onClicked: {
                cardController.createCard(
                    nameField.text,
                    descriptionField.text,
                    attackSpin.value,
                    defenseSpin.value,
                    costSpin.value
                )
            }
        }

        Label {
            id: statusLabel
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
        }
    }

    Connections {
        target: cardController

        function onCardCreated(message) {
            statusLabel.text = message
        }

        function onCardCreationFailed(message) {
            statusLabel.text = message
        }
    }
}