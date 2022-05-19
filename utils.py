from datetime import datetime
from dateutil.parser import parse
import math
import json
import requests
import os
from dotenv import load_dotenv

def revisarWarning(z: dict,l:dict) ->bool:
    """ Funcion para revisar que no venga algun dato sospechoso, como una fecha que no es hoy o registros de entrada muy altos. """
    hoy=datetime.today()
    fecha=[]

    for llave1 in l:
        #Nos apoyamos en un diccionario para extraer la hora y registro de entradas de la llave actual
        registroHora=l[llave1]
        for llave2 in registroHora:
            hora=llave2
            registro=registroHora[llave2]
            fecha.append(hora[0:10].split('-'))


    for llave1 in z:
        registroHora=z[llave1]
        for llave2 in registroHora:
            hora=llave2
            registro=registroHora[llave2]                     
            fecha.append(hora[0:10].split('-'))

    for f in fecha:
        if f[0]!=hoy.year:
            return False 
        elif f[1]!=hoy.month:
            return False
        elif f[2]!=hoy.day:
            return False
    
    return True

def obtenerFix(fecha: str) -> str:
    """Funcion de apoyo para obtener el fix de una fecha en formato -XXXX"""
    #Objeto datetime
    Dt=parse(fecha.replace('"',''))
    fix=Dt.strftime('%z')
    return fix

def obtenerHora(fecha: str) -> str:
    """Funcion de apoyo para obtener la hora de un string en formato Y-m-d H:M:S"""
    Dt=parse(fecha.replace('"',''))
    f=Dt.strftime('%Y-%m-%d %H:%M:%S')
    return f
    
def getDistance(signal_str : float) -> float:
    """Función para calcular la distancia de un dispositivo al router en metros"""
    fpsl=27.55
    MHz=2417
    dBm=signal_str
    distance=math.pow(10,(( fpsl - (20 * math.log10(MHz)) + abs(dBm) ) / 20 ))
    return distance

def slackMessage(errors: str,n_errores: int) -> None:
    """Función para enviar un mensaje con los errores de la ejecución a un canal de slack mediante webhooks-"""
    data={
        "text":'Se han encontrado un total de '+str(n_errores)+' errores.'+errors
    }
    requests.post(getEnvironVar('SLACK_HOOD'),json.dumps(data))

def getEnvironVar(varName: str)->str:
    """Función para obtener las variables de entorno del archivo .env.gpg"""
    root = os.path.dirname(os.path.realpath(__file__))
    os.system('gpg '+root+'/.env.gpg')    #Remplazar por al ruta del archivo .env.gpg con las variables de entorno 
    load_dotenv(os.path.join(root,'.env'))  #Remplazar por la ruta el .env generado
    variable=os.getenv(varName)
    if os.path.exists(os.path.join(root,'.env')):   #Remplazar estas dos líneas por la ruta del .env generado
        os.remove(os.path.join(root,'.env'))
    return variable
    

def formatId(id: str)->str:
    """ Función para darle formato a un id con los : """
    string_split=[id[i:i+2] for i in range(0, len(id), 2)]
    new_string=''
    for s in string_split:
        new_string+=s+':'
    return new_string[:-1]  