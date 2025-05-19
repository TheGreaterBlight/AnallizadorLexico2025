import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QHeaderView, QFileDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("MainWindow.ui", self)
        self.setWindowTitle("Analizador Léxico, Sintáctico y Semántico")

        self.pushButton.clicked.connect(self.iniciar_analisis_lexico)
        self.pushButton_2.clicked.connect(self.iniciar_analisis_sintactico)
        self.pushButtonfile.clicked.connect(self.obtener_archivo)
        self.pushButton_3.clicked.connect(self.iniciar_analisis_semantico)

        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Lexema", "Token", "#"])
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStretchLastSection(True)

    def obtener_archivo(self):
        options = QFileDialog.Options()
        archivo, _ = QFileDialog.getOpenFileName(self, "Abrir archivo de texto", "", "Text Files (*.txt)", options=options)
        if archivo:
            with open(archivo, 'r') as file:
                content = file.read()
                self.plainTextEdit_2.appendPlainText(content)

    def iniciar_analisis_lexico(self):
        texto = self.plainTextEdit_2.toPlainText()
        palabras_reservadas = ["int", "float", "void", "if", "while", "return", "else"]
        operadores = ['+', '-', '*', '/', '<', '<=', '>', '>=', '==', '!=', '&&', '||']
        delimitadores = ['(', ')', '{', '}', ';', ',']
        resultados = []
        i = 0
        while i < len(texto):
            c = texto[i]
            if c.isspace():
                i += 1
                continue
            if c.isalpha():
                inicio = i
                while i < len(texto) and (texto[i].isalnum() or texto[i] == '_'):
                    i += 1
                token = texto[inicio:i]
                if token in palabras_reservadas:
                    resultados.append([token, "Palabra reservada", 4])
                else:
                    resultados.append([token, "Identificador", 0])
                continue
            elif c.isdigit():
                inicio = i
                tiene_punto = False
                while i < len(texto) and (texto[i].isdigit() or (texto[i] == '.' and not tiene_punto)):
                    if texto[i] == '.':
                        tiene_punto = True
                    i += 1
                token = texto[inicio:i]
                if tiene_punto:
                    resultados.append([token, "Número real", 2])
                else:
                    resultados.append([token, "Número entero", 1])
                continue
            elif c in operadores:
                if i + 1 < len(texto) and texto[i:i+2] in operadores:
                    resultados.append([texto[i:i+2], "Operador", 7])
                    i += 2
                else:
                    resultados.append([c, "Operador", 7])
                    i += 1
                continue
            elif c in delimitadores:
                resultados.append([c, "Delimitador", 12])
                i += 1
                continue
            else:
                resultados.append([c, "Error léxico", 6])
                i += 1
        self.tableWidget.setRowCount(0)
        for fila in resultados:
            row_position = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row_position)
            for columna, item in enumerate(fila):
                self.tableWidget.setItem(row_position, columna, QTableWidgetItem(str(item)))

    def iniciar_analisis_sintactico(self):
        texto = self.plainTextEdit_2.toPlainText().splitlines()
        errores = []
        variables_declaradas = {}
        variables_reportadas = set()
        function_declaration = False
        function_opened = False
        for num_linea, linea in enumerate(texto, start=1):
            linea = linea.strip()
            if linea.startswith("int main()"):
                function_declaration = True
                continue
            if function_declaration:
                if linea.startswith("{"):
                    function_opened = True
                    function_declaration = False
                    continue
                errores.append(f"Error en la línea {num_linea}: falta '{{' después de 'int main()'.")
                function_declaration = False
            if not linea:
                continue
            if linea.startswith(("int", "float", "void")):
                if not linea.endswith(";"):
                    errores.append(f"Error en la línea {num_linea}: falta ';' al final de la declaración.")
                else:
                    tokens = linea.split()
                    if len(tokens) >= 2:
                        tipo = tokens[0]
                        variable = tokens[1].replace(";", "")
                        variables_declaradas[variable] = tipo
            elif "=" in linea:
                if not linea.endswith(";"):
                    errores.append(f"Error en la línea {num_linea}: falta ';' al final de la asignación.")
                tokens = linea.replace(";", "").split()
                for token in tokens:
                    if token.isidentifier() and token not in variables_declaradas and token not in variables_reportadas:
                        errores.append(f"Error en la línea {num_linea}: variable '{token}' no está declarada.")
                        variables_reportadas.add(token)
                variable, valor = linea.replace(";", "").split("=")
                variable = variable.strip()
                valor = valor.strip()
                if variable in variables_declaradas:
                    tipo = variables_declaradas[variable]
                    if tipo == "int" and "." in valor:
                        errores.append(f"Error en la línea {num_linea}: no se puede asignar un valor de punto flotante a una variable de tipo 'int'.")
            else:
                tokens = linea.replace(";", "").split()
                for token in tokens:
                    if token.isidentifier() and token not in variables_declaradas and token not in ["if", "else"] and token not in variables_reportadas:
                        errores.append(f"Error en la línea {num_linea}: variable '{token}' no está declarada.")
                        variables_reportadas.add(token)
            if "if" in linea:
                if not linea.strip().endswith("{"):
                    siguiente_linea = texto[num_linea].strip() if num_linea < len(texto) else ""
                    if not siguiente_linea.startswith("{"):
                        errores.append(f"Error en la línea {num_linea}: falta '{{' al final del bloque 'if'.")
        self.plainTextEdit_3.clear()
        if errores:
            for error in errores:
                self.plainTextEdit_3.appendPlainText(error)
        else:
            self.plainTextEdit_3.appendPlainText("Análisis sintáctico completado: no se encontraron errores.")
    
    def iniciar_analisis_semantico(self):
        texto = self.plainTextEdit_2.toPlainText().splitlines()
        errores = []
        variables_declaradas = {}
        palabras_reservadas = {"int", "float", "if", "else", "return"}
        simbolos_ignorar = {"{", "}", "(", ")", "<", ">", "+", "-", "*", "/", "=", ";"}
        for num_linea, linea in enumerate(texto, start=1):
            tokens = linea.replace(";", "").replace("(", "").replace(")", "").split()
            if len(tokens) >= 2 and tokens[0] in ["int", "float"]:
                tipo = tokens[0]
                variable = tokens[1].strip().lower()
                variables_declaradas[variable] = tipo
            if "=" in linea:
                partes = linea.split("=")
                variable = partes[0].strip().lower()
                valor = partes[1].strip().replace(";", "")
                if variable not in variables_declaradas:
                    errores.append(f"Error en la línea {num_linea}: variable '{variable}' no está declarada.")
                else:
                    tipo_variable = variables_declaradas[variable]
                    if tipo_variable == "int" and any(c in valor for c in ".eE"):
                        errores.append(f"Error en la línea {num_linea}: tipo incompatible, asignación de flotante a 'int'.")
            for token in tokens:
                if (token not in variables_declaradas and 
                    token not in palabras_reservadas and
                    token not in simbolos_ignorar and
                    not token.isdigit()):
                    errores.append(f"Error en la línea {num_linea}: identificador '{token}' no está definido.")
        self.plainTextEdit_4.clear()
        if errores:
            for error in errores:
                self.plainTextEdit_4.appendPlainText(error)
        else:
            self.plainTextEdit_4.appendPlainText("Análisis semántico completado: no se encontraron errores.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())