import Gramatica as g
import tablasimbolos as TS
from expresiones import *
from instrucciones import *
from reporteAST import *
from temporal import *
from storageManager import jsonMode as EDD
import Funciones as f
import math
import random
from tkinter import *
import tkinter.filedialog
import tkinter.messagebox
from prettytable import PrettyTable
from reporte_g import *
import copy
import itertools
from reportes import *

#---------variables globales
listaInstrucciones = []
listaTablas = [] #guarda las cabeceras de las tablas creadas
outputTxt = [] #guarda los mensajes a mostrar en consola
outputTS = [] #guarda el reporte tabla simbolos
baseActiva = "" #Guarda la base temporalmente activa

Errores_Semanticos = []
#--------Ejecucion Datos temporales-----------
def reiniciarVariables():
    global outputTxt
    outputTxt=[]
    global listaTablas
    listaTablas=[]
    global outputTS
    outputTS = []
    EDD.dropAll() #eliminar para ir haciendo pruebas, quitarlo al final
    baseActiva =""#eliminar para ir haciendo pruebas, quitarlo al final

def insertartabla(columnas,nombre):
    global listaTablas
    listaTablas.append(Tabla_run(baseActiva,nombre,columnas))

def EliminarTablaTemp(baseAc,nombre):
    global listaTablas
    pos=0
    #all para eliminar todas las tablas de una base de datos
    if(nombre=='all'):
        while pos< len(listaTablas):
            if(listaTablas[pos].basepadre==baseAc):
                listaTablas.pop(pos)
            else:
                pos=pos+1
    else:
        while pos< len(listaTablas):
            if(listaTablas[pos].nombre==nombre and listaTablas[pos].basepadre==baseAc):
                listaTablas.pop(pos)
                break
            else:
                pos=pos+1

def agregarMensjae(tipo,mensaje,codigo):
    global outputTxt
    txtOut=MensajeOut()
    txtOut.tipo=tipo
    txtOut.mensaje=mensaje
    txtOut.codigo=codigo
    outputTxt.append(txtOut)

def agregarTSRepor(instruccion,identificador,tipo,referencia,dimension):
    global outputTS
    tsOut=MensajeTs()
    tsOut.instruccion=instruccion
    tsOut.identificador=identificador
    tsOut.tipo=tipo
    tsOut.referencia=referencia
    tsOut.dimension=dimension
    outputTS.append(tsOut)

def buscarTabla(baseAc,nombre):
    pos=0
    while pos< len(listaTablas):
            if(listaTablas[pos].nombre==nombre and listaTablas[pos].basepadre==baseAc):
                return listaTablas[pos]
            else:
                pos=pos+1
    return None

def validarTipo(T,valCOL):
    if(valCOL==None):
        ''
    #acepta int
    elif(T=="smallint" or T=="integer" or T=="bigint"):
        try:
            valCOL=int(round(float(valCOL)))
        except:
            valCOL=None
    #acepta float
    elif(T=="decimal" or T=="numeric" or T=="real" or T=="double precision" or T=="money"):
        try:
            valCOL=float(valCOL)
        except:
            valCOL=None
    #acepta str        
    elif(T=="character varying" or T=="varchar" or T=="text" or T=="character" or T=="char"):
        try:
            valCOL=str(valCOL)
        except:
            valCOL=None
    #acepta date
    elif(T=="date" or T=="timestamp" or T=="time" or T=="interval"):
        try:
            valCOL=str(valCOL)
        except:
            valCOL=None
    #acepta Type
    elif(T=="boolean"):
        try:
            valCOL=str(valCOL)
            if(valCOL=='1'):
                valCOL=True
            elif(valCOL=='0'):
                valCOL=False
            else:
                valCOL=valCOL.lower()
                if(valCOL=='true' or valCOL=='t' or valCOL=='y' or valCOL=='yes' or valCOL=='on'):
                    valCOL=True
                elif(valCOL=='false' or valCOL=='f' or valCOL=='n' or valCOL=='no' or valCOL=='off'):
                    valCOL=False
                else:
                    valCOL=None
        except:
            valCOL=None
    else:
        tablaType=EDD.extractTable(baseActiva,T)#Extraer valores de la tabla
        if(tablaType==None):
            valCOL=None
        else:
            if valCOL not in tablaType[0]:
                valCOL=None
            
    return valCOL

def validarSizePres(tipo,val,size,presicion):
    result=True
    #revisar el valor
    if(val!=None):
        if(size!=None):
            #tipos con (n)
            if(presicion==None):
                if(tipo=="character varying" or tipo=="varchar" 
                or tipo=="text" or tipo=="character" or tipo=="char"):
                    if(len(val)>size):
                        result=False
            #tipos con (n,m)
            else:
                ''
        #tamanio por defecto    
        else:
            if(tipo=='char' or tipo=='character'):
                #size por defecto = 1
                if(len(val)>1):
                    result=False
    #no hay valor
    else:
        result=True
    return result

def use_db(nombre):
    global baseActiva
    baseActiva = nombre

def indiceColum(baseAc,ntable,nombre):
    pos=0
    posC=0
    while pos< len(listaTablas):
            posC=0
            if(listaTablas[pos].nombre==ntable and listaTablas[pos].basepadre==baseAc): 
                while posC < len(listaTablas[pos].atributos):
                    if listaTablas[pos].atributos[posC].nombre == nombre:
                        return posC
                    else:
                        posC=posC+1
            else:
                pos=pos+1
    return None

def obtenerPKexp(expresion,nombres,ts):
    if isinstance(expresion, Operacion_Relacional):
        if expresion.operador == OPERACION_RELACIONAL.IGUAL: 
            col = resolver_operacion(expresion.op1,ts)
            if col in nombres:
                return resolver_operacion(expresion.op2,ts)
    elif isinstance(expresion, Operacion_Logica_Binaria):
        op1 = obtenerPKexp(expresion.op1,nombres,ts)
        op2 = obtenerPKexp(expresion.op2,nombres,ts)
        if op1 is not None:
            return op1
        if op2 is not None:
            return op2
    return None

def getpks(baseAc,nombret):
    tabla=buscarTabla(baseAc,nombret)
    llaves=[]
    if tabla is not None:
        for colum in tabla.atributos:
            if colum.primary==True:
                llaves.append(colum.nombre)
    return llaves

def llaves_tabla(exp,llaves,ts):
    keys=[]
    for key in llaves:
        ky=obtenerPKexp(exp,key,ts)
        if key is not None:
            keys.append(ky)
    return keys

def indice_llaves(llaves,baseAc,ntabla):
    lindices=[]
    cont=0
    while cont < len(llaves):
        lindices.append(indiceColum(baseActiva,ntabla,llaves[cont]))
        cont=cont+1
    return lindices

#---------Ejecucion Funciones EDD-------------
def crear_BaseDatos(instr,ts):
    nombreDB=resolver_operacion(instr.nombre,ts).lower()
    
    msg='Creando base de datos: '+nombreDB
    agregarMensjae('normal',msg,'')

    #result=0 operacion exitosa
    #result=1 error en la operacion
    #result=2 base de datos existente       
    result = EDD.createDatabase(nombreDB)

    if instr.reemplazar and result==2:
        #eliminar
        EDD.dropDatabase(nombreDB)
        EliminarTablaTemp(nombreDB,'all')#eliminar los temporales
        #crear
        result = EDD.createDatabase(nombreDB)
        if result==1:
            msg='Error en EDD'
            agregarMensjae('error',msg,'')
        else:
            msg='Fue Reemplazada'
            agregarMensjae('alert',msg,'')

    elif instr.verificacion:
        if result==0:
            msg='Todo OK'
            agregarMensjae('exito',msg,'')
        elif result==2 :
            msg='existe pero se omite error'
            agregarMensjae('alert',msg,'')
            #si retorna error no se muestra
    else:
        if result==0:
            msg='Todo OK'
            agregarMensjae('exito',msg,'')
        elif result==2:
            msg='Error base de existente: '+nombreDB
            agregarMensjae('error',msg,'')
        elif result==1:
            msg='Error en EDD'
            agregarMensjae('error',msg,'')

    #print('reemplazar:',instr.reemplazar,'verificar:',instr.verificacion,'nombre:',instr.nombre,'propietario:',instr.propietario,'modo:',instr.modo)

def eliminar_BaseDatos(instr,ts):
    nombreDB=str(resolver_operacion(instr.nombre,ts)).lower()
    eliminarOK=False;
    #result=0 operacion exitosa
    #result=1 error en la operacion
    #result=2 base de datos no existente  
    result = EDD.dropDatabase(nombreDB)
    msg='Eliminado Base de datos: '+nombreDB;
    agregarMensjae('normal',msg,'')
    
    if(instr.existencia):
        if(result==0):
            eliminarOK=True;
            msg='Todo OK'
            agregarMensjae('exito',msg,'')
        else:
            eliminarOK=False
            msg='no se muestra el error'
            agregarMensjae('alert',msg,'')
            #si retorna error no se muestra
    else:
        if(result==0):
            eliminarOK=True;
            msg='Todo OK'
            agregarMensjae('exito',msg,'')
        elif(result==1):
            eliminarOK=False
            msg='Error en EDD'
            agregarMensjae('error',msg,'')
        else:
            msg='Error base de datos no existente: '+nombreDB
            agregarMensjae('error',msg,'')
    
    if eliminarOK:
        EliminarTablaTemp(nombreDB,'all')#eliminar los temporales
        #elim_use()

    #print('nombre:',instr.nombre,'validarExistencia',instr.existencia)

def mostrar_db(instr,ts):
    #retorna una lista[db1,db2...], si no hay estara vacia[]
    result=EDD.showDatabases()
    msg='Lista de bases de datos'
    agregarMensjae('normal',msg,'')

    if not result:
        msg='No existen bases de datos ...' 
        agregarMensjae('alert',msg,'')   
    else:
        for val in result:
            agregarMensjae('exito',val,'')

def eliminar_Tabla(instr,ts):
    nombreT=''
    nombreT=resolver_operacion(instr.nombre,ts).lower()

    #Valor de retorno: 0 operación exitosa
    # 1 error en la operación, 
    # 2 database no existente, 
    # 3 table no existente.
    result=EDD.dropTable(baseActiva,nombreT)
    eliminarOK=False;

    msg='Eliminar Tabla:'+nombreT
    agregarMensjae('normal',msg,'')
    if(instr.existencia):
        if(result==0):
            msg='Tabla eliminada'
            agregarMensjae('exito',msg,'')
            eliminarOK=True
        else:
            msg='se omite error'
            agregarMensjae('alert',msg,'')
    else:
        if(result==0):
            msg='Tabla eliminada'
            agregarMensjae('exito',msg,'')
            eliminarOK=True
        elif(result==1):
            msg='Error en EDD'
            agregarMensjae('error',msg,'')
        elif(result==2):
            Errores_Semanticos.append("Error Semantico: No Existe la base de datos activa "+baseActiva)
            msg='no existe la base de datos activa:'+baseActiva
            agregarMensjae('error',msg,'')
        elif(result==3):
            Errores_Semanticos.append("Error Semantico: 42P01: La tabla "+nombre +" no existe")
            msg='42P01:Tabla no existe:'+nombreT
            agregarMensjae('error',msg,'42P01')
        
    if eliminarOK:
        EliminarTablaTemp(baseActiva,nombreT)


    #print('nombre:',instr.nombre,'validarExistencia',instr.existencia)

def seleccion_db(instr,ts):
    nombreDB = resolver_operacion(instr.nombre,ts).lower()
    result=EDD.showDatabases()
    msg='Seleccionando base de datos: '+nombreDB
    agregarMensjae('normal',msg,'')
    if not result: # Lista Vacia
        msg='No existen bases de datos ...'
        agregarMensjae('alert',msg,'')  
    elif nombreDB in result: # Encontrada
        msg='Base de datos seleccionada'
        agregarMensjae('exito',msg,'')
        use_db(nombreDB)
    else: # No encontrada
        Errores_Semanticos.append("Error Semantico: 42602: La Base de datos  "+ str(nombreDB) +" no existe")
        msg='Base de datos \"'+str(nombreDB)+'\" no registrada'
        agregarMensjae('error',msg,'')
        
