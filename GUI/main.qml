import QtQuick
import QtQuick.Controls

ApplicationWindow {
    visible: true
    width: 400
    height: 300
    color: "#111111"

    property string currentState: "idle"

    Connections {
        target: backend
        function onStateChanged(state) {
            currentState = state
        }
    }

    Rectangle {
        id: face
        anchors.centerIn: parent
        width: 200
        height: 100
        color: "transparent"

        Row {
            anchors.centerIn: parent
            spacing: 40

            Rectangle {
                id: leftEye
                width: 40
                height: 40
                radius: 20
                color: currentState === "listening" ? "#00ffcc" : "white"
                scale: 1.0
            }

            Rectangle {
                id: rightEye
                width: 40
                height: 40
                radius: 20
                color: currentState === "listening" ? "#00ffcc" : "white"
                scale: 1.0
            }
        }

        // 👁 Blink Animation
        SequentialAnimation {
            id: blinkAnim
            loops: Animation.Infinite

            PauseAnimation { duration: 2000 + Math.random() * 2000 }

            ParallelAnimation {
                NumberAnimation { target: leftEye; property: "scaleY"; to: 0.1; duration: 100 }
                NumberAnimation { target: rightEye; property: "scaleY"; to: 0.1; duration: 100 }
            }

            ParallelAnimation {
                NumberAnimation { target: leftEye; property: "scaleY"; to: 1; duration: 100 }
                NumberAnimation { target: rightEye; property: "scaleY"; to: 1; duration: 100 }
            }
        }

        Component.onCompleted: blinkAnim.start()

        // 👀 Random small movement
        Timer {
            interval: 3000
            running: true
            repeat: true
            onTriggered: {
                leftEye.x = leftEye.x + (Math.random() * 10 - 5)
                rightEye.x = rightEye.x + (Math.random() * 10 - 5)
            }
        }
    }
}