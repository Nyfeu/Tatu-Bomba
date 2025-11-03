import sys
from PyQt6.QtWidgets import QApplication

from dashboard_app import MainWindow

if __name__ == "__main__":
    
    # Cria a instância da aplicação
    app = QApplication(sys.argv)
    
    # Cria e exibe a janela principal
    window = MainWindow()
    window.show()
    
    # Inicia o loop de eventos da aplicação
    sys.exit(app.exec())