#---------pendientes-----------------------
def crear_Tabla(instr,ts):
    #Pendiente
    # -zonahoraria
    # -check

    nombreT=resolver_operacion(instr.nombre,ts).lower()
    listaColumnas=[]
    crearOK=True
    pkCompuesta=False
    msg='Creando Tabla:'+nombreT
    agregarMensjae('normal',msg,'')
    contC=0# variable para contar las columnas a mandar a EDD
    
    #verificar el padre
    if(instr.padre!=False):
        nombPadre=resolver_operacion(instr.padre,ts).lower()
        herencia=buscarTabla(baseActiva,nombPadre)
        #error no existe la tabla
        if(herencia==None):
            crearOK=False
            Errores_Semanticos.append("Error Semantico: 42P01: No existe la tabla para la herencia:"+nombPadre)
            msg='42P01:No existe la tabla para la herencia:'+nombPadre
            agregarMensjae('error',msg,'42P01')
        #copiar las columnas
        else:
            for col in herencia.atributos:
                msg='columna herencia:'+col.nombre
                agregarMensjae('alert',msg,'')
                listaColumnas.append(col)
    
    #recorrer las columnas
    for colum in instr.columnas :
        colAux=Columna_run()#columna temporal para almacenar
        #bloque de llaves primarias o foraneas
        if isinstance(colum, llaveTabla) :
            #bloque de primarias
            if(colum.tipo==True):
                if(pkCompuesta==False):
                    pkCompuesta=True#primer bloque pk(list)
                    #pk compuesta, revisar la lista
                    for pkC in colum.columnas:
                        exCol=False
                        for lcol in listaColumnas:
                            if(lcol.nombre==pkC.lower()):
                                exCol=True
                                if(lcol.primary==None):
                                    lcol.primary=True
                                else:
                                    crearOK=False
                                    msg='primary key repetida:'+pkC.lower()
                                    agregarMensjae('error',msg,'42P16') 
                                    Errores_Semanticos.append("Error Semantico: 42P16: Primary key Repetida "+pkC.lower())
                                      
                        if(exCol==False):
                            crearOK=False
                            Errores_Semanticos.append("Error Semantico: 42P16: No se puede asignar como primaria: "+pkC.lower())
                            msg='42P16:No se puede asignar como primaria:'+pkC.lower()
                            agregarMensjae('error',msg,'42P16')
                            

                else: 
                    crearOK=False
                    msg='42P16:Solo puede existir un bloque de PK(list)'
                    agregarMensjae('error',msg,'42P16')
                    Errores_Semanticos.append("Error Semantico: 42P16:  Solo puede existir un bloque de PK(list)")
            #bloque de foraneas
            else:
                refe=colum.referencia.lower()
                tablaRef=buscarTabla(baseActiva,refe)
                #no existe la tabla de referencia
                if(tablaRef==None):
                    crearOK=False
                    msg='42P01:no existe la referencia a la Tabla '+refe
                    agregarMensjae('error',msg,'42P01')
                    Errores_Semanticos.append("Error Semantico: 42P01: No existe la referencia a la Tabla "+refe)
                else:
                    #validar #columnas==#refcolums
                    if(len(colum.columnas)==len(colum.columnasRef)):
                        #verificar si existen dentro de la tabla a crear
                        pos=0#contador para referencias
                        for fkC in colum.columnas:
                            exCol=False
                            for lcol in listaColumnas:
                                if(lcol.nombre==fkC.lower()):
                                    exCol=True
                                    if(lcol.foreign==None):
                                        #validar si existe en la tabla de referencia
                                        exPK=False
                                        for pkC in tablaRef.atributos:
                                            #validar nombre y Primary
                                            if(pkC.nombre==colum.columnasRef[pos].lower() and pkC.primary==True):
                                                exPK=True
                                                lcol.foreign=True #asignar como foranea
                                                lcol.refence=[refe,pkC.nombre] #guardar la tabla referencia y la columna
                                                if(pkC.tipo!=lcol.tipo):
                                                    crearOK=False
                                                    msg='42804:no coicide el tipo de dato:'+colum.columnasRef[pos]
                                                    agregarMensjae('error',msg,'42804')
                                                    Errores_Semanticos.append("Error Semantico: no coicide el tipo de dato:"+colum.columnasRef[pos])
                                                break                                  
                                        if(exPK==False):
                                            crearOK=False
                                            msg='42703:no existe la referencia pk:'+colum.columnasRef[pos]
                                            agregarMensjae('error',msg,'42703')
                                            Errores_Semanticos.append("Error Semantico 42703: No existe la referencia pk: "+colum.columnasRef[pos])
                                    else:
                                        crearOK=False
                                        msg='foreign key repetida:'+fkC.lower()
                                        agregarMensjae('error',msg,'42P16')
                                        Errores_Semanticos.append("Error Semantico 42P16: foreign key repetida: "+fkC.lower())
                            if(exCol==False):
                                crearOK=False
                                msg='42P16:No se puede asignar como foranea:'+fkC.lower()
                                agregarMensjae('error',msg,'42P16')
                                Errores_Semanticos.append('Error Semantico 42P16:No se puede asignar como foranea: '+fkC.lower())
                            pos=pos+1
                    else:
                        crearOK=False
                        msg='42P16: la cantidad de referencias es distinta: '+str(len(colum.columnas))+'!='+str(len(colum.columnasRef))
                        agregarMensjae('error',msg,'42P16')
                        Errores_Semanticos.append('Error Semantico 42P16: la cantidad de referencias es distinta: '+str(len(colum.columnas))+'!='+str(len(colum.columnasRef)))
        #columna
        elif isinstance(colum, columnaTabla) :
            contC=contC+1
            colAux.nombre=resolver_operacion(colum.id,ts).lower()#guardar nombre col
            #revisar columnas repetidas
            pos=0
            colOK=True
            while pos< len(listaColumnas):
                if(listaColumnas[pos].nombre==colAux.nombre):
                    crearOK=False;
                    colOK=False
                    msg='42701:nombre de columna repetido:'+colAux.nombre
                    agregarMensjae('error',msg,'42701')
                    Errores_Semanticos.append('Error Semantico 42701:nombre de columna repetido:'+colAux.nombre)
                    break;
                else:
                    pos=pos+1
            #si no existe el nombre de la columna revisa el resto de errores
            if(colOK):
                if isinstance(colum.tipo,Operando_ID):
                    colAux.tipo=resolver_operacion(colum.tipo,ts).lower()#guardar tipo col
                    tablaType=buscarTabla(baseActiva,colAux.tipo)#revisar la lista de Types
                    if(tablaType==None):
                        crearOK=False
                        msg='42704:No existe el Type '+colAux.tipo+' en la columna '+colAux.nombre
                        agregarMensjae('error',msg,'42704')
                        Errores_Semanticos.append('Error Semantico 42704:No existe el Type '+colAux.tipo+' en la columna '+colAux.nombre)

                else:
                    colAux.tipo=colum.tipo.lower() #guardar tipo col
                if(colum.valor!=False):
                    if(colAux.tipo=='character varying' or colAux.tipo=='varchar' or colAux.tipo=='character' or colAux.tipo=='char' or colAux.tipo=='interval'):
                        if(len(colum.valor)==1):
                            errT=True;#variable error en p varchar(p)
                            if isinstance(colum.valor[0],Operando_Numerico):
                                val=resolver_operacion(colum.valor[0],ts)
                                if(type(val) == int):
                                    colAux.size=val
                                    errT=False#no existe error
                            if errT:
                                crearOK=False
                                msg='42601:el tipo '+colAux.tipo+' acepta enteros como parametro: '+colAux.nombre
                                agregarMensjae('error',msg,'42601')
                                Errores_Semanticos.append('Error Semantico: 42601: El tipo '+colAux.tipo+' acepta enteros como parametro: '+colAux.nombre)
                        else:
                            crearOK=False
                            msg='42601:el tipo '+colAux.tipo+' solo acepta 1 parametro: '+colAux.nombre
                            agregarMensjae('error',msg,'42601')
                            Errores_Semanticos.append('Error Semantico: 42601:el tipo '+colAux.tipo+' solo acepta 1 parametro: '+colAux.nombre)
                    elif(colAux.tipo=='decimal' or colAux.tipo=='numeric'):
                        if(len(colum.valor)==1):
                            errT=True;#variable error en p varchar(p)
                            if isinstance(colum.valor[0],Operando_Numerico):
                                val=resolver_operacion(colum.valor[0],ts)
                                if(type(val) == int):
                                    colAux.size=val
                                    errT=False#no existe error
                            if errT:
                                crearOK=False
                                msg='42601:el tipo '+colAux.tipo+' acepta enteros como parametro: '+colAux.nombre
                                agregarMensjae('error',msg,'42601')
                                Errores_Semanticos.append('Error Semantico: 42601:el tipo '+colAux.tipo+' acepta enteros como parametro: '+colAux.nombre)
                        elif(len(colum.valor)==2):
                            errT=True;#variable error en p varchar(p)
                            if (isinstance(colum.valor[0],Operando_Numerico) and isinstance(colum.valor[1],Operando_Numerico)):
                                val1=resolver_operacion(colum.valor[0],ts)
                                val2=resolver_operacion(colum.valor[1],ts)
                                if(type(val1) == int and type(val2) == int):
                                    colAux.size=val1
                                    colAux.precision=val2
                                    errT=False#no existe error
                            if errT:
                                crearOK=False
                                msg='42601:el tipo '+colAux.tipo+' acepta enteros como parametro: '+colAux.nombre
                                agregarMensjae('error',msg,'42601')
                                Errores_Semanticos.append('Error Semantico: 42601:el tipo '+colAux.tipo+' acepta enteros como parametro: '+colAux.nombre)
                        else:
                            crearOK=False
                            msg='42601:el tipo '+colAux.tipo+' acepta maximo 2 parametro: '+colAux.nombre
                            agregarMensjae('error',msg,'42601')
                            Errores_Semanticos.append('Error Semantico: 42601:el tipo '+colAux.tipo+' acepta maximo 2 parametro: '+colAux.nombre)
                    else:
                        crearOK=False
                        msg='42601:el tipo '+colAux.tipo+' no acepta parametros:'+colAux.nombre
                        agregarMensjae('error',msg,'42601')
                        Errores_Semanticos.append('Error Semantico: 42601:el tipo '+colAux.tipo+' no acepta parametros:'+colAux.nombre)
                if(colum.zonahoraria!=False):
                    '''aca se debe verificar la zonahoraria es una lista'''
                    print('zonahoraria',colum.zonahoraria)
                if(colum.atributos!=False):
                    #aca se debe verificar la lista de atributos de una columna
                    for atributoC in colum.atributos :
                        if isinstance(atributoC, atributoColumna):
                            if(atributoC.default!=None):
                                if(colAux.default==None):
                                    T=resolver_operacion(atributoC.default,ts)#valor default
                                    T=validarTipo(colAux.tipo,T)
                                    if isinstance(atributoC.default,Operando_ID):
                                        crearOK=False
                                        msg='42804:no se puede asignar como default un ID col:'+colAux.nombre
                                        agregarMensjae('error',msg,'42804')
                                        Errores_Semanticos.append('Error Semantico: 42804:no se puede asignar como default un ID col:'+colAux.nombre)
                                    elif(T==None or isinstance(atributoC.default,Operando_ID)):
                                        T=''
                                        crearOK=False
                                        msg='42804:valor default != '+colAux.tipo+ ' en col:'+colAux.nombre
                                        agregarMensjae('error',msg,'42804')
                                        Errores_Semanticos.append('Error Semantico: 42804:valor default != '+colAux.tipo+ ' en col:'+colAux.nombre)
                                    colAux.default=T#guardar default
                                else:
                                    crearOK=False
                                    msg='42P16:atributo default repetido en Col:'+colAux.nombre
                                    agregarMensjae('error',msg,'42P16')
                                    Errores_Semanticos.append('Error Semantico: 42P16:atributo default repetido en Col:'+colAux.nombre)
                            elif(atributoC.constraint!=None):
                                if(colAux.constraint==None):
                                    colAux.constraint=atributoC.constraint#guardar constraint
                                else:
                                    crearOK=False
                                    msg='42P16:atributo constraint repetido en Col:'+colAux.nombre
                                    agregarMensjae('error',msg,'42P16')
                                    Errores_Semanticos.append('Error Semantico: 42P16:atributo constraint repetido en Col:'+colAux.nombre)
                            elif(atributoC.null!=None):
                                if(colAux.anulable==None):
                                    colAux.anulable=atributoC.null#guardar anulable
                                else:
                                    crearOK=False
                                    msg='42P16:atributo anulable repetido en Col:'+colAux.nombre
                                    agregarMensjae('error',msg,'42P16')
                                    Errores_Semanticos.append('Error Semantico: 42P16:atributo anulable repetido en Col:'+colAux.nombre)
                            elif(atributoC.unique!=None):
                                if(colAux.unique==None):
                                    colAux.unique=atributoC.unique#guardar unique
                                else:
                                    crearOK=False
                                    msg='42P16:atributo unique repetido en Col:'+colAux.nombre
                                    agregarMensjae('error',msg,'42P16')
                                    Errores_Semanticos.append('Error Semantico: 42P16:atributo unique repetido en Col:'+colAux.nombre)
                            elif(atributoC.primary!=None):
                                if(colAux.primary==None):
                                    colAux.primary=atributoC.primary#guardar primary
                                else:
                                    crearOK=False
                                    msg='42P16:atributo primary repetido en Col:'+colAux.nombre
                                    agregarMensjae('error',msg,'42P16')
                                    Errores_Semanticos.append('Error Semantico: 42P16:atributo primary repetido en Col:'+colAux.nombre)
                            elif(atributoC.check != None):
                                #el atributo check trae otra lista
                                print('check:',atributoC.check)
                                for exp in atributoC.check:
                                    print('resultado: ',resolver_operacion(exp,ts))
                listaColumnas.append(colAux)
    
    #validar foranea compuesta
    if(crearOK):
        listFK=[]
        #recorrer la tabla nueva para obtener las referencias
        for col in listaColumnas:
            if(col.foreign):
                if col.refence[0] not in listFK:
                    listFK.append(col.refence[0])
        lenFK=[]
        lenPK=[]
        
        #obtener longitud de foranea
        for tab in listFK:
            lenPK.append(0)
            lenFK.append(len(getpks(baseActiva,tab)))
        #obtener la longitud de foranea en tabla actual
        for col in listaColumnas:
            if(col.foreign):
                contFK=0
                for tab in listFK:
                    if(col.refence[0]==tab):
                        lenPK[contFK]+=1
                        break
                    contFK=contFK+1
        #validar #foraneas==#primarias en referencia
        pos=0
        while pos<len(listFK):
            if(lenFK[pos]!=lenPK[pos]):
                crearOK=False
                msg='42830:llave foranea debe ser compuesta ref:'+listFK[pos]
                agregarMensjae('error',msg,'42830')
                Errores_Semanticos.append('Error Semantico: 42830:llave foranea debe ser compuesta ref:'+listFK[pos])
            pos+=1
        #print('lista de Referencias:',listFK)
        #print('count pk en la  refe:',lenFK)
        #print('count fk tabla nueva:',lenPK)
    #crear la tabla
    if(crearOK):
        result=EDD.showTables(baseActiva)
        if(result!=None):
            for tab in result:
                if tab==nombreT:
                    msg='42P07:Error la tabla ya existe:'+nombreT
                    agregarMensjae('error',msg,'42P07')
                    Errores_Semanticos.append('Error Semantico: 42P07: Latabla '+ nombreT + ' ya existe')
                    crearOK=False
                    break
            if crearOK:
                EDD.createTable(baseActiva,nombreT,contC)
                insertartabla(listaColumnas,nombreT)
                msg='Todo OK'
                agregarMensjae('exito',msg,'')
                #agregar las llaves primarias
                x=0
                lis=[]
                for col in listaColumnas:
                    if(col.primary==True):
                        lis.append(x)
                    x=x+1
                if(len(lis)>0):
                    EDD.alterAddPK(baseActiva,nombreT,lis)

        else:
            msg='no existe la base de datos activa:'+baseActiva
            Errores_Semanticos.append('Error Semantico: no existe la base de datos activa:'+baseActiva)
            agregarMensjae('error',msg,'')

def crear_Type(instr,ts):
    nombreT=resolver_operacion(instr.nombre,ts).lower()
    msg='Creacion de Type: '+nombreT
    agregarMensjae('normal',msg,'')
    if baseActiva != "":
        result=EDD.showTables(baseActiva)
        cont=0
        flag=False
        lvalores=[]
        if instr.valores is not None:  
            if nombreT in result: # Repetido
                msg='42P07:Nombre repetido ...'
                agregarMensjae('error',msg,'42P07')
                Errores_Semanticos.append('Error Semantico: 42P07 Nombre repetido')
            else:
                for valor in instr.valores: # Verificacion tipos
                    val=resolver_operacion(valor,ts)
                    if isinstance(val, str):
                        lvalores.append(resolver_operacion(valor,ts))
                        cont=cont+1
                if cont != len(instr.valores):
                    msg='42804:No todos los valores son del mismo tipo'
                    agregarMensjae('error',msg,'42804')
                    Errores_Semanticos.append('Error Semantico: 42804:No todos los valores son del mismo tipo')
                else:
                    flag=True
            if(flag): # crea e inserta valores
                respuestatype=EDD.createTable(baseActiva,nombreT,cont)
                if respuestatype==0:
                    msg='Type registrado con exito'
                    agregarMensjae('exito',msg,'')
                    insertartabla(None,nombreT)
                    respuestavalores=EDD.insert(baseActiva,nombreT,lvalores)
                    if respuestavalores==0:
                        msg='con valores: '+str(lvalores)
                        agregarMensjae('exito',msg,'')
                    elif respuestavalores==1:
                        msg='42P16:Error insertando valores'
                        agregarMensjae('error',msg,'42P16')
                        Errores_Semanticos.append('Error Semantico: 42P16:Error insertando valores')
                    elif respuestavalores==2:
                        msg='Base de datos no existe'
                        agregarMensjae('error',msg,'')
                        Errores_Semanticos.append('Error Semantico: 42P16: La base de datos no existe')
                    elif respuestavalores==3:
                        msg='Type no encontrado'
                        agregarMensjae('error',msg,'')
                        Errores_Semanticos.append('Error Semantico: 42P01: Type no encontrado')
                elif respuestatype==1:
                    msg='Error al crear type'
                    agregarMensjae('error',msg,'42P16')
                    Errores_Semanticos.append('Error Semantico: 42P16: Error al crear type')
                elif respuestatype==2:
                    msg='Base de datos no existe'
                    agregarMensjae('error',msg,'')
                    Errores_Semanticos.append('Error Semantico: 42P01: La base de datos no existe')
                elif respuestatype==3:
                    msg='42P07:Nombre repetido ...'
                    agregarMensjae('error',msg,'42P07')
                    Errores_Semanticos.append('Error Semantico: 42P07: Nombre repetido')
    else:
        msg='No hay una base de datos activa'
        agregarMensjae('alert',msg,'')

