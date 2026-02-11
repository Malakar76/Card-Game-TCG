import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    visible: true
    width: 900
    height: 600
    title: "Card Game TCG"

    ColumnLayout {
        anchors.fill: parent

        TabBar {
            id: tabBar
            Layout.fillWidth: true

            TabButton { text: "Créer une carte" }
            TabButton { text: "Cartes existantes" }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            CreateCardPage { Layout.fillWidth: true; Layout.fillHeight: true }
            CardsPage { Layout.fillWidth: true; Layout.fillHeight: true }
        }
    }
}