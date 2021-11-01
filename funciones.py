import time
from io import open
import rrdtool
import os
from pysnmp.hlapi import *
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import threading
from pdf_mail import sendpdf

def agregarElemento (lista,comunidad,direccion,version,puerto, tarifa):
    if(lista[0]==0):
        lista.pop()
    lista.extend([direccion,comunidad,version,puerto,tarifa])

def guardarAgentes(lista):
    try:
        archivo = open("agentes.txt", "w")
        i = 0
        while i < len(lista):
            a = lista[i]
            archivo.write(a + "\n")
            i += 1
        archivo.close()
        print("\nAgentes guardados\n")
    except:
        print("No fue posible guardar los agentes")

def leerAgentes(lista):
    try:
        archivo = open("agentes.txt", "r")
        lista = archivo.read().split("\n")
        lista.pop()
        archivo.close()
        print(lista, "Numero de agentes monitorizados:",len(lista)/5)
        return lista
    except:
        print("No se pudo leer los agentes")

def imprimirLista (lista):
    print(lista[:])

def eliminarAgente (lista,direccion):
    try:
        dex=lista.index(direccion)
        dex2=dex+4
        i=int(dex)
        i=(i/5)+1
        try:
            archivo="agente"+str(int(i))
            os.remove("/home/mint2/Documentos/Practica_2/RRD/"+archivo+".rrd")
            os.remove("/home/mint2/Documentos/Practica_2/RRD/"+archivo + ".xml")
            os.remove("/home/mint2/Documentos/Practica_2/IMG/"+archivo + "TCP.png")
            os.remove("Reporte de agentes.pdf")
        except:
            print("No hay archivos")
        while (dex<=dex2):
            lista.pop(dex2)
            dex2-=1
    except:
       print("No hay agentes")

def consultaSNMP(comunidad,host,oid,puerto):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData(comunidad),
               UdpTransportTarget((host, puerto)),
               ContextData(),
               ObjectType(ObjectIdentity(oid))))

    if errorIndication:
        resultado=errorIndication
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    else:
        for varBind in varBinds:
            varB=(' = '.join([x.prettyPrint() for x in varBind]))
            resultado= varB.split()[2]
    return resultado