def insertar_en_tabla(instr,ts):
    #pendiente
    # -Datos de tipo fecha
    # -size and precision para numeric
    # -check
    # -constraint
    insertOK=True
    ValInsert=[] #lista de valores a insertar
    nombreT=resolver_operacion(instr.nombre,ts).lower()
    msg='Insertado en Tabla:'+nombreT
    agregarMensjae('normal',msg,'')
    
    #-Tabla existente
    result=EDD.showTables(baseActiva)
    tablaInsert=None
    if(result!=None):
        if(nombreT not in result):
            insertOK=False
            msg='42P01'+':la tabla no existe en DB:'+baseActiva
            agregarMensjae('error',msg,'42P01')
            Errores_Semanticos.append('Error Semantico: 42P01'+':la tabla no existe en DB:'+baseActiva)
        else:
            tablaInsert = buscarTabla(baseActiva,nombreT)
    else:
        insertOK=False
        msg='no existe la base de datos activa:'+baseActiva
        agregarMensjae('error',msg,'')   
    #tabla no guardada en temporal
    if(tablaInsert == None):
        insertOK=False
        msg='No se encuentra en memoria los tipos de valor para esta tabla'
        agregarMensjae('error',msg,'')
    #-entrada solo con valores
    elif(instr.columnas==False):
        #crear la lista de columnas con NOne para EDD
        x=len(tablaInsert.atributos)
        while x>0:
            ValInsert.append(None)
            x=x-1
        #no exeder numero de columnas
        if(len(tablaInsert.atributos)>=len(instr.valores)):
            pos=0
            for col in instr.valores:
                #error al colocar un id
                valCOL=resolver_operacion(col,ts)#valor de la columna
                x=''
                try:
                    x=col.lower()
                except:
                    ''
                if(x=='null'):
                    valCOL=Operando_Booleano
                elif isinstance(col,Operando_ID):
                    #valores null
                    insertOK=False
                    msg='42804:no se pueden insertar valores de tipo ID:'+resolver_operacion(col,ts)
                    Errores_Semanticos.append('Error Semantico: 42804:no se pueden insertar valores de tipo ID:'+resolver_operacion(col,ts))
                    agregarMensjae('error',msg,'42804')
                else:
                    #validar el tipo de dato
                    valCOL=resolver_operacion(col,ts)#valor de la columna
                    T=tablaInsert.atributos[pos].tipo#Tipo de la columna
                    valCOL=(validarTipo(T,valCOL))
                    if(valCOL==None):
                        insertOK=False
                        msg='42804:La columna '+tablaInsert.atributos[pos].nombre+' es de tipo '+tablaInsert.atributos[pos].tipo
                        Errores_Semanticos.append('Error Semantico: 42804:La columna '+tablaInsert.atributos[pos].nombre+' es de tipo '+tablaInsert.atributos[pos].tipo)
                        agregarMensjae('error',msg,'42804')

                ValInsert[pos]=valCOL
                pos=pos+1
        else:
            insertOK=False
            msg='42601:la tabla solo posee '+str(len(tablaInsert.atributos))+' columas'
            Errores_Semanticos.append('Error Semantico: 42601:la tabla solo posee '+str(len(tablaInsert.atributos))+' columas')
            agregarMensjae('error',msg,'42601')            
    #-entrada con columnas y valores
    else:
        #crear la lista de columnas con NOne para EDD
        x=len(tablaInsert.atributos)
        while x>0:
            ValInsert.append(None)
            x=x-1
        #no exeder numero de columnas
        if(len(instr.columnas)==len(instr.valores)):
            #recorrer las columnas a insertar
            posVal=0
            for colList in instr.columnas:
                posEDD=0
                valCOL=None
                colEx=False
                #recorrer las columnas en la tabla
                for colTab in tablaInsert.atributos:
                    if(colTab.nombre==colList.lower()):
                        colEx=True
                        valCOL=resolver_operacion(instr.valores[posVal],ts)#valor de la columna
                        x=''
                        try:
                            x=instr.valores[posVal].lower()
                        except:
                            ''
                        if(x=='null'):
                            valCOL=Operando_Booleano
                        elif isinstance(instr.valores[posVal],Operando_ID):
                            #valores null
                            insertOK=False
                            msg='42804:no se pueden insertar valores de tipo ID:'+resolver_operacion(instr.valores[posVal],ts)
                            Errores_Semanticos.append('Error Semantico: 42804:no se pueden insertar valores de tipo ID:'+resolver_operacion(instr.valores[posVal],ts))
                            agregarMensjae('error',msg,'42804')
                        else:
                            #validar el tipo de dato
                            valCOL=resolver_operacion(instr.valores[posVal],ts)#valor de la columna
                            T=colTab.tipo#Tipo de la columna
                            valCOL=(validarTipo(T,valCOL))
                            if(valCOL==None):
                                insertOK=False
                                msg='42804:La columna '+colTab.nombre+' es de tipo '+colTab.tipo
                                Errores_Semanticos.append('Error semantico: 42804:La columna '+colTab.nombre+' es de tipo '+colTab.tipo)
                                agregarMensjae('error',msg,'42804')
                        #agregar a la lista de EDD
                        ValInsert[posEDD]=valCOL
                        break
                    #cambiar en la posicion lista EDD
                    posEDD=posEDD+1
                #error si no existe    
                if (colEx==False):
                    insertOK=False
                    msg='42703:la columna no existe:'+colList
                    Errores_Semanticos.append('Error semantico: 42703:la columna no existe:'+colList)
                    agregarMensjae('error',msg,'42703')
                #cambiar de valor
                posVal=posVal+1


        #error columnas!=valores
        else:
            insertOK=False
            msg='#columas no es igual a #valores, '+str(len(instr.columnas))+'!='+str(len(instr.valores))
            Errores_Semanticos.append('Error_Semantico: #columas no es igual a #valores, '+str(len(instr.columnas))+'!='+str(len(instr.valores)))
            agregarMensjae('error',msg,'')
            

    #validaciones parametros de columna
    if(insertOK):
        #-pendiente
        # check
        pos=0
        for col in tablaInsert.atributos:
            if(ValInsert[pos]==None):
                #verificar not null sin default
                if(col.anulable==False and col.default==None):
                    insertOK=False
                    msg='23502:columna no puede ser null:'+col.nombre
                    Error_Semantico.append('Error Semantico: 23502:columna no puede ser null:'+col.nombre)
                    agregarMensjae('error',msg,'23502')
                #agregar valores default
                elif(col.default!=None):
                    ValInsert[pos]=col.default
                #llaves primaria != null
                if(col.primary):
                    insertOK=False
                    msg='23502:llave primaria no puede ser null:'+col.nombre
                    Error_Semantico.append('Error Semantico: 23502:llave primaria no puede ser null:'+col.nombre)
                    agregarMensjae('error',msg,'23502')
                #llaves foranea != null
                if(col.foreign):
                    insertOK=False
                    msg='23502:llave foranea no puede ser null:'+col.nombre
                    Error_Semantico.append('Error Semantico: 23502:llave foranea no puede ser null:'+col.nombre)
                    agregarMensjae('error',msg,'23502')
            #insertaron null desde consola
            elif(ValInsert[pos]==Operando_Booleano):
                #cambiamos a none
                ValInsert[pos]=None
                if(col.anulable==False):
                    insertOK=False
                    msg='23502:columna no puede ser null:'+col.nombre
                    Error_Semantico.append('Error Semantico: 23502:columna no puede ser null:'+col.nombre)
                    agregarMensjae('error',msg,'23502')
                if(col.primary):
                    insertOK=False
                    msg='23502:llave primaria no puede ser null:'+col.nombre
                    Error_Semantico.append('Error Semantico: 23502:Primary key no puede ser null:'+col.nombre)
                    agregarMensjae('error',msg,'23502')
                #llaves foranea != null
                if(col.foreign):
                    insertOK=False
                    msg='23502:llave foranea no puede ser null:'+col.nombre
                    Error_Semantico.append('Error Semantico: 23502:Foreing key no puede ser null:'+col.nombre)
                    agregarMensjae('error',msg,'23502')
            pos=pos+1
    #validaciones llaves foraneas
    if(insertOK):
        
        #obtener las tablas referenciadas
        listTabRef=[]#guarda las tablas referenciadas 
        listColFK=[]#guarda las columnas primarias de cada tabla referenciada
        listValFK=[]#guarda los valores a insertar en esas columnas
        listPosFk=[]#guarda la pos[x] de la tabla referenciada para los valores
        for col in tablaInsert.atributos:
            if (col.foreign and col.refence[0] not in listTabRef):
                listTabRef.append(col.refence[0])
        #obtener los valores para cada ref
        for x in listTabRef:
            colAux=[]
            valAux=[]
            posAux=[]
            pos=0
            for col in tablaInsert.atributos:
                if(col.foreign and col.refence[0]==x):
                    colAux.append(col.refence[1])
                    valAux.append(ValInsert[pos])
                pos+=1
            listColFK.append(colAux)
            listValFK.append(valAux)
            #obtener la posicion segun la tabla original
            result=buscarTabla(baseActiva,x)
            if(result==None):
                insertOK=False
                msg='la tabla de referencia no existe:'+x
                agregarMensjae('error',msg,'')
            else:
                
                for i in colAux:
                    pos=0
                    for val in result.atributos:
                        if(val.nombre==i):
                            posAux.append(pos)
                            break
                        pos+=1
            listPosFk.append(posAux)
        #validar si existen los valores
        contx=0
        for x in listTabRef:
            result=EDD.extractTable(baseActiva,x)
            if(result==None):
                insertOK=False
                msg='la tabla de referencia no existe:'+x
                agregarMensjae('error',msg,'')
            else:
                #recorrer tabla fila por fila
                pkExiste=False
                for y in result:
                    pos=0
                    contEx=0
                    #verificar si cumple toda la llave compuesta
                    for d in listValFK[contx]:
                        if(y[listPosFk[contx][pos]]==d):
                            contEx+=1
                        pos+=1
                    if(contEx==len(listValFK[contx])):
                        pkExiste=True
                        break

                if(pkExiste==False):
                    insertOK=False
                    msg='23503:no existe la llave foranea'+str(listValFK[contx])+' en '+x 
                    Error_Semantico.append('Error Semantico: 23503:no existe la llave foranea'+str(listValFK[contx])+' en '+x)
                    agregarMensjae('error',msg,'23503')
            contx+=1

        #print(' Tablas Referenciadas  :',listTabRef)
        #print(' Columnas de Referencia:',listColFK)
        #print('     valores a insertar:',listValFK)
        #print('posicion tabla original:',listPosFk)
        


    #validar size, presicion
    if(insertOK):
        pos=0
        for col in tablaInsert.atributos:
            val=validarSizePres(col.tipo,ValInsert[pos],col.size,col.precision)
            if(val==False):
                insertOK=False
                msg='22001:valor muy grande para la columna:'+col.nombre
                Error_Semantico.append('Error semantico: 22001:valor muy grande para la columna:'+col.nombre)
                agregarMensjae('error',msg,'22001')
            pos=pos+1
    #realizar insert con EDD
    if(insertOK):
        #llamar metodo insertar EDD
        # 0 operación exitosa, 
        # 1 error en la operación, 
        # 2 database no existente, 
        # 3 table no existente, 
        # 4 llave primaria duplicada, 
        # 5 columnas fuera de límites
        result=EDD.insert(baseActiva,nombreT,ValInsert)
        if(result==0):
            msg='valores insertados:'+str(ValInsert)
            agregarMensjae('exito',msg,'')
            #agregar mensaje Tabla simbolos
            agregarTSRepor('INSERT','','','','')
            #lista de valores
            if(instr.columnas==False):
                pos=0
                #recorrer los valores
                for val in instr.valores:
                    tip=tablaInsert.atributos[pos].tipo
                    ident=tablaInsert.atributos[pos].nombre
                    agregarTSRepor('',ident,tip,nombreT,'1')
                    pos+=1
            #listado de columnas y valores
            else:
                #recorrer las columnas a insertar
                for colList in instr.columnas:
                    #recorrer las columnas en la tabla
                    for colTab in tablaInsert.atributos:
                        if(colTab.nombre==colList.lower()):
                            tip=colTab.tipo
                            ident=colTab.nombre
                            agregarTSRepor('',ident,tip,nombreT,'1')
                            break;
            
        elif (result==1):
            msg='Error en EDD:'
            agregarMensjae('error',msg,'')
        elif (result==2):
            msg='no existe DB:'+baseActiva
            agregarMensjae('error',msg,'')
        elif (result==3):
            msg='42P01:tabla no existe:'+nombreT
            agregarMensjae('error',msg,'42P01')
            Error_Semantico.append('Error Semantico: 42P01:tabla no existe:'+nombreT)
        elif (result==4):
            msg='23505:llave primaria duplicada:'
            Error_Semantico.append('Error Semantico: 23505:llave primaria duplicada:')
            agregarMensjae('error',msg,'23505')
        elif (result==5):
            msg='columnas faltantes para EDD'
            agregarMensjae('error',msg,'')

def update_register(exp,llaves,ts,baseAc,tablenm,nameC,valor):
    pk_value = llaves_tabla(exp,llaves,ts)
    pk_index = indice_llaves(llaves,baseAc,tablenm)
    pk_value = list(filter(None, pk_value))
    if pk_value is not None:
        col = {}
        registros=EDD.extractTable(baseAc,tablenm) 
        for registro in registros:
            atributosact=[]
            if len(pk_value) != len(pk_index):
                if any(item in registro for item in pk_value):
                    for i in pk_index:
                        atributosact.append(registro[i])
                    if len(atributosact) > 0:
                        col[indiceColum(baseAc,tablenm,nameC)]=valor
                        respuesta=EDD.update(baseAc,tablenm,col,atributosact)
                        if respuesta==0:
                            agregarMensjae('exito','Registro actualizado.','')
                        elif respuesta==1:
                            agregarMensjae('error','Error en actualizar registro','')
                        elif respuesta==2:
                            agregarMensjae('error','Base de datos no existe','')
                        elif respuesta==3:
                            agregarMensjae('error','42P01:Tabla '+tablenm+' no registrada','42P01')
                            Error_Semantico.append('Error semantico: 42P01:Tabla '+tablenm+' no registrada')
            else:
                if all(item in registro for item in pk_value):
                    for i in pk_index:
                        atributosact.append(registro[i])
                    if len(atributosact) > 0:
                        col[indiceColum(baseAc,tablenm,nameC)]=valor
                        respuesta=EDD.update(baseAc,tablenm,col,atributosact)
                        if respuesta==0:
                            agregarMensjae('exito','Registro actualizado.','')
                        elif respuesta==1:
                            agregarMensjae('error','Error en actualizar registro','')
                        elif respuesta==2:
                            agregarMensjae('error','Base de datos no existe','')
                        elif respuesta==3:
                            agregarMensjae('error','42P01:Tabla '+tablenm+' no registrada','42P01')
                            Error_Semantico.append('Error semantico: 42P01:Tabla '+tablenm+' no registrada')
    else:
        agregarMensjae('error','No se encontro la llave primaria','')

def actualizar_en_tabla(instr,ts):
    # pendiente completar condicion where 
    # una key en where ok o keys en where ok pero otras condiciones aun no
    tipostring=['character varying','character','char','varchar','text','date','timestamp','time','interval']
    tiponum=['smallint','integer','bigint','decimal','numeric','real','double precision','money','boolean']
    nombreT=resolver_operacion(instr.nombre,ts)
    primarias=getpks(baseActiva,nombreT)
    agregarMensjae('normal','Actualizar tabla '+nombreT,'')
    if baseActiva != "": # base seleccionada
        resultdb=EDD.showTables(baseActiva)
        if nombreT in resultdb: # tabla encontrada
            cabeceras = buscarTabla(baseActiva,nombreT)
            if cabeceras is not None:
                for colum in cabeceras.atributos:
                    if colum is not None:
                        for valor in instr.valores:
                            name=resolver_operacion(valor.nombre,ts)
                            value=resolver_operacion(valor.valor,ts)
                            if colum.nombre == name: # columna encontrada
                                if isinstance(value, str): # string
                                    if colum.tipo in tipostring: # update normal
                                        if colum.size != "":
                                            if len(value)<int(colum.size):
                                                 update_register(instr.condicion,primarias,ts,baseActiva,nombreT,name,value)
                                            else:
                                                agregarMensjae('error','22001:Valor muy grande para tipo '+colum.tipo+'('+str(colum.size)+')','22001')
                                                Error_Semantico.append('Error semantico: 22001:Valor muy grande para tipo '+colum.tipo+'('+str(colum.size)+')')
                                        else: 
                                            update_register(instr.condicion,primarias,ts,baseActiva,nombreT,name,value)
                                    elif colum.tipo in tiponum: # error update
                                        agregarMensjae('error','42804:datatype_mismatch (no coincide el tipo de datos)','42804')
                                        Error_Semantico.append('Error semantico: 42804:datatype_mismatch (no coincide el tipo de datos)')
                                else: # numero
                                    if colum.tipo in tipostring: # casteo y update
                                        if colum.size != "":
                                            if len(str(value)) < int(colum.size):
                                                update_register(instr.condicion,primarias,ts,baseActiva,nombreT,name,str(value))
                                            else:
                                                agregarMensjae('error','22001:Valor muy grande para tipo '+colum.tipo+'('+str(colum.size)+')','22001')
                                                Error_Semantico.append('Error Semantico: 22001:Valor muy grande para tipo '+colum.tipo+'('+str(colum.size)+')')
                                        else:
                                            update_register(instr.condicion,primarias,ts,baseActiva,nombreT,name,value)
                                    elif colum.tipo in tiponum: # update normal
                                        update_register(instr.condicion,primarias,ts,baseActiva,nombreT,name,value)
        else:
            agregarMensjae('error','42P01:Tabla '+nombreT+' no registrada','42P01')
            Error_Semantico.append('Error semantico: 42P01:Tabla '+nombreT+' no registrada')
    else:
        agregarMensjae('alert','No hay una base de datos activa','')

