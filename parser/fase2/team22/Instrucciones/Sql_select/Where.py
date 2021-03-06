from Instrucciones.TablaSimbolos.Instruccion import Instruccion

class Where(Instruccion):
    def __init__(self, valor, tipo, strGram, linea, columna):
        Instruccion.__init__(self,tipo,linea,columna, strGram)
        self.valor = valor

    def ejecutar(self, tabla, arbol):
        super().ejecutar(tabla,arbol)
        if not arbol.getUpdate():
            arbol.setWhere(True)
            val = self.valor.ejecutar(tabla,arbol)
            arbol.setWhere(False)
            return val
            
        val = self.valor.ejecutar(tabla,arbol)
        print("hola me ejecuto en el where porque ahora soy un update")
        return val
        
    def generar3D(self, tabla, arbol):
        super().generar3D(tabla,arbol)

'''
instruccion = Where("hola mundo",None, 1,2)

instruccion.ejecutar(None,None)
'''