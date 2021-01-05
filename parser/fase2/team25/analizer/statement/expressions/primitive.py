from analizer.abstract.expression import Expression
from analizer.reports import Nodo


class Primitive(Expression):
    """
    Esta clase contiene los tipos primitivos
    de datos como STRING, NUMBER, BOOLEAN
    """

    def __init__(self, type_, value, temp, row, column):
        super().__init__(row, column)
        self.type = type_
        self.value = value
        self.temp = str(temp)

    def execute(self, environment):
        return self

    def dot(self):
        node = Nodo.Nodo(str(self.value))
        return node
    
    def generate3d(self,environment, instanciaAux):
        return str(self.value) if not isinstance(self.value, str) else "'" + self.value + "'" # TANTO PARA FASE 1 O FASE 2 SE RETORNA LO MISMO