def eliminar_de_tabla(instr,ts):
    #pendiente completar condicion where
    nombreT=resolver_operacion(instr.nombre,ts)
    primarias=getpks(baseActiva,nombreT)
    agregarMensjae('normal','Eliminar tabla '+nombreT,'')
    if baseActiva != "": # base seleccionada
        resultdb=EDD.showTables(baseActiva)
        if nombreT in resultdb: # tabla encontrada
            pk_value = llaves_tabla(instr.condicion,primarias,ts)
            pk_index = indice_llaves(primarias,baseActiva,nombreT)
            pk_value = list(filter(None, pk_value))
            if pk_value is not None:
                registros=EDD.extractTable(baseActiva,nombreT) 
                for registro in registros:
                    atributodel=[]
                    if len(pk_value) != len(pk_index):
                        if any(item in registro for item in pk_value):
                            for i in pk_index:
                                atributodel.append(registro[i])
                        if len(atributodel) > 0:       
                            respuesta=EDD.delete(baseActiva,nombreT,atributodel)
                            if respuesta==0:
                                agregarMensjae('exito','Registro eliminado.','')
                            elif respuesta==1:
                                agregarMensjae('error','Error en eliminar registro','')
                            elif respuesta==2:
                                agregarMensjae('error','Base de datos no existe','')
                            elif respuesta==3:
                                agregarMensjae('error','42P01:Tabla '+nombreT+' no registrada','42P01')
                                Error_Semantico.append('Error semantico: 42P01:Tabla '+nombreT+' no registrada')
                    else:
                        if all(item in registro for item in pk_value):
                            for i in pk_index:
                                atributodel.append(registro[i])
                        if len(atributodel) > 0:       
                            respuesta=EDD.delete(baseActiva,nombreT,atributodel)
                            if respuesta==0:
                                agregarMensjae('exito','Registro eliminado.','')
                            elif respuesta==1:
                                agregarMensjae('error','Error en eliminar registro','')
                            elif respuesta==2:
                                agregarMensjae('error','Base de datos no existe','')
                            elif respuesta==3:
                                agregarMensjae('error','42P01:Tabla '+nombreT+' no registrada','42P01')
                                Error_Semantico.append('Error semantico: 42P01:Tabla '+nombreT+' no registrada')
            else:
                agregarMensjae('error','no se encontro pk','')          
        else:
            agregarMensjae('error','42P01:Tabla '+nombreT+' no registrada','42P01')
            Error_Semantico.append('Error semantico: 42P01:Tabla '+nombreT+' no registrada')
    else:
        agregarMensjae('alert','No hay una base de datos activa','')

#EMPIEZA MIO --------------------------------------------




def AlterDBF(instr,ts):

    print("nombre:",instr.Id,"Tipo:",instr.TipoCon,"Valor:",instr.valor)
    outputTxt=""
    #Nombre de la base de datos
    NombreBaseDatos= instr.Id
    #Instruccion RENAME O OWNER
    TipoOperacion= (instr.TipoCon).upper()
    #Valor de la operacion, ID , CURREN_USER O SESSION_USER
    ValorInstruccion=instr.valor

    if TipoOperacion=="RENAME":
        retorno=EDD.alterDatabase(NombreBaseDatos, ValorInstruccion)

        if retorno==0:
            Rename_Database(NombreBaseDatos,ValorInstruccion)
            outputTxt='La base de datos Old_Name: '+NombreBaseDatos +', New_Name: '+ValorInstruccion 
            outputTxt+='\n> se ha renombrado exitosamente '
            agregarMensjae('normal',outputTxt,"")
            print ("La base de datos se ha renombrado exitosamente")
        elif retorno==1:
            outputTxt='Hubo un error durante la modificacion de la bd  '
            agregarMensjae('normal',outputTxt,"")
            print ("Hubo un error durante la modificacion de la bd")  
        elif retorno==2:
            outputTxt='La base de datos :'+NombreBaseDatos +' ,no existe '
            agregarMensjae('normal',outputTxt,"")
            print ("La base de datos no existe")
        elif retorno==3:
            outputTxt='El nombre de la base de datos :'+ValorInstruccion +' ,ya esta en uso '
            agregarMensjae('normal',outputTxt,"")
            print ("El nombre de la bd ya esta en uso")
            
    else:
        #reconoce OWNER 
        if ValorInstruccion.upper()=="CURRENT_USER":
            outputTxt='Se ha ejecutado con exito la modificacion DB CURRENT_USER'
            agregarMensjae('normal',outputTxt,"")
        elif ValorInstruccion.upper()=="SESSION_USER":
            outputTxt='Se ha ejecutado con exito la modificacion DB SESSION_USER'
            agregarMensjae('normal',outputTxt,"")
        else:
            outputTxt='Se ha ejecutado con exito la modificacion DB ID'
            agregarMensjae('normal',outputTxt,"")





#Empieza alter TABLE

def AlterTBF(instr,ts):

    #global outputTxt
    print("nombreT:",instr.Id,"CuerpoT:",instr.cuerpo)
    print(instr)
    #TABLA A ANALIZAR
    NombreTabla=instr.Id
    global listaTablas
    #RENAME , ALTER_TABLE_SERIE,   ALTER_TABLE_DROP,   ALTER_TABLE_ADD
    ObjetoAnalisis=instr.cuerpo

    global baseActiva

    #ANALISIS ALTER RENAME
    if isinstance(ObjetoAnalisis,ALTERTBO_RENAME ):
        #Primer ID
        ID1=ObjetoAnalisis.Id1
        #Segundo ID
        ID2=ObjetoAnalisis.Id2
        #Operacion Column ,Constraint o nula
        OPERACION=ObjetoAnalisis.operacion

        cuerpo_ALTER_RENAME(NombreTabla,ObjetoAnalisis,ID1,ID2,OPERACION)
        #FALTA RENAME CONSTRAINT
        #RENOMBRAR LLAVES FORANEAS Y REFERENCES
       
    #ANALISIS ALTER DE ALTERS
    elif isinstance(ObjetoAnalisis,ALTERTBO_ALTER_SERIE ):

        
        #Lista de Alter's
        Lista_Alter = ObjetoAnalisis.listaval
        
        Cuerpo_ALTER_ALTER(Lista_Alter,NombreTabla,instr,ts)
        #CASTEAR INFO DE LA TABLA SI ES QUE SE DEBE CASTEAR

    #ANALISIS ALTER DROP
    elif isinstance(ObjetoAnalisis,ALTERTBO_DROP ):
        #Definicion de Instruccion  COLUMN , CONSTRAINT o nula
        INSTRUCCION=ObjetoAnalisis.instruccion
        #Identificador 
        ID=ObjetoAnalisis.id
        Cuerpo_ALTER_DROP(NombreTabla,ObjetoAnalisis,INSTRUCCION,ID)
        #FALTA DROP CONSTRAINT
        #RENOMBRAR LLAVES FORANEAS Y REFERENCES SI SE ELIMINA O DEJAR ASI

        
    #ANALISIS ALTER ADD
    elif isinstance(ObjetoAnalisis,ALTERTBO_ADD ):
        '''alttbadd : ADD ID tipo valortipo
                    | ADD COLUMN ID tipo valortipo
                    | ADD CONSTRAINT ID alttbadd2
                    | ADD alttbadd2  '''

        #Identificador
        ID=ObjetoAnalisis.id

        #Etiqueta tipo de dato y su especificacion
        TIPO=ObjetoAnalisis.tipo
        VALORTIPO=ObjetoAnalisis.valortipo

        #Recupera prefijo column constraint
        INSTRUCCION=ObjetoAnalisis.instruccion

        #Recupera posible multiple constraint
        Obj_Extras=ObjetoAnalisis.extra

        #Para reposicionar valores
        #if INSTRUCCION.upper()=="C" or INSTRUCCION.upper()=="CONSTRAINT":
        #elif INSTRUCCION.upper()=="ID" or INSTRUCCION.upper()=="COLUMN":
        #else:


        if INSTRUCCION.upper()=="C" or INSTRUCCION.upper()=="CONSTRAINT":
            ' '
            #si trae id agrgar nombre
            #sino es 0
            #viene lista de constraints
            tablab= copy.deepcopy(Get_Table(NombreTabla))

            if len(tablab)>0:
                #encontro la tabla
                #comprueba que el nombre columna exista en la tabla
                Constraint_Resuelve(Obj_Extras,tablab,ID)
            else:
                print("la tabla no existe en la base de datos")




        elif INSTRUCCION.upper()=="ID" or INSTRUCCION.upper()=="COLUMN":
            tablab= copy.copy(Get_Table(NombreTabla))

            if len(tablab)>0:
                #encontro la tabla
                #comprueba que el nombre columna no exista en la tabla
                columnab=copy.copy(Get_Column(ID,(tablab[0]).atributos,tablab[2]))
                if len(columnab)==0:
                    #no existe la columna en tabla , la creara
                    retor=1
                    try:
                        #VERFICAR SI DEFAULT ALGUN VALOR XXXXX
                        retor=EDD.alterAddColumn(baseActiva,NombreTabla,None)
                    except:
                        ' '
                        print("ERROR EN edd")
                    if retor==0:
                        #Si se agrego' la columna a la tabla, crea el header COLUMNA
                        col_new= Columna_run()

                        col_new.nombre=ID
                        col_new.tipo=TIPO
                        col_new.constraint=constraint_name()

                        if (VALORTIPO!="") and (VALORTIPO!=None) and (VALORTIPO!=0):
                            valor= resolver_operacion(VALORTIPO[0],ts)
                            if valor!=None:
                                col_new.size=valor
                            else:
                                col_new.size=None
                        else:
                             col_new.size=None

                        # ((indexo la tabla ).listacolumnas)
                        cambio=((listaTablas[tablab[1]]).atributos)
                        cambio+=[col_new]
                    else:
                        ' '
                    #ciclo mensajes
                    Msg_Alt_Add_Column(NombreTabla,ID,retor)
                else:
                    ' '
                    #existe la columna no la crea
                    print("la columna YA existe")
                    outputTxt='La columna:'+ID+" ya Existe en la tabla:"+NombreTabla
                    agregarMensjae('normal',outputTxt,"")
            else:
                ' '
                #la tabla no existe
                print("la tabla no existe")
                outputTxt='La tabla:'+NombreTabla+" no Existe"
                agregarMensjae('normal',outputTxt,"")
        else:
            ' '
            print("Operacion desconocida")
            




def Table_Reensable_H(tablaB,indice):
    #tablab es un objeto tipo Tabla
    #indice posicion de columna a eliminar

    #array de objeto tipo columna
    columnas_tem=copy.copy(tablaB.atributos)

    print("antes:",columnas_tem,"longi:",len(columnas_tem))
    nueva_columna=[]
    contadort=0
    for c_t in columnas_tem:
        if contadort!=indice:
            nueva_columna+=[c_t]

        contadort+=1
    print("des:",columnas_tem,"longi:",len(columnas_tem))

    copia_tablaB=copy.copy(tablaB)
    copia_tablaB.atributos=nueva_columna

    return copia_tablaB





def Mostrar_TB(operacion,ts):
    listaR=EDD.showTables(baseActiva)
    try:
        outputTxt="Nombre BD: "+baseActiva
        for val in listaR:
            outputTxt+='\n> Tabla Name: '+val
        agregarMensjae('normal',outputTxt,"")
    except:
        if listaR==None:
            outputTxt='La base de datos no Existe, ShowTables'
            agregarMensjae('normal',outputTxt,"")
        else:
            outputTxt='La tabla no existe en la bd, ShowTables'
            agregarMensjae('normal',outputTxt,"")




#19/12/20
#retorna tabla cabecera mas cuerpo , lista
def Get_Table(nameTable):
    global baseActiva
    global listaTablas
    TablaC=[]
    posicionH=0
    #[Cabecera ,Posicion_Header, Cuerpo ]

    #busca primero cabecera
    for tablaT in listaTablas:
        if tablaT.nombre==nameTable and tablaT.basepadre==baseActiva:
            TablaC+=[tablaT]
            TablaC+=[posicionH]
            break
        posicionH+=1

    #si encuentra la cabecera tabla , procede a buscar el cuerpo
    if len(TablaC)>0:
        try:
            contenido=EDD.extractTable(baseActiva,nameTable)
            print(contenido)
            if contenido!=None:
                #Si no da error , agrega la tabla fisica
                TablaC=TablaC+[contenido]
            else:
                vacio=[]
                TablaC=TablaC+[vacio]
        except:
            vacio=[]
            TablaC=TablaC+[vacio]
            
            #TablaC=[]
            #print ("error proc busqueda")
            #error al procesar la busqueda

    return TablaC


#recibe parametro lista de Objeto tabla y nombre de la columna
def Get_Column(name_c,tabla_H_List,tabla_C_List):
    #tabla_H_List es lista de objetos Columna_run
    vacio=[]
    retorna=[]
    contador=0
    print(tabla_H_List)
    for col_temp in tabla_H_List:

        if col_temp.nombre==name_c:
            #guarda posicion columna y cabecera columna
            retorna+=[copy.copy(col_temp)]
            retorna+=[contador]
            break
        contador+=1

    #construye columna valores
    col_Ret=[]
    print(contador)
    
    if len(retorna)>0:
        for row_t in tabla_C_List:
            print(row_t)
            print(contador)
            col_Ret+=[row_t[contador]]
        #guarda registros Columna
        retorna+=[col_Ret]
    
    #Estructura Retorno
    #[Objeto_Columna,posicion,[Registros]]
    return retorna

def Rename_Database(nombreOld,nombreNew):
    
    global listaTablas
    tablas=copy.copy(listaTablas)

    for tab in tablas:
        if tab.basepadre==nombreOld:
            tab.basepadre=nombreNew
    
    listaTablas=copy.copy(tablas)




