import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    Layout.fillWidth: true
    Layout.fillHeight: true

    ListModel { id: cardsModel }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 10

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: cardsModel

            delegate: Rectangle {
                width: (ListView.view ? ListView.view.width : 0)
                height: 60
                border.width: 1
                radius: 4
                color: "#f5f5f5"

                Column {
                    anchors.centerIn: parent
                    spacing: 2

                    Text { text: name; font.bold: true }
                    Text { text: "ATK: " + attack + "  DEF: " + defense + "  COST: " + cost }
                }
            }
        }
    }

    onVisibleChanged: {
        if (visible) {
            cardController.loadCards()
        }
    }


    Component.onCompleted: {
        cardController.loadCards()
    }

    Connections {
        target: cardController

        function onCardsLoaded(cards) {
            cardsModel.clear()
            for (let i = 0; i < cards.length; i++) {
                cardsModel.append(cards[i])
            }
        }
    }
}