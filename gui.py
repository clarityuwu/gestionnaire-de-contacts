from PyQt5.QtWidgets import QWidget, QApplication

application = QApplication([])

mainWindow = QWidget()

mainWindow.setGeometry(0, 0, 1200, 700)
mainWindow.setWindowTitle('Contacts')

mainWindow.show()

application.exec()