#Objeto analiza constraint individual
def Constraint_Resuelve(Obj_Add_Const,tablab,ID):

    #obtiene instrucion: check unique primary foranea
    Uptemp=(Obj_Add_Const.instruccion).upper()
    #obtiene contenido,lista de columnas
    contenido=Obj_Add_Const.contenido
    #obtiene ID tabla Referencias
    TabIDRef=Obj_Add_Const.id
    #obtiene Contenido Referencias ,lista de columnas
    contenido2=Obj_Add_Const.contenido2

    #servira para escribir los cambios temporalmente
    tab_Temp=copy.deepcopy(tablab)



    #Revisa que No exista el nombre constraint si se fuera a poner
    reviConsName=True
    if ID!=0 and ID!=None and ID!="":
        reviConsName=Ver_Exist_Name_Const(ID,(tab_Temp[0]).atributos)
    else:
        reviConsName=False

    #NOTA SI SE ELIMINA alguno INDIVIDUAL Nose 

    #Construye el id si no tiene ID
    new_id=""
    for con in contenido:
        if new_id=="":
            new_id=new_id+con
        else:
            new_id=new_id+"_"+con


    #INCIA LA VERIFICACION DE TIPO CONSTRAINT
    if  Uptemp=="CHECK" and not(reviConsName):
        ' '
    elif Uptemp =="UNIQUE" and  not(reviConsName):

        existenCols=0
        #Busca cada columna del query , en las columnas de la Tabla
        for col_rev in contenido:
            subCont=0
            existeC=0
            for COL_T in ((tablab[0]).atributos):
                if col_rev == COL_T.nombre:
                    #((busca e indexa tabla).get columns List)[indexa col].unique=asigna
                    #(((listaTablas[tablab[1]]).atributos)[subCont]).unique='True'
                    
                    
                    #Obtiene info de la columna para verificar que Registro sean unicos
                    columnab=copy.copy(Get_Column(col_rev,((tablab[0]).atributos),tablab[2]))


                    #Busca columnas Repetidos en el query 
                    DatoRepetidoQuery=B_Repetidos(contenido)

                    #Busca Regisros Repetidos en la columna 
                    DatoRepetido=B_Repetidos(columnab[2])
                    #obitiene Nombre UNIQUE de esa columna
                    #para ver que sea vacio , sino NO MODIFICA
                    pre_con=((((tablab[0]).atributos)[subCont]).constraint).unique
                    print("BOOL ASDF:",(pre_con==None))
                    print(pre_con)

                    if (ID!=0 and ID!=None and ID!="") and (pre_con==None) and not(DatoRepetido) and not(DatoRepetidoQuery):
                        print("INGRESO ID TIENE:")
                        #SI UNIQUE NO HA SIDO ASIGNADO, y SI  le puso ID , y si NO REGISTROS REPETIDOS
                        ((((tab_Temp[0]).atributos)[subCont]).constraint).unique=ID
                        #usara el objeto tempral tablab=tab_Temp ,
                        #Asigna el valor Verdadero
                        (((tab_Temp[0]).atributos)[subCont]).unique='True'
                    elif (ID==0 or ID==None or ID=="") and pre_con==None and not(DatoRepetido) and not(DatoRepetidoQuery):
                        print("INGRESO NO ID TIENE:")
                        #SI UNIQUE NO HA SIDO ASIGNADO, y NO se le puso ID , y si NO REGISTROS REPETIDOS
                        #ID= concatena columnas col_col2_col3_etc
                        ((((tab_Temp[0]).atributos)[subCont]).constraint).unique=new_id
                        #Asigna el valor Verdadero
                        (((tab_Temp[0]).atributos)[subCont]).unique='True'
                    else:
                        print("Unique Error")
                        existenCols=0
                        break

                    #AREA DE MENSAJES de validaciones
                    Msg_Alt_Add_CONSTRAINT(pre_con,DatoRepetido,columnab)

                    existeC=1
                    existenCols=copy.deepcopy(existeC)
                    break
                subCont+=1
            else:
                #Transfiere el valor, para no guardar informacion, o si guardarla 
                #existenCols=copy.deepcopy(existeC)
                if existeC==0:
                    print("La columna:",col_rev," no existe en la tabla")
                    break
                
                

        print("existecols:",existenCols)
        #((((tab_Temp[0]).atributos)[0]).constraint).unique='23'
        print(((((tab_Temp[0]).atributos)[0]).constraint).unique)
        if existenCols==1:
            #procede a actualizar la tabla
            pre_con=((((tab_Temp[0]).atributos)[0]).constraint).unique
            pre_con1=((((tablab[0]).atributos)[1]).constraint).unique
            pre_con2=((((tablab[0]).atributos)[2]).constraint).unique
            pre_con3=((((tab_Temp[0]).atributos)[3]).constraint).unique
            pre_con4=((((tablab[0]).atributos)[4]).constraint).unique
            print("pre_con:",pre_con,"-")
            print("pre_con1:",pre_con1)
            print("pre_con2:",pre_con2)
            print("pre_con3:",pre_con3)
            print("pre_con4:",pre_con4)
            listaTablas[tablab[1]]=copy.deepcopy(tab_Temp[0])
            
            ' '
        else:
            print("Error no se puede guardar la tabla constraint")


    elif Uptemp =="PRIMARY" and not(reviConsName):
        existenCols=0
        #Busca cada columna del query , en las columnas de la Tabla
        for col_rev in contenido:
            subCont=0
            existeC=0
            for COL_T in ((tablab[0]).atributos):
                if col_rev == COL_T.nombre:
                    #((busca e indexa tabla).get columns List)[indexa col].unique=asigna
                    #(((listaTablas[tablab[1]]).atributos)[subCont]).unique='True'
                    
                    
                    #Obtiene info de la columna para verificar que Registro sean unicos
                    columnab=copy.copy(Get_Column(col_rev,((tablab[0]).atributos),tablab[2]))

                    #Busca columnas Repetidos en el query 
                    DatoRepetidoQuery=B_Repetidos(contenido)

                    #Busca nulos en Registros
                    nulosR=B_Nulos(columnab[2])

                    #Busca Regisros Repetidos en la columna 
                    DatoRepetido=B_Repetidos(columnab[2])
                    #obitiene Nombre UNIQUE de esa columna

                    #para No debe haber otra primary key 
                    pre_con=True
                    for cb in ((tablab[0]).atributos):
                        if ((cb.primary))!=None:
                            pre_con=False
                            break

                    #pre_con=((((tablab[0]).atributos)[subCont]).constraint).primary
                    print("BOOL ASDF:",(pre_con==None))
                    print(pre_con)

                    if (ID!=0 and ID!=None and ID!="") and (pre_con) and not(DatoRepetido) and not(DatoRepetidoQuery) and not(nulosR):
                        print("INGRESO ID TIENE:")
                        #SI UNIQUE NO HA SIDO ASIGNADO, y SI  le puso ID , y si NO REGISTROS REPETIDOS
                        ((((tab_Temp[0]).atributos)[subCont]).constraint).primary=ID
                        #usara el objeto tempral tablab=tab_Temp ,
                        #Asigna el valor Verdadero
                        (((tab_Temp[0]).atributos)[subCont]).primary='True'
                        (((tab_Temp[0]).atributos)[subCont]).unique='True'
                        (((tab_Temp[0]).atributos)[subCont]).anulable='False'

                    elif (ID==0 or ID==None or ID=="") and (pre_con) and not(DatoRepetido) and not(DatoRepetidoQuery) and not(nulosR):
                        print("INGRESO NO ID TIENE:")
                        #SI UNIQUE NO HA SIDO ASIGNADO, y NO se le puso ID , y si NO REGISTROS REPETIDOS
                        #ID= concatena columnas col_col2_col3_etc
                        ((((tab_Temp[0]).atributos)[subCont]).constraint).primary=new_id
                        #Asigna el valor Verdadero
                        (((tab_Temp[0]).atributos)[subCont]).primary='True'
                        (((tab_Temp[0]).atributos)[subCont]).unique='True'
                        (((tab_Temp[0]).atributos)[subCont]).anulable='False'
                    else:
                        print("Unique Error")
                        existenCols=0
                        break

                    #AREA DE MENSAJES de validaciones
                    Msg_Alt_Add_CONSTRAINT(pre_con,DatoRepetido,columnab)

                    existeC=1
                    existenCols=copy.deepcopy(existeC)
                    break
                subCont+=1
            else:
                #Transfiere el valor, para no guardar informacion, o si guardarla 
                #existenCols=copy.deepcopy(existeC)
                if existeC==0:
                    print("La columna:",col_rev," no existe en la tabla")
                    break
                
                

        print("existecols:",existenCols)
        #((((tab_Temp[0]).atributos)[0]).constraint).unique='23'
        print(((((tab_Temp[0]).atributos)[0]).constraint).primary)
        if existenCols==1:
            #procede a actualizar la tabla
            pre_con=((((tab_Temp[0]).atributos)[0]).constraint).primary
            pre_con1=((((tablab[0]).atributos)[1]).constraint).primary
            pre_con2=((((tablab[0]).atributos)[2]).constraint).primary
            pre_con3=((((tab_Temp[0]).atributos)[3]).constraint).primary
            pre_con4=((((tablab[0]).atributos)[4]).constraint).primary
            print("pre_con:",pre_con,"-")
            print("pre_con1:",pre_con1)
            print("pre_con2:",pre_con2)
            print("pre_con3:",pre_con3)
            print("pre_con4:",pre_con4)
            listaTablas[tablab[1]]=copy.deepcopy(tab_Temp[0])
            
            ' '
        else:
            print("Error no se puede guardar la tabla constraint")



    elif Uptemp =="FOREIGN" and not(reviConsName):
        ' '
        #debe cumplir:
        #ser del mismo tipo
        #ser primary key
        #si hay informacion en la tabla que queremos asignarle la llave foranea
        #debemos ver si la informacion coincide con las llaves foraneas declaradas
        #si no tiene ninguna foranea no se puede
        #y si algun registro Padre no coincide con las foraneas tampoco
        #NOSE si vincula multiples primary keys

        #TabIDRef=Obj_Add_Const.id
        #obtiene Contenido Referencias ,lista de columnas
        #contenido2=Obj_Add_Const.contenido2

        #Construye el id si no tiene ID
        new_id=""
        for con in contenido:
            if new_id=="":
                new_id=new_id+con
            else:
                new_id=new_id+"_"+con




        #Longitud columnas Padre
        longi1=len(contenido)
        #Longitud columnas Reference Foranea
        longi2=len(contenido2)
        #Comparacion Longitudes
        lonI=(longi1==longi2)


        #valores tabla padre
        tablaP=copy.deepcopy(tablab)
        #valores tabla foranea, verifica que exista a traves de esta parte
        tablaF=copy.deepcopy(Get_Table(TabIDRef))
        print(TabIDRef)
        #Comparacion Existen las 2 tablas
        ExiT=(len(tablaP)>0) and (len(tablaF)>0)


        #Tabla en donde Guardaremos la info terporalmente
        tabla_Temp=copy.deepcopy(tablab[0])


        #verifica columnas Repetidas
        DatRepQuery1=B_Repetidos(contenido)
        #verifica columnas Repetidas
        DatRepQuery2=B_Repetidos(contenido2)
        #compara que no Repetidos en ambas filas columnas
        RepQuery=(not(DatRepQuery1)) and (not(DatRepQuery2))

        #compara que nombre de tablas Diferentes
        NomTabDif=False
        if len(tablaF)>0:
            NomTabDif=(((tablaF[0]).nombre)!=((tablaP[0]).nombre))

        GuardaF=False

        veriConstName=False
        if (ID!=0 and ID!=None and ID!=""):
            veriConstName=Ver_Exist_Name_Const(ID,(tablab[0]).atributos)

        #Verifica que exista las dos tablas y que ademas tenga misma cantidad de columnas 
        #que no hallan columnas Repetidas en querys
        #que no se autoreferencie
        #que no exista el name constraint
        if (lonI)and(ExiT)and(RepQuery)and(NomTabDif)and not(veriConstName):
            #Procede a Buscar cada Columna y hacer sus validaciones Individual y dual
            conta=0
            for colT in (contenido):   
                #Busca Columna Tabla Padre
                Colum_P=copy.deepcopy(Get_Column(colT ,((tablaP[0]).atributos) ,tablaP[2]))
                #Busca Columna Tabla Foranea, a travez de conta
                Colum_F=copy.deepcopy(Get_Column(contenido2[conta] ,((tablaF[0]).atributos) ,tablaF[2]))
                
                #Longitud columnas Padre
                longiC1=len(Colum_P)
                #Longitud columnas Reference Foranea
                longiC2=len(Colum_F)

                #Ambas columnas deben existir
                LonC=(longiC1>0)and (longiC2>0)


                #Si ambas columnas a comparar existen
                if LonC:
                    #Extrae el tipo para comparar
                    TipCompC1=(Colum_P[0]).tipo
                    TipCompC2=(Colum_F[0]).tipo
                    #Compara los tipos de las 2 columnas
                    ComTipC=(TipCompC1==TipCompC2)

                    #veficar que primary key ,foranea
                    #verificar si foranea tiene llaves , 
                    #si tiene llaves , y TabPadre tiene ver que se puedan asociar
                    #y llave foranea destino diferente de primary key

                    #Verifica Columna Tabla Padre, no llave primaria
                    #DifPriKey=((Colum_P[0]).primary)!="True"
                    DifPriKey=True
                    
                    #Verifica Columna Tabla Padre, no llave foranea
                    DifForeKey=((Colum_P[0]).foreign)!="True"

                    #Verifica Columna Tabla Foranea SI llave primaria
                    SiPriKeyFora=((Colum_F[0]).primary)!=None

                    #Asocia llaves de padre a foraneas , deben existir
                    #false error, True bien
                    AsociaKeys=B_AsociarForanea((Colum_P[2]),(Colum_F[2]))

                    #compara Desti no primary , Fora si primary , mismo tipo dato, asocia llaves
                    if(ComTipC) and (DifPriKey)and (SiPriKeyFora)and(AsociaKeys) and (DifForeKey):
                        print("Si se puede guardar")    
                        #crea la llave foranea y desvincula objetos
                        New_Foranea=[copy.deepcopy((tablaF[0]).nombre),copy.deepcopy((Colum_F[0]).nombre)]
                        (tabla_Temp.atributos)[(Colum_P[1])].refence=(New_Foranea)
                        (tabla_Temp.atributos)[(Colum_P[1])].foreign="True"
                        #asigna el nombre de la foranea
                        if (ID!=0 and ID!=None and ID!=""):
                            ((tabla_Temp.atributos)[(Colum_P[1])].constraint).foreign=ID
                            GuardaF=True
                        elif (ID==0 or ID==None or ID==""):
                            ((tabla_Temp.atributos)[(Colum_P[1])].constraint).foreign=new_id
                            GuardaF=True
                        else:
                            ' '
                            GuardaF=False
                    else:
                        ' '
                        GuardaF=False
                        print("NO   se puede guardar3")
                        #compara Desti no primary , Fora si primary , mismo tipo dato
                        break
                else:
                    ' '
                    print("NO   se puede guardar2")
                    GuardaF=False
                    break
                    #Comparacion Lon columnas


                #para Get colForanea
                conta+=1
            

        else:
            ' ' 
            print("NO   se puede guardar1")
            GuardaF=False
            #multiple comparaciones for

        if GuardaF:
            listaTablas[tablab[1]]=copy.deepcopy(tabla_Temp)

    else:
        if reviConsName:
            print("Nombre constraint Repetido")
        else:
            print("Instruccion desconocida")


#Verifica pueda asociar llava foranea a Registros Prealmacenados Tabla padre
def B_AsociarForanea(DP,DF):
    
    retorna=False

    sumaComp=True
    for ver  in DP:
        bolT=False
        if ver!=None:
            for ver2 in DF:
                if (ver==ver2):
                    bolT=True
                    break
                if ver2==None:
                    #la tabla foranea no puede tener null en primar key
                    sumaComp=False
                    break
            sumaComp=(sumaComp and bolT)
        
    retorna=copy.copy(sumaComp)

    return retorna



#Verifica que si se va a asignar un UNIQUE la informacion de ella cumpla previamente
def B_Repetidos(ColumnaInfo_Col):
    
    con=0
    retorna=False

    for ver  in ColumnaInfo_Col:
        con2=0
        for ver2 in ColumnaInfo_Col:
            if (con!=con2) and (ver==ver2) and (ver!=None) and (ver2!=None):
                retorna=True
                break
            con2+=1
        con+=1
    return retorna



#Verifica que si se va a asignar un UNIQUE la informacion de ella cumpla previamente
def B_Nulos(ColumnaInfo_Col):
    
    retorna=False

    for ver in ColumnaInfo_Col:
        if (ver==None) :
            retorna=True
            break
        
    return retorna




def Ver_Exist_Name_Const(nameConst,T_head_cols):

    retornaExiste=True

    for c_t in T_head_cols:
        if (c_t.constraint).unique!=nameConst:
            retornaExiste=False
        else:
            retornaExiste=True
            break

        if (c_t.constraint).anulable!=nameConst:
            retornaExiste=False
        else:
            retornaExiste=True
            break

        if (c_t.constraint).default!=nameConst:
            retornaExiste=False
        else:
            retornaExiste=True
            break

        if (c_t.constraint).primary!=nameConst:
            retornaExiste=False
        else:
            retornaExiste=True
            break

        if (c_t.constraint).foreign!=nameConst:
            retornaExiste=False
        else:
            retornaExiste=True
            break

        if (c_t.constraint).check!=nameConst:
            retornaExiste=False
        else:
            retornaExiste=True
            break

    return retornaExiste
            


#Respuestas*********************************


def Msg_Alt_Add_CONSTRAINT(pre_con,DatoRepetido,columnab):
    outputTxt=""
    global baseActiva
    #Verifica Respuesta
    #if retorno==0:
        #outputTxt='Se agrego exitosamente la columna:'+ ID+' de Tabla:'+NombreTabla 
        #agregarMensjae('normal',outputTxt,"")
    #elif retorno==1:
        
    #elif retorno==2:
        
    #elif retorno==3:
        
    #else:
    
    print("Ingreso Mensajes CONSTRIN")





def Msg_Alt_Add_Column(NombreTabla,ID,retorno):
    outputTxt=""
    global baseActiva
    #Verifica Respuesta
    if retorno==0:
        outputTxt='Se agrego exitosamente la columna:'+ ID+' de Tabla:'+NombreTabla 
        agregarMensjae('normal',outputTxt,"")
    elif retorno==1:
        outputTxt='Hubo un error durante la eliminacion de la columna  '
        agregarMensjae('normal',outputTxt,"")
    elif retorno==2:
        outputTxt='La Base de datos :'+ baseActiva +' ,no existe '
        agregarMensjae('normal',outputTxt,"")
    elif retorno==3:
        outputTxt='La Tabla :'+NombreTabla +' ,no existe en la bd'
        agregarMensjae('normal',outputTxt,"")
    else:
        print("operacion desconocida 0")