def consultaSNMP2(comunidad,host,oid,puerto):
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData(comunidad),
               UdpTransportTarget((host, puerto)),
               ContextData(),
               ObjectType(ObjectIdentity(oid))))

    if errorIndication:
        resultado=errorIndication
    elif errorStatus:
        print('%s at %s' % (errorStatus.prettyPrint(),errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
    else:
        for varBind in varBinds:
            varB=(' = '.join([x.prettyPrint() for x in varBind]))
            resultado= varB.split()[14]
    return resultado

def estadoAgente (lista):
    tamaño=int(len(lista))/5
    print("Número de agentes monitorizados",tamaño)
    i=0
    j=0
    while (i<tamaño):
        resultado=consultaSNMP(lista[j+1],lista[j],'1.3.6.1.2.1.1.1.0',int(lista[j+3]))
        if(str(resultado)=="No SNMP response received before timeout"):
            print("Estado del agente",i+1,": down")
        else:
            print("Estado del agente",i+1,": up")
            resultado=consultaSNMP(lista[j+1],lista[j],'1.3.6.1.2.1.2.1.0',lista[j+3])
            print("El número de interfaces de red del agente",i+1,"son:", resultado)
        i+=1
        j+=5

def createRRD(nombre):
    nombre+=".rrd"
    ret = rrdtool.create("/home/mint2/Documentos/Practica_3/RRD/"+nombre,
                         "--start", 'N',
                         "--step", '60',
                         "DS:TCPOut:COUNTER:600:U:U",
                         "RRA:AVERAGE:0.5:1:50",
                         )

    if ret:
        print(rrdtool.error())
    else :
        print("Creación satisfactoria")

def updateRRD (lista, agente, nombre, tiempo):
    timeout = time.time() + tiempo
    xml=nombre+".xml"
    nombre+=".rrd"
    rrdpath = '/home/mint2/Documentos/Practica_3/RRD/'
    j=(agente-1)*5
    Total=0
    Inicio= int(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.6.11.0', int(lista[j + 3])))
    while 1:
        if time.time() > timeout:
            break
        carga_TCP = int(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.6.11.0', int(lista[j + 3])))
        carga_TCP1 = int(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.6.12.0', int(lista[j + 3])))
        carga_TCP +=carga_TCP1
        Total+=carga_TCP-Inicio
        Inicio=carga_TCP
        valor = "N:" + str(carga_TCP)
        print(Total)
        rrdtool.update(rrdpath + nombre, valor)
        rrdtool.dump(rrdpath + nombre, rrdpath + xml)
        time.sleep(1)
    creacionGraphU(lista, agente, tiempo)
    reporte(lista, agente, Total)



def graphRRD(nombre, tiempo, agente):
    rrdpath = '/home/mint2/Documentos/Practica_3/RRD/'
    imgpath = '/home/mint2/Documentos/Practica_3/IMG/'
    j=(agente-1)*4
    ultima_lectura = int(rrdtool.last(rrdpath + nombre +".rrd"))
    tiempo_final = ultima_lectura
    tiempo_inicial = tiempo_final - tiempo
    ret = rrdtool.graphv(imgpath + nombre + "TCP.png",
                         "--start", str(tiempo_inicial),
                         "--end", str(tiempo_final),
                         "--vertical-label=TCP Traffic",
                         "--title=Trafico de red (TCP)",

                         "DEF:TCPOut=" + rrdpath + nombre + ".rrd:TCPOut:AVERAGE",
                         "AREA:TCPOut#00FF00:Carga de RED")

def creacion(lista):
    agente = int(input("Indique el número del agente: "))
    nombre="agente"+str(agente)
    createRRD(nombre)
    tiempo=int(input("Tiempo de ejecuci+on de update en segundos: "))
    thread = threading.Thread(name="hilo1", target=updateRRD, args=(lista,agente,nombre,tiempo,))
    thread.start()

def creacionGraph (lista):
    agente = int(input("Ingresa el numero de agente: "))
    nombre="agente"+str(agente)
    tiempo = int(input("Ingresa el tiempo utlizado en segundos: "))
    graphRRD(nombre, tiempo,agente,lista)
    print("Operación exitosa\n\n")

def creacionGraphU (lista, ag, t):
    agente = ag
    nombre="agente"+str(agente)
    tiempo = int(t)
    graphRRD(nombre, tiempo,agente)
    print("Operación exitosa\n\n")

def tarifa(lista, agente, total):
    i= (agente-1)*5
    precio=(50)*int(lista[i+4])
    cantidad =(50000)*int(lista[i+4])
    if(total > cantidad):
        var= "El agente "+ str(agente) + " supero el limite propuesto se le aplicara un cargo de $25 por cada 150 paquetes extra"
        cantidad =total-cantidad
        precio= precio + (cantidad/150)*25
        var+="\nSu monto final es de: $"+str(precio)+"MXN"
        return var
    else :
        var = "El agente " + str(agente) + " mantuvo su consumo dentro de lo acordado \n El monto final es de:"+ str(precio) + "MXN"
        return var

def generarPDF (lista,agente, total):
    j=0
    c=canvas.Canvas("Agente"+str(agente)+".pdf", pagesize=A4)
    h=A4
    path="/home/mint2/Documentos/Practica_3/IMG/"
    print(lista[j + 2])
    if lista[j + 2] == "windows":
        c.drawImage("Windows.jpeg", 20, h[1] - 60, width=50, height=50)
        text = c.beginText(50, h[1] - 80 )
        text.textLines(
            "\n\n\nNombre: " + str(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.1.5.0', lista[j + 3])) + "   "
            + "Version: " + str(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.1.2.0', lista[j + 3])) + "    "
            + "   SO: " + str(consultaSNMP2(lista[j + 1], lista[j], '1.3.6.1.2.1.1.1.0', lista[j + 3])) + "\n"
            + "Ubicacion: " + str(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.1.6.0', lista[j + 3])) + "\n"
            + "Puerto: " + str(lista[j + 3]) + " Tiempo de Actividad: " + str(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.1.3.0', lista[j + 3])) + "\n"
            + "Comunidad: " + str(lista[j + 1]) + " IP: " + str(lista[j]) + " Tipo de tarifa (Alta=3, Media=2, Baja=1):  " + str(lista[j + 4]) + "\nFactura para "+str(total)+" paquetes enviados\n" + str(tarifa(lista, agente, total)))
        c.drawText(text)
        c.drawImage(path + "agente" + str(agente) + "TCP.png", 50, h[1] - 315 , width=248, height=143)
        j += 4
    else:
        c.drawImage("mint.png", 20, h[1] - 60 , width=50, height=50)
        text = c.beginText(50, h[1] - 80 )
        text.textLines(
            "\n\n\nNombre: " + str(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.1.5.0', lista[j + 3])) + "   "
            + "Version: " + str(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.1.2.0', lista[j + 3])) + "    "
            + "   SO: " + str(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.1.1.0', lista[j + 3])) + "\n"
            + "Ubicacion: " + str(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.1.6.0', lista[j + 3])) + "\n"
            + "Puerto: " + str(lista[j + 3]) + " Tiempo de Actividad: " + str(consultaSNMP(lista[j + 1], lista[j], '1.3.6.1.2.1.1.3.0', lista[j + 3])) + "\n"
            + "Comunidad: " + str(lista[j + 1]) + " IP: " + str(lista[j]) + " Tipo de tarifa (Alta=3, Media=2, Baja=1):  " + str(lista[j + 4]) + "\nFactura para " +str(total)+" paquetes enviados\n" + str(tarifa(lista, agente, total)))
        c.drawText(text)
        c.drawImage(path + "agente" + str(agente) + "TCP.png", 50, h[1] - 315, width=248, height=143)
        j += 4

    c.showPage()
    c.save()

def reporte(lista, agente, total):
    generarPDF(lista, agente, total)