def Msg_Alt_Drop(NombreTabla,ID,retorno):
    outputTxt=""
    global baseActiva
    #Verifica Respuesta
    if retorno==0:
        outputTxt='Se elimino exitosamente la columna:'+ ID+' de Tabla:'+NombreTabla 
        agregarMensjae('normal',outputTxt,"")
    elif retorno==1:
        outputTxt='Hubo un error durante la eliminacion de la columna  '
        agregarMensjae('normal',outputTxt,"")
    elif retorno==2:
        outputTxt='La Base de datos :'+ baseActiva +' ,no existe '
        agregarMensjae('normal',outputTxt,"")
    elif retorno==3:
        outputTxt='La Tabla :'+NombreTabla +' ,no existe en la bd'
        agregarMensjae('normal',outputTxt,"")
    elif retorno==4:
        outputTxt='La Tabla no puede quedar vacia o se trata eliminar Primary Key '
        agregarMensjae('normal',outputTxt,"")
    elif retorno==5:
        outputTxt='El valor de columna esta fuera de la tabla'
        agregarMensjae('normal',outputTxt,"")
    else:
        print("operacion desconocida 0")




def Msg_Alt_Rename(NombreTabla,ID1,retorno):
    outputTxt=""
    global baseActiva
    #Verifica Respuesta

    if retorno==0:
        outputTxt='Se Renombro la Tabla exitosamente,'+NombreTabla +' TO '+ID1 
        agregarMensjae('normal',outputTxt,"")
    elif retorno==1:
        outputTxt='Hubo un error durante la modificacion de la Tabla  '
        agregarMensjae('normal',outputTxt,"")
    elif retorno==2:
        outputTxt='La Base de datos :'+ baseActiva +' ,no existe '
        agregarMensjae('normal',outputTxt,"")
    elif retorno==3:
        outputTxt='La Tabla :'+NombreTabla +' ,no existe en la bd'
        agregarMensjae('normal',outputTxt,"")
    elif retorno==4:
        outputTxt='El nombre de la Tabla :'+ ID1 +' ,ya esta en uso '
        agregarMensjae('normal',outputTxt,"")
    else:
        print("operacion desconocida 0")



#CUERPOS=====================


def Cuerpo_ALTER_ALTER(Lista_Alter,NombreTabla,instr,ts):
    NombreTabla=instr.Id
    global listaTablas

    if 1==1:
        #Busca la tabla 
        tablab=copy.copy(Get_Table(NombreTabla))
        if len(tablab)>0:
            #Recorre Lista Alters 
            for alter_list_temp in Lista_Alter:
                #Instruccion a procesar COLUMN extra
                INSTRUCCION=alter_list_temp.instruccion
                #ID en columna 
                ID=alter_list_temp.id

                #Busca columna
                columnab=copy.copy(Get_Column(ID,(tablab[0]).atributos,tablab[2]))
                cop_tablab=copy.copy(tablab)

                if len(columnab)>0:


                    #Analisis continuacion Column Alter , no Constraint
                    Obj_Ext=alter_list_temp.extra
                    '''alttbalter1  : SET     NOT       NULL
                                    | DROP    NOT       NULL
                                    | SET     DATA      TYPE tipo valortipo
                                    | TYPE    tipo      valortipo
                                    | SET     DEFAULT   exp
                                    | DROP    DEFAULT  '''

                    OPE1=(Obj_Ext.prop1) #set  ,drop ,type        
                    OPE2=(Obj_Ext.prop2) #not  ,data ,tipo        ,default
                    OPE3=(Obj_Ext.prop3) #null ,type ,valortipo   , exp
                    
                    if OPE1.upper()=="TYPE":
                        #si es exp ni idea
                        OPEE1=OPE2 #tipo
                        OPEE2=OPE3 #valor tipo
                    else:
                        #si es exp ni idea
                        OPEE1=(Obj_Ext.prop4) #tipo
                        OPEE2=(Obj_Ext.prop5) #valor tipo


                    #Modificara una propieda de una columna
                    if OPE1.upper()=="SET" and OPE2.upper()=="NOT":
                        #columna SET NOT NULL
                        
                        algun_Null=0
                        for row in columnab[2]:
                            if row==None:
                                algun_Null=1
                                break
                        
                        if algun_Null==0:
                            (columnab[0]).anulable="False"
                            #((selecciona Tabla con index).get ListCol)[selec col tab]=set columna header
                            (((listaTablas[cop_tablab[1]]).atributos)[columnab[1]])=columnab[0]
                            msg='Se agrego exitosamente NOT NULL a:'+ID
                            agregarMensjae('normal',msg,'')
                        else:
                            ' '
                            #hay registros con contenido nulo
                            msg='Hay registros Nulos en la columna:'+ID
                            agregarMensjae('normal',msg,'')
                            print("hay registros nulos")
                        
                        
                    elif (OPE1.upper()=="SET" and OPE2.upper()=="DATA") or OPE1.upper()=="TYPE" :
                        
                        #NOTA SI TIPO VIENE MALO LOQUEA 
                        #en numero puede venir es exp

                        algun_No_Cast=0
                        #compara tipo  nuevo con valores
                        #para detectar incopatibilidad
                        for row in columnab[2]:
                            if row!=None:
                                resuBool=(validarTipo(OPEE1,row))
                                if resuBool==None:
                                    #el valor es incompatible
                                    algun_No_Cast=1
                                    break
                                print("resulbool:",resuBool)
                        print("algun_No_Cast:",algun_No_Cast)
                            
                        print("1:",OPE1,"22:",OPE2,"3:",OPE3,"4:",OPEE1,"5:",OPEE2)
                        if algun_No_Cast==0 and (OPEE1!="" or OPEE1!=None or OPEE1!=''):
                            (columnab[0]).tipo=OPEE1
                            if OPEE2!=0:
                                OP=OPEE2[0]
                                (columnab[0]).size=resolver_operacion(OP,ts)
                                print("sale:",resolver_operacion(OP,ts))
                            else:
                                (columnab[0]).size=""
                            #((selecciona Tabla con index).get ListCol)[selec col tab]=set columna header
                            (((listaTablas[cop_tablab[1]]).atributos)[columnab[1]])=columnab[0]
                            msg='Se cambio exitosamente el tipo de la columna:'+ID
                            agregarMensjae('normal',msg,'')
                        else:
                            ' '
                            #hay registros con contenido nulo
                            print("un registro no puede ser casteado")
                            msg='El nuevo tipo de dato es incompatible'
                            agregarMensjae('normal',msg,'')





                    elif OPE1.upper()=="SET" and OPE2.upper()=="DEFAULT":
                        #columna SET DEFAULT EXP
                        valCOL=resolver_operacion(OPE3,ts)#valor de la columna
                        T=(columnab[0]).tipo#Tipo de la columna
                        resuBool=None
                        try:
                            resuBool=(validarTipo(T,valCOL))
                            print("resulbool:",resuBool)
                        except:
                            ' '
                        if(resuBool==None):
                            msg='42804:La columna '+ID+' es de tipo '+T
                            agregarMensjae('error',msg,'42804')
                        else:
                            print(T," ",valCOL)
                            #((selecciona Tabla con index).get ListCol)[selec col tab]=set columna header
                            (((listaTablas[cop_tablab[1]]).atributos)[columnab[1]]).default=valCOL
                            msg='Se agrego exitosamente DEFAULT a la columna:'+ID
                            agregarMensjae('normal',msg,'')
                    elif OPE1.upper()=="DROP" and OPE2.upper()=="NOT":
                        #columna DROP NOT NULL
                        (columnab[0]).anulable=None
                        #((selecciona Tabla con index).get ListCol)[selec col tab]=set columna header
                        (((listaTablas[cop_tablab[1]]).atributos)[columnab[1]])=columnab[0]
                        msg='Se Elimino exitosamente NOT NULL de la columna:'+ID
                        agregarMensjae('normal',msg,'')
                    elif OPE1.upper()=="DROP" and OPE2.upper()=="DEFAULT":
                        #columna DROP DEFAULT
                        (columnab[0]).default=None
                        #((selecciona Tabla con index).get ListCol)[selec col tab]=set columna header
                        (((listaTablas[cop_tablab[1]]).atributos)[columnab[1]])=columnab[0]
                        msg='Se elimino exitosamente DEFAULT de la columna:'+ID
                        agregarMensjae('normal',msg,'')
                    else:
                        ' '
                        #operacionn desconocida
                        print("op desconocida")


                else: 
                    ' '
                    #la columna no existe
                    print("columna no existe")
                    msg='La columna:'+ID+' no existe '
                    agregarMensjae('normal',msg,'')

                
        else:
            ' '
            #La tabla no existe
            print("tabla no existe")
            msg='La tabla:'+NombreTabla+' no existe '
            agregarMensjae('normal',msg,'')







def cuerpo_ALTER_RENAME(NombreTabla,ObjetoAnalisis,ID1,ID2,OPERACION):
    global listaTablas

    print(NombreTabla," ------")
    #determinar si es RENAME COLUMN , RENAME COLUMN , RENAME CONSTRAINT, RENAME TABLE
    if OPERACION.upper()=="CONSTRAINT":
        ' '

        RenomForanConstraint(NombreTabla,ID1,ID2)


    elif OPERACION.upper()=="TO":
        #Alterara el NOMBRE de una tabla de una db Seleccionada
        print("BASEACTIVA:",baseActiva)
        retorno=EDD.alterTable(baseActiva, NombreTabla,ID1)

        #si encuentra la tabla en fisico , procede a buscar header
        if retorno==0:
            #hace copia de las tablas 
            #tablab=copy.copy(Get_Table(copy.deepcopy(NombreTabla)))
            #recorre las tablas para modificar el nombre de la tabla
            conta=0
            for tab_t in listaTablas:
                if (tab_t.nombre)==NombreTabla:

                    #Renombra las Tablas Foraneas
                    RenomForanTab(NombreTabla,ID1)
                    #Renombra la tabla
                    ((listaTablas[conta]).nombre)=ID1
                    
                    break
                conta+=1
        #Verifica Respuesta
        Msg_Alt_Rename(NombreTabla,ID1,retorno)


    elif OPERACION.upper()=="COLUMN" or OPERACION.upper()=="ID" :
            
        #[Cabecera ,Posicion_Header, Cuerpo ]
        #def Get_Column(name_c,tabla_H_List,tabla_C_List):
        tablab=copy.copy(Get_Table(NombreTabla))
            
        #si existe la tabla en la base de datos
        if len(tablab)>0:
                
            #Busca la columna para cambiarla
            print(tablab)
            columnab=Get_Column(ID1,(tablab[0]).atributos,tablab[2])
                
            #Si encuentra la columna procede a verificar que no exista el nombre NUEVO
            if len(columnab)>0:
                columnaComprueba=Get_Column(ID2,(tablab[0]).atributos,tablab[2])
                    
                #Si el nombre no existe en la tabla procede a cambiarlo
                if len(columnaComprueba)==0:
                    RenomForanCol(NombreTabla,ID1,ID2)
                    head_Tabla_Cols=(tablab[0]).atributos
                    #Renombra la columna
                    (head_Tabla_Cols[columnab[1]]).nombre=ID2
                    #Actualiza la lista de columnas tabla
                    (tablab[0]).atributos=head_Tabla_Cols
                    head_Tabla_Cols=(tablab[0]).atributos
                    print((head_Tabla_Cols[columnab[1]]).nombre)
                        #Actualiza en la base de datos
                        
                    listaTablas[tablab[1]]=tablab[0]

                    outputTxt='La columna:'+ID1+' cambio su nombre por:'+ID2+' exitosamente'
                    agregarMensjae('normal',outputTxt,"")
                    #print("el nombre existe col")
                else:
                    outputTxt='El nombre:'+ID2+' ya existe en la tabla:'+NombreTabla
                    agregarMensjae('normal',outputTxt,"")
                    print("el nombre existe col")
                    #el nombre Nuevo de la columna ya existe
            else:
                outputTxt='La columna:'+ID1+' no existe en la Tabla:'+NombreTabla
                agregarMensjae('normal',outputTxt,"")
                print("la col no existe")
                #la columna a modificar no existe
        else:
            outputTxt='La tabla:'+NombreTabla+' no existe en la bd:'+baseActiva
            agregarMensjae('normal',outputTxt,"")
            print("la tabla no existe")
            #la tabla a modificar no existe




#Renombra llaves foraneas vinculadas a la tabla, oldName, newname
def RenomForanTab(NombreTabla,ID1):
    global baseActiva
    global listaTablas

    for tabT in listaTablas:
        #extrae una tabla
        if tabT.basepadre==baseActiva:
            #extra las columnas
            listaCols=tabT.atributos
            cont=0
            #recorre las columnas
            for colT in listaCols:
                #si columna tiene alguna foranea guardada puede ser None
                if (colT.refence)!=None:
                    f_t=(colT.refence)
                    if f_t[0]==NombreTabla:
                        #Renombra la tabla foranea
                        f_t[0]=ID1

                cont+=1


#Renombra llaves foraneas vinculadas a la tabla, columna, old columna , new columna
def RenomForanCol(NombreTabla,ID1,ID2):
    global baseActiva
    global listaTablas

    for tabT in listaTablas:
        #extrae una tabla
        if tabT.basepadre==baseActiva:
            #Verifica que tenga la tabla

            #extra las columnas
            listaCols=tabT.atributos
            cont=0
            #recorre las columnas
            for colT in listaCols:
                #si columna tiene alguna foranea guardada puede ser None
                if (colT.refence)!=None:
                    f_t=(colT.refence)
                    if (f_t[0]==NombreTabla) and (f_t[1]==ID1):
                        #Renombra la tabla foranea
                        f_t[1]=ID2
                cont+=1


#Renombra llaves foraneas vinculadas a la tabla, columna, old columna , new columna
def RenomForanConstraint(NombreTabla,ID1,ID2):
    global baseActiva
    global listaTablas

    for tabT in listaTablas:
        #extrae una tabla
        if tabT.basepadre==baseActiva:
            #Verifica que tenga la tabla
            if tabT.nombre==NombreTabla:
                #extra las columnas
                listaCols=tabT.atributos
                cont=0
                #recorre las columnas
                for colT in listaCols:
                    #si columna tiene algun constraint puede ser nulo
                    print("busca:",ID1," cambia por:",ID2)
                    val1=((colT.constraint).unique)
                    val2=((colT.constraint).anulable)
                    val3=((colT.constraint).default)
                    val4=((colT.constraint).primary)
                    val5=((colT.constraint).foreign)
                    val6=((colT.constraint).check)
                    
                    if val1==ID1:
                        ((colT.constraint).unique)=ID2
                        #Renombra constraint
                    elif val2==ID1:
                        ((colT.constraint).anulable)=ID2
                        #Renombra constraint
                    elif val3==ID1:
                        ((colT.constraint).default)=ID2
                        #Renombra constraint
                        
                    elif val4==ID1:
                        ((colT.constraint).primary)=ID2
                        #Renombra constraint
                        
                    elif val5==ID1:
                        ((colT.constraint).foreign)=ID2
                        print("MODIFICA FORRANEAA")
                        #Renombra constraint
                    elif val6==ID1:
                        ((colT.constraint).check)=ID2
                        #Renombra constraint

                    cont+=1



#Renombra llaves foraneas vinculadas a la tabla, columna, old columna , new columna
def DropForanConstraint(NombreTabla,ID1):
    global baseActiva
    global listaTablas

    for tabT in listaTablas:
        #extrae una tabla
        if tabT.basepadre==baseActiva:
            #Verifica que tenga la tabla
            if tabT.nombre==NombreTabla:
                #extra las columnas
                listaCols=tabT.atributos
                cont=0
                #recorre las columnas
                for colT in listaCols:
                    #si columna tiene algun constraint puede ser nulo
                    print("busca:",ID1," cambia por:",None)
                    val1=((colT.constraint).unique)
                    val2=((colT.constraint).anulable)
                    val3=((colT.constraint).default)
                    val4=((colT.constraint).primary)
                    val5=((colT.constraint).foreign)
                    val6=((colT.constraint).check)
                    
                    if val1==ID1:
                        ((colT.constraint).unique)=None
                        ((colT).unique)=None

                        #Renombra constraint
                    elif val2==ID1:
                        ((colT.constraint).anulable)=None
                        ((colT).anulable)=None

                        #Renombra constraint
                    elif val3==ID1:
                        ((colT.constraint).default)=None
                        ((colT).default)=None
                        #Renombra constraint
                        
                    elif val4==ID1:
                        ((colT.constraint).primary)=None
                        ((colT).primary)=None
                        #Renombra constraint
                        
                    elif val5==ID1:
                        ((colT.constraint).foreign)=None
                        ((colT).foreign)=None
                        ((colT).refence)=None

                        print("MODIFICA FORRANEAA")
                        #Renombra constraint
                    elif val6==ID1:
                        ((colT.constraint).check)=None
                        ((colT).check)=None
                        #Renombra constraint

                    cont+=1




#Renombra llaves foraneas vinculadas a la tabla, columna, old columna , new columna
def BuscForanCol(NombreTabla,ID1):
    global baseActiva
    global listaTablas

    retorno=False
    for tabT in listaTablas:
        #extrae una tabla
        if tabT.basepadre==baseActiva:
            #Verifica que tenga la tabla

            #extra las columnas
            listaCols=tabT.atributos
            cont=0
            #recorre las columnas
            for colT in listaCols:
                #si columna tiene alguna foranea guardada puede ser None
                if (colT.refence)!=None:
                    f_t=(colT.refence)
                    if (f_t[0]==NombreTabla) and (f_t[1]==ID1):
                        retorno=True
                        break
                cont+=1

    return retorno


def Cuerpo_ALTER_DROP(NombreTabla,ObjetoAnalisis,INSTRUCCION,ID):
    if INSTRUCCION.upper()=="COLUMN" or INSTRUCCION.upper()=="ID":
        #busco la Tabla en las cabeceras
        tablaB=Get_Table(NombreTabla)
        #[[cabecera],posicion,[cuerpo]]
        print (tablaB)
        if len(tablaB)>0:
            #busco la columna en las cabeceras
            ColumnInfo=Get_Column(ID,(tablaB[0]).atributos,(tablaB[2]))
            #[Objeto_Columna,posicion,[Registros]]
            #def Get_Column(name_c,tabla_H_List,tabla_C_List):
            print (ColumnInfo)
            busRefFuera=BuscForanCol(NombreTabla,ID)
            print("salalsdfkj :",not(busRefFuera))
            if (len(ColumnInfo)>0) and (len(tablaB[0].atributos)>1) and not(busRefFuera):
                    
                #obtiene No. de columna del objeto ColumnInfo
                No_col=ColumnInfo[1]
                table_cambiado=Table_Reensable_H(tablaB[0],No_col)
                retorno=1
                try:
                    #si no da error al eliminar columna Registro,
                    #Elimina Header
                    print(baseActiva," ",NombreTabla," ",No_col)
                    retorno=EDD.alterDropColumn(baseActiva,NombreTabla,No_col)
                except:
                    retorno=0
                    #VER PORQUE ERRO EN EDD
                    ' '
                print (retorno)
                if retorno==0:
                    ' '
                    posicion=ColumnInfo[1]
                    del ((listaTablas[tablaB[1]]).atributos)[posicion]

                Msg_Alt_Drop(NombreTabla,ID,retorno)


            else:
                outputTxt='La tabla debe tener al menos 1 columna'
                agregarMensjae('normal',outputTxt,"")
        else:
            outputTxt='La tabla '+NombreTabla +' no existe en la base de datosc'
            agregarMensjae('normal',outputTxt,"")
            #la tabla no existe en cabeceras o cuerpo
    elif INSTRUCCION.upper()=="CONSTRAINT":
        ' '
        DropForanConstraint(NombreTabla,ID)

    else:
        ' '#Error

#FIN MIO --------------------------------------------


#--Select

def ejecutar_select(instr,ts):
    agregarMensjae('normal','Select','')
    for val in instr.funcion_alias:
        if(isinstance (val,Funcion_Alias)):
            result = resolver_operacion(val.nombre,ts)
            alias = ''
            print("SALIDA",result)
            if isinstance (val.alias,Operando_ID):
                alias = str(val.alias.id)
            elif isinstance (val.alias,Operando_Cadena):
                alias = str(val.alias.valor)
            print("CABECERA",alias,"RESULTADO",result)
            print(val.nombre)

            tablaresult = PrettyTable()
            #tablaresult.title = 'Resultado'
            if (alias != None):
                tablaresult.field_names = [ str(alias) ]

            elif isinstance (val, Operacion_Math_Unaria):
                tablaresult.field_names = [ str(val.nombre.operador) ]

            tablaresult.add_row([ str(result) ])
            agregarMensjae('table',tablaresult,'')


def select_table(instr,ts):
    #print('cantidad ',instr.cantida,' parametros ',instr.parametros,' cuerpo ',instr.cuerpo,' funcion_alias',instr.funcion_alias)
    agregarMensjae('normal','Select','')
    if instr.cantida==True: # Distinct
        cuerpo_select_parametros(True,instr.parametros,instr.cuerpo,ts)
    else: # No Distinct
        if instr.parametros=="*": # All
            cuerpo_select(instr.cuerpo,ts)
        else: # Algunas
            cuerpo_select_parametros(False,instr.parametros,instr.cuerpo,ts)

def cuerpo_select(cuerpo,ts):
    ltablas=[] # tablas seleccionadas
    lalias=[] # alias de tablas seleccionadas
    lcabeceras=[] # cabeceras tablas
    lregistros=[] # registros tablas
    tablastmp = EDD.showTables(baseActiva)
    # FROM ---------------------------------------------------------
    for tabla in cuerpo.b_from:
        name=''
        alias=''
        if ' ' in tabla.nombre:  
            splited=tabla.nombre.split()  # puede venir ID ID en gramatica se concatenan
            name=splited[0]
            alias=splited[1]
        else:
            name=tabla.nombre
        if name in tablastmp: # tabla registrada
            ltablas.append(name)
            if alias != '':
                lalias.append(alias)
            tb = buscarTabla(baseActiva,name).atributos
            for col in tb:
                lcabeceras.append(col.nombre)
        lregistros.append(EDD.extractTable(baseActiva,name))
    # crearTabla--------------------------------------------------------
    result = PrettyTable()
    result.field_names = lcabeceras
    for registro in itertools.product(*lregistros): #producto cartesiano
        fila=[]
        for i in registro:
            for j in i:
                fila.append(j)
        result.add_row(fila)

    # WHERE --------------------------------------------------------
    if cuerpo.b_where != False:
        result=filtroWhere(result,cuerpo.b_where,ts)
    
    #mostrar el resultado
    agregarMensjae('table',result,'')
    #agregar reporteTS
    agregarTSRepor('SELECT','','','','')
    for tab in ltablas:
        #obtener la tabla
        res=buscarTabla(baseActiva,tab)
        if(res!=None):
            for col in res.atributos:
                tip=col.tipo
                nom=col.nombre
                agregarTSRepor('',nom,tip,tab,'1')

def cuerpo_select_parametros(distinct,parametros,cuerpo,ts):
    ltablas=[] # tablas seleccionadas
    lalias=[] # alias de tablas seleccionadas
    lcabeceras=[] # cabeceras tablas
    lcolumnas=[] # columnas a mostrar
    lalias_colum=[] # alias columnas
    lregistros=[] # registros tablas
    tablastmp = EDD.showTables(baseActiva)
    # FROM ---------------------------------------------------------
    for tabla in cuerpo.b_from:
        name=''
        alias=''
        if ' ' in tabla.nombre:  
            splited=tabla.nombre.split()  # puede venir ID ID en gramatica se concatenan
            name=splited[0]
            alias=splited[1]
        else:
            name=tabla.nombre
        if name in tablastmp: # tabla registrada
            ltablas.append(name)
            if alias != '':
                lalias.append(alias)
            tb = buscarTabla(baseActiva,name).atributos
            for col in tb:
                lcabeceras.append(col.nombre)
        lregistros.append(EDD.extractTable(baseActiva,name))
    # Campos Select ------------------------------------------------
    for campo in parametros:  #nombre tipo alias fun_exp
        nm = resolver_operacion(campo.nombre,ts)
        ali = resolver_operacion(campo.alias,ts)
        lcolumnas.append(nm)
        lalias_colum.append(ali)
    # JOINS --------------------------------------------------------
    # WHERE --------------------------------------------------------
    #print(lcolumnas)
    #print(lcabeceras)
    colEx=True
    for col in lcolumnas:
        if(col not in lcabeceras):
            colEx=False
            msg='42703: No existe columna en tabla:'+col
            agregarMensjae('error',msg,'42703')
             
    if colEx:
        result = PrettyTable()
        result.field_names = lcabeceras
        for registro in itertools.product(*lregistros): #producto cartesiano
            fila=[]
            for i in registro:
                for j in i:
                    fila.append(j)
            result.add_row(fila) 
        # WHERE --------------------------------------------------------
        if cuerpo.b_where != False:
            result=filtroWhere(result,cuerpo.b_where,ts)
        
        #filtro col a mostrar    
        result = result.get_string(fields=lcolumnas)
        agregarMensjae('table',result,'')
        #agregar reporteTS
        agregarTSRepor('SELECT','','','','')
        for tab in ltablas:
            #obtener la tabla
            res=buscarTabla(baseActiva,tab)
            if(res!=None):
                for col in res.atributos:
                    if(col.nombre in lcolumnas):
                        tip=col.tipo
                        nom=col.nombre
                        agregarTSRepor('',nom,tip,tab,'1')




def filtroWhere(tabla,filtro,ts):
    listaEliminar=[]
    filtroOK=True
    if isinstance(filtro,Operacion_Relacional):
        op1=resolver_operacion(filtro.op1,ts)
        op2=resolver_operacion(filtro.op2,ts)
        #id operador XXX
        if isinstance(filtro.op1,Operando_ID):
            if(op1 in tabla.field_names):
                #id operador id
                if isinstance(filtro.op2,Operando_ID):
                    if(op2 in tabla.field_names):
                        cont=0
                        for row in tabla:
                            row.border = False
                            row.header = False
                            col1=row.get_string(fields=[op1]).strip()
                            col2=row.get_string(fields=[op2]).strip()
                            if(filtro.operador == OPERACION_RELACIONAL.MAYOR_QUE and col1>col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MAYORIGUALQUE and col1>=col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MENOR_QUE and col1<col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MENORIGUALQUE and col1<=col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.IGUAL and col1==col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.DIFERENTE and col1!=col2):''
                            else:
                                listaEliminar.append(cont)
                            cont+=1
                    else:
                        filtroOK=False
                        msg='la columna no existe en la consulta:'+op1
                        agregarMensjae('error',msg,'42804')
                #id operador numero,cadena,boleano
                elif (isinstance(filtro.op2,Operando_Numerico) or 
                isinstance(filtro.op2,Operacion_Aritmetica) or 
                isinstance(filtro.op2,Operando_Cadena) or 
                isinstance(filtro.op2,Operando_Booleano)):
                    if(op2 != None):
                        cont=0
                        for row in tabla:
                            row.border = False
                            row.header = False
                            col1=row.get_string(fields=[op1]).strip()
                            col2=str(op2)
                            if(filtro.operador == OPERACION_RELACIONAL.MAYOR_QUE and col1>col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MAYORIGUALQUE and col1>=col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MENOR_QUE and col1<col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MENORIGUALQUE and col1<=col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.IGUAL and col1==col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.DIFERENTE and col1!=col2):''
                            else:
                                listaEliminar.append(cont)
                            cont+=1
                    else:
                        filtroOK=False
                        msg='42804:no es posible evaluar el where'
                        agregarMensjae('error',msg,'42804')
                else:
                    filtroOK=False
                    msg='42804:no es posible evaluar el where'
                    agregarMensjae('error',msg,'42804')
            else:
                filtroOK=False
                msg='la columna no existe en la consulta:'+op1
                agregarMensjae('error',msg,'42804')
        #XXX operador XXX 
        elif (isinstance(filtro.op1,Operando_Numerico) or 
                isinstance(filtro.op1,Operacion_Aritmetica) or 
                isinstance(filtro.op1,Operando_Cadena) or 
                isinstance(filtro.op1,Operando_Booleano)):
                if isinstance(filtro.op2,Operando_ID):
                    if(op2 in tabla.field_names):
                        cont=0
                        for row in tabla:
                            row.border = False
                            row.header = False
                            col1=str(op1)
                            col2=row.get_string(fields=[op2]).strip()
                            if(filtro.operador == OPERACION_RELACIONAL.MAYOR_QUE and col1>col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MAYORIGUALQUE and col1>=col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MENOR_QUE and col1<col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MENORIGUALQUE and col1<=col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.IGUAL and col1==col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.DIFERENTE and col1!=col2):''
                            else:
                                listaEliminar.append(cont)
                            cont+=1
                    else:
                        filtroOK=False
                        msg='la columna no existe en la consulta:'+op1
                        agregarMensjae('error',msg,'42804')
                #id operador numero,cadena,boleano
                elif (isinstance(filtro.op2,Operando_Numerico) or 
                isinstance(filtro.op2,Operacion_Aritmetica) or 
                isinstance(filtro.op2,Operando_Cadena) or 
                isinstance(filtro.op2,Operando_Booleano)):
                    if(op2 != None):
                        cont=0
                        for row in tabla:
                            row.border = False
                            row.header = False
                            col1=str(op1)
                            col2=str(op2)
                            if(filtro.operador == OPERACION_RELACIONAL.MAYOR_QUE and col1>col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MAYORIGUALQUE and col1>=col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MENOR_QUE and col1<col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.MENORIGUALQUE and col1<=col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.IGUAL and col1==col2):''
                            elif(filtro.operador == OPERACION_RELACIONAL.DIFERENTE and col1!=col2):''
                            else:
                                listaEliminar.append(cont)
                            cont+=1
                    else:
                        filtroOK=False
                        msg='42804:no es posible evaluar el where'
                        agregarMensjae('error',msg,'42804')
                else:
                    filtroOK=False
                    msg='42804:no es posible evaluar el where'
                    agregarMensjae('error',msg,'42804')

        else:
            filtroOK=False
            msg='42804:no es posible evaluar el where'
            agregarMensjae('error',msg,'42804')
    #recursividad        
    elif isinstance(filtro,Operacion_Logica_Binaria):
        if(filtro.operador==OPERACION_LOGICA.AND):
            tabla=filtroWhere(tabla,filtro.op1,ts)
            tabla=filtroWhere(tabla,filtro.op2,ts)
        elif(filtro.operador==OPERACION_LOGICA.OR):
            tabla1=copy.deepcopy(tabla)
            tabla2=copy.deepcopy(tabla)
            tabla1=filtroWhere(tabla1,filtro.op1,ts)
            tabla2=filtroWhere(tabla2,filtro.op2,ts)
            #unir las tablas
            for row in tabla2:
                listInsert=[]
                row.border = False
                row.header = False
                for col in tabla2.field_names:
                    col1=row.get_string(fields=[col]).strip()
                    listInsert.append(col1)
                tabla1.add_row(listInsert)

            tabla=tabla1
    else:
        filtroOK=False
        msg='debe haber una condicion relacional en el where'
        agregarMensjae('error',msg,'42804')

    #realizar eliminacion
    if(filtroOK):
        cont=len(listaEliminar)
        while cont>0:
            tabla.del_row(listaEliminar[cont-1])
            cont=cont-1
    

    return tabla


#-------------
def resolver_operacion(operacion,ts):
    if isinstance(operacion, Operacion_Logica_Unaria):
        op = resolver_operacion(operacion.op, ts)
        if isinstance(op, bool):
            return not(op)
        else:
            print('Error: No se permite operar los tipos involucrados')
    elif isinstance(operacion, Operacion_Logica_Binaria):
        op1 = resolver_operacion(operacion.op1,ts)
        op2 = resolver_operacion(operacion.op2,ts)
        if isinstance(op1, bool) and isinstance(op2, bool):
            if operacion.operador == OPERACION_LOGICA.AND: return op1 and op2
            elif operacion.operador == OPERACION_LOGICA.OR: return op1 or op2 
        else:
            print('Error: No se permite operar los tipos involucrados')
    elif isinstance(operacion, Operacion_Relacional):
        op1 = resolver_operacion(operacion.op1,ts)
        op2 = resolver_operacion(operacion.op2,ts)
        if isinstance(op1, (int,float)) and isinstance(op2, (int,float)):
            if operacion.operador == OPERACION_RELACIONAL.IGUAL: return op1 == op2
            elif operacion.operador == OPERACION_RELACIONAL.DIFERENTE: return op1 != op2
            elif operacion.operador == OPERACION_RELACIONAL.MAYORIGUALQUE: return op1 >= op2
            elif operacion.operador == OPERACION_RELACIONAL.MENORIGUALQUE: return op1 <= op2
            elif operacion.operador == OPERACION_RELACIONAL.MAYOR_QUE: return op1 > op2
            elif operacion.operador == OPERACION_RELACIONAL.MENOR_QUE: return op1 < op2
        elif isinstance(op1, (str)) and isinstance(op2, (str)):
            if operacion.operador == OPERACION_RELACIONAL.IGUAL: return op1 == op2
            elif operacion.operador == OPERACION_RELACIONAL.DIFERENTE: return op1 != op2
            elif operacion.operador == OPERACION_RELACIONAL.MAYORIGUALQUE: return op1 >= op2
            elif operacion.operador == OPERACION_RELACIONAL.MENORIGUALQUE: return op1 <= op2
            elif operacion.operador == OPERACION_RELACIONAL.MAYOR_QUE: return op1 > op2
            elif operacion.operador == OPERACION_RELACIONAL.MENOR_QUE: return op1 < op2
        else:
            print('Error: No se permite operar los tipos involucrados') 
    elif isinstance(operacion, Operacion_Aritmetica):
        op1 = resolver_operacion(operacion.op1,ts)
        op2 = resolver_operacion(operacion.op2,ts)
        if isinstance(op1, (int,float)) and isinstance(op2, (int,float)):
            if operacion.operador == OPERACION_ARITMETICA.MAS: return op1 + op2
            elif operacion.operador == OPERACION_ARITMETICA.MENOS: return op1 - op2
            elif operacion.operador == OPERACION_ARITMETICA.POR: return op1 * op2
            elif operacion.operador == OPERACION_ARITMETICA.DIVIDIDO: return op1 / op2
            elif operacion.operador == OPERACION_ARITMETICA.POTENCIA: return op1 ** op2
            elif operacion.operador == OPERACION_ARITMETICA.MODULO: return op1 % op2
        else:
            print('Error: No se permite operar los tipos involucrados') 
    elif isinstance(operacion, Operacion_Especial_Binaria):
        op1 = resolver_operacion(operacion.op1,ts)
        op2 = resolver_operacion(operacion.op2,ts)
        if isinstance(op1, int) and isinstance(op2, int):
            if operacion.operador == OPERACION_ESPECIAL.AND2: return op1 & op2
            elif operacion.operador == OPERACION_ESPECIAL.OR2: return op1 | op2
            elif operacion.operador == OPERACION_ESPECIAL.XOR: return op1 ^ op2
            elif operacion.operador == OPERACION_ESPECIAL.DEPDER: return op1 >> op2
            elif operacion.operador == OPERACION_ESPECIAL.DEPIZQ: return op1 << op2
        else:
            print('Error: No se permite operar los tipos involucrados')
    elif isinstance(operacion, Operacion_Especial_Unaria):
        op = resolver_operacion(operacion.op,ts)
        if isinstance(op, (int,float)):
            if operacion.operador == OPERACION_ESPECIAL.SQRT2: return op ** (1/2)
            elif operacion.operador == OPERACION_ESPECIAL.CBRT2: return op ** (1/3)
            elif operacion.operador == OPERACION_ESPECIAL.NOT2: 
                if isinstance(op, int): return ~op
                else: print('Error: No se permite operar los tipos involucrados')
            else:
                print('Error: No se permite operar los tipos involucrados')
    elif isinstance(operacion, Negacion_Unaria):
        op = resolver_operacion(operacion.op,ts)
        if isinstance(op, (int,float)):
            return op * -1
        else:
            print('Error: No se permite operar los tipos involucrados')
    elif isinstance(operacion, Operando_Booleano):
        return operacion.valor
    elif isinstance(operacion, Operando_Numerico):
        return operacion.valor
    elif isinstance(operacion, Operando_Cadena):
        return operacion.valor
    elif isinstance(operacion, Operando_ID):
        return operacion.id 
    elif isinstance(operacion, Operacion_Math_Unaria):
        op = resolver_operacion(operacion.op,ts)
        print("Entre a math unaria")
        if isinstance(op, (int,float)):
            if operacion.operador == OPERACION_MATH.ABS: return abs(op) 
            elif operacion.operador == OPERACION_MATH.CBRT: return f.func_cbrt(op)
            elif operacion.operador == OPERACION_MATH.CEIL: return math.ceil(op)
            elif operacion.operador == OPERACION_MATH.CEILING: return math.ceil(op)
            elif operacion.operador == OPERACION_MATH.DEGREES: return math.degrees(op)
            elif operacion.operador == OPERACION_MATH.EXP: return math.exp(op)
            elif operacion.operador == OPERACION_MATH.FACTORIAL: return math.factorial(op)
            elif operacion.operador == OPERACION_MATH.FLOOR: return math.floor(op)
            elif operacion.operador == OPERACION_MATH.LN: return math.log(op)
            elif operacion.operador == OPERACION_MATH.LOG: return math.log10(op)
            elif operacion.operador == OPERACION_MATH.RADIANS: return math.radians(op)
            elif operacion.operador == OPERACION_MATH.SIGN: return f.func_sign(op)
            elif operacion.operador == OPERACION_MATH.SQRT: return  math.sqrt(op)
            elif operacion.operador == OPERACION_MATH.TRUNC: return math.trunc(op)

            elif operacion.operador == OPERACION_MATH.ACOS: return math.acos(op)
            elif operacion.operador == OPERACION_MATH.ACOSD: return math.acos(math.radians(op))
            elif operacion.operador == OPERACION_MATH.ASIN: return math.asin(op)
            elif operacion.operador == OPERACION_MATH.ASIND: return math.asin(math.radians(op))
            elif operacion.operador == OPERACION_MATH.ATAN: return math.atan(op)
            elif operacion.operador == OPERACION_MATH.ATAND: return math.atan(math.radians(op))
            elif operacion.operador == OPERACION_MATH.COS: return math.cos(op)
            elif operacion.operador == OPERACION_MATH.COSD: return math.cos(math.radians(op))
            elif operacion.operador == OPERACION_MATH.COT: return f.func_cot(op)
            elif operacion.operador == OPERACION_MATH.COTD: return f.func_cot(math.radians(op))
            elif operacion.operador == OPERACION_MATH.SIN: return math.sin(op)
            elif operacion.operador == OPERACION_MATH.SIND: return math.sin(math.radians(op))
            elif operacion.operador == OPERACION_MATH.TAN: return math.tan(op)
            elif operacion.operador == OPERACION_MATH.TAND: return math.tan(math.radians(op))
            elif operacion.operador == OPERACION_MATH.SINH: return math.sinh(op)
            elif operacion.operador == OPERACION_MATH.COSH: return math.cosh(op)
            elif operacion.operador == OPERACION_MATH.TANH: return math.tanh(op)
            elif operacion.operador == OPERACION_MATH.ASINH: return math.asinh(op)
            elif operacion.operador == OPERACION_MATH.ACOSH: return math.acosh(op)
            elif operacion.operador == OPERACION_MATH.ATANH: return math.atanh(op)

    elif isinstance(operacion, Operacion_Math_Binaria):
        op1 = resolver_operacion(operacion.op1,ts)
        op2 = resolver_operacion(operacion.op2,ts)
        if isinstance(op1,(int,float)) and isinstance(op2,(int,float)):
            if operacion.operador == OPERACION_MATH.DIV: return op1//op2
            elif operacion.operador == OPERACION_MATH.MOD: return math.fmod(op1,op2)
            elif operacion.operador == OPERACION_MATH.GCD: return math.gcd(op1,op2)
            elif operacion.operador == OPERACION_MATH.POWER: return math.pow(op1,op2)
            elif operacion.operador == OPERACION_MATH.ROUND: return f.func_round(op1,op2)
            elif operacion.operador == OPERACION_MATH.ATAN2: return f.func_atan2(op1,op2)
            elif operacion.operador == OPERACION_MATH.ATAN2D: return f.func_atan2d(op1,op2)

    elif isinstance(operacion,Operacion__Cubos):
        op1 = resolver_operacion(operacion.op1,ts)
        op2 = resolver_operacion(operacion.op2,ts)
        op3 = resolver_operacion(operacion.op3,ts)
        op4 = resolver_operacion(operacion.op4,ts)
        if isinstance(op1,(int,float)) and isinstance(op2,(int,float)) and isinstance(op3,(int,float)) and isinstance(op4,(int,float)) :
            if operacion.operador == OPERACION_MATH.WIDTH_BUCKET: return f.func_width_bucket(op1,op2,op3,op4)
            else: print("Error width bucket en tipo de parametros")
            
    elif isinstance(operacion, Operacion_Definida):
        if operacion.operador == OPERACION_MATH.PI: return math.pi
        elif operacion.operador == OPERACION_MATH.RANDOM: return f.func_random() 

    elif isinstance(operacion, Operacion_Strings):
        op = resolver_operacion(operacion.cadena,ts)
        if isinstance (op,(str)):
            if operacion.operador == OPERACION_BINARY_STRING.MD5: return f.func_md5(op)
            elif operacion.operador == OPERACION_BINARY_STRING.SHA256: return f.func_md5(op)
            elif operacion.operador == OPERACION_BINARY_STRING.LENGTH: return f.func_length(op)

    elif isinstance(operacion,Operacion_String_Binaria):
        op1 = resolver_operacion(operacion.op1,ts)
        op2 = resolver_operacion(operacion.op2,ts)
        if isinstance(op1,(str)) and isinstance(op2,(int)):
            print(op1+ "-->" +str(op2))
            if(operacion.operador == OPERACION_BINARY_STRING.GET_BYTE): return f.func_get_byte(op1,op2)
        elif isinstance(op1,(str)) and isinstance(op2,(str)):
            if (operacion.operador == OPERACION_BINARY_STRING.ENCODE) : return f.func_encode(op1,op2)
            elif (operacion.operador == OPERACION_BINARY_STRING.DECODE) : return f.func_decode(op1,op2) 
       
    elif isinstance(operacion,Operacion_String_Compuesta):
        op1 = resolver_operacion(operacion.op1,ts)
        op2 = resolver_operacion(operacion.op2,ts)
        op3 = resolver_operacion(operacion.op3,ts)
        if isinstance(op1,(str)) and isinstance(op2,(int)) and isinstance(op3,(int)) :
            if operacion.operador == OPERACION_BINARY_STRING.SUBSTR: return f.func_substring(op1,op2,op3)
            elif operacion.operador == OPERACION_BINARY_STRING.SUBSTRING: return f.func_substring(op1,op2,op3)
            elif operacion.operador == OPERACION_BINARY_STRING.SET_BYTE: return f.func_set_byte(op1,op2,op3)
        

    elif isinstance(operacion, Operacion_Patron):
        op1 = resolver_operacion(operacion.op1,ts)
        if operacion.operador == OPERACION_PATRONES.BETWEEN: return f.Between(op1,operacion.op2,ts)
        elif operacion.operador == OPERACION_PATRONES.NOT_BETWEEN: return not(f.Between(op1,operacion.op2,ts))
        elif operacion.operador == OPERACION_PATRONES.IN: return f.In(op1,operacion.op2,ts)
        elif operacion.operador == OPERACION_PATRONES.NOT_IN: return not(f.In(op1,operacion.op2,ts))
        elif operacion.operador == OPERACION_PATRONES.LIKE: return f.Like(op1,operacion.op2,ts)
        elif operacion.operador == OPERACION_PATRONES.NOT_LIKE: return not(f.Like(op1,operacion.op2,ts))
        elif operacion.operador == OPERACION_PATRONES.ILIKE: return f.Ilike(op1,operacion.op2,ts)
        elif operacion.operador == OPERACION_PATRONES.NOT_ILIKE: return not(f.Ilike(op1,operacion.op2,ts))
        elif operacion.operador == OPERACION_PATRONES.SIMILAR: return f.Similar(op1,operacion.op2,ts)
        elif operacion.operador == OPERACION_PATRONES.NOT_SIMILAR: return not(f.Similar(op1,operacion.op2,ts))
    elif isinstance(operacion, Operacion_NOW): return f.Now()
    elif isinstance(operacion, Operacion_CURRENT):
        if operacion.tipo=="date": return f.Date()
        else: return f.Time()
    elif isinstance(operacion, Operando_EXTRACT): return f.Extract(operacion.medida,operacion.valores,ts)
    elif isinstance(operacion, Operacion_DATE_PART): return f.Date_Part(operacion.val1,operacion.val2,ts)
    elif isinstance(operacion, Operacion_TIMESTAMP):
        op = resolver_operacion(operacion.valor,ts) 
        if op=='now': return f.Now()
    elif isinstance(operacion, Operacion_Great_Least):
        if operacion.tipo == 'greatest': return f.Greatest(operacion.expresion,ts)
        else: return f.Least(operacion.expresion,ts)
    

def procesar_instrucciones(instrucciones, ts) :
    ## lista de instrucciones recolectadas
    global Errores_Semanticos
    global listaInstrucciones 
    listaInstrucciones  = instrucciones
    if instrucciones is not None:
        for instr in instrucciones :
            if isinstance(instr, CrearBD) : crear_BaseDatos(instr,ts)
            elif isinstance(instr, CrearTabla) : crear_Tabla(instr,ts)
            elif isinstance(instr, CrearType) : crear_Type(instr,ts)
            elif isinstance(instr, EliminarDB) : eliminar_BaseDatos(instr,ts)
            elif isinstance(instr, EliminarTabla) : eliminar_Tabla(instr,ts)
            elif isinstance(instr, Insertar) : insertar_en_tabla(instr,ts)
            elif isinstance(instr, Actualizar) : actualizar_en_tabla(instr,ts)
            elif isinstance(instr, Eliminar) : eliminar_de_tabla(instr,ts)
            elif isinstance(instr, DBElegida) : seleccion_db(instr,ts)
            elif isinstance(instr, MostrarDB) : mostrar_db(instr,ts)
            elif isinstance(instr, ALTERDBO) : AlterDBF(instr,ts)
            elif isinstance(instr, ALTERTBO) : AlterTBF(instr,ts)
            elif isinstance(instr, MostrarTB) : Mostrar_TB(instr,ts)
            else: 
                for val in instr:
                    if(isinstance (val,SELECT)): 
                        if val.funcion_alias is not None:
                            ejecutar_select(val,ts)
                        else:
                            select_table(val,ts)
                    else : print('Error: instrucción no válida')      
    else: agregarMensjae('error','El arbol no se genero debido a un error en la entrada','')
    Reporte_Errores_Sem(Errores_Semanticos)  







def Analisar(input):
    reiniciarVariables()#reiniciar variables (revisar algunas son para pruebas)
    instrucciones = g.parse(input)
    print(instrucciones)
    ts_global = TS.TablaDeSimbolos()
    procesar_instrucciones(instrucciones,ts_global)

    #crea la consola y muestra el resultado
    global outputTxt
    consola = tkinter.Tk() # Create the object
    consola.geometry('950x200')
    text = tkinter.Text(consola,height=200, width=1280)
    consola.title("Consola")
    text.pack()
    text.insert(END,outputTxt)
    return outputTxt

#Metodos para graficar el ast 
def generarAST():
    global listaInstrucciones
    astGraph = DOTAST()
    astGraph.getDot(listaInstrucciones)


#Metodo para generar los reportes gramaticales 
def generarGASC():
    global listaInstrucciones
    r_asc = Reporte_Gramaticas()
    r_asc.grammarASC(listaInstrucciones)

def generarGDSC():
    '''global listaInstrucciones
    r_asc = Reporte_Gramaticas()
    r_asc.grammarDSC(listaInstrucciones)'''

#metodo para mostrar las tablas temporales
def mostrarTablasTemp():
    global listaTablas
    misTablas=[]
    
    for tab in listaTablas:
        texTab=PrettyTable()
        texTab.title='DB:'+tab.basepadre+'\tTABLA:'+tab.nombre
        texTab.field_names = ["nombre","tipo","size","precision","unique","anulable","default","primary","foreign","refence","check"]
        #recorrer las columans
        if tab.atributos!=None:
            for col in tab.atributos:
                texTab.add_row([col.nombre,col.tipo,col.size,col.precision,col.unique,col.anulable,col.default,col.primary,col.foreign,col.refence,col.check])
        misTablas.append(texTab)
    #agregar tabla de simbolos a los reportes
    misTablas.append(generarTSReporte())

    return misTablas

def generarTSReporte():
    global outputTS
    textTs=PrettyTable()
    textTs.title='REPORTE TABLA DE SIMBOLOS'
    textTs.field_names=['instruccion','identificador','tipo','referencia','dimension']
    for x in outputTS:
        textTs.add_row([x.instruccion,x.identificador,x.tipo,x.referencia,x.dimension])
    return textTs
   
'''
#usar las tablas
table = PrettyTable()
table.title = 'Results for method Foo'
table.field_names = ['Experiment', 'Value']
table.add_row(['bla', 3.14])
table.add_row(['baz', 42.0])

Salida
+-------------------------+
|  Results for method Foo |
+---------------+---------+
|   Experiment  |  Value  |
+---------------+---------+
|      bla      |   3.14  |
|      baz      |   42.0  |
+---------------+---------+

'''