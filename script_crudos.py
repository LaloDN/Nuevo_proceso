import os 
import json
import shutil
import argparse
import logging
import mysql.connector
import pandas as pd   
from datetime import datetime  
from dateutil.parser import parse
from utils import getDistance, getEnvironVar, slackMessage, formatId


#region Variables de log globales y root
buen=0
buenos='\n'
mal=0
malos='\n'
war=0
warning='\n'
root = os.path.dirname(os.path.realpath(__file__))
#endregion

def crudosWireless(file: str, user_db: str ,password_db: str) -> None:
    """ Funcion para extraer los datos de los archivos que terminen con _wireless"""
    #region variables
    global buen
    global buenos
    global mal
    global malos
    global war
    global warning
    global root
    #endregion
    try:
        with open(os.path.join(root,'Archivos',file)) as f:

            #region Pre-proceso
            jsArch=json.load(f)
            mac_address=jsArch['wifi_bt_data']['sensor_info']['serial_number']

            #Conexión base de datos
            connection = mysql.connector.connect(host='localhost',
                                         database='DB_prueba_corregido',
                                         user=user_db,
                                         password=password_db)
            try:
                cursor=connection.cursor()
            except:
                print('Error: las credenciales para acceder a la base de datos no son correctas')
                logging.critical('Intento fallido de conectar a la base de datos, las credenciales no parecen ser correctas')
                logging.info('\nFin de la ejecución '+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'\n---------------------------------\n')
                quit()
                
            #Verificar nodos y zonas
            cursor.callproc('spCheckNodo',[mac_address,])
            connection.commit()  
            result=cursor.callproc('spGetZoneNode',[mac_address,0,])
            zona=result[1]
            #endregion
            
            if zona==None:
                logging.warning('ATENCIÓN: Aún no ha creado un registro zona ligado al nodo '+mac_address+' dentro de la base de datos.')
                war+=1
                warning+=file+'\n'
                if not os.path.exists(os.path.join(root,'Archivos','Warning_wireless')):
                    os.mkdir(os.path.join(root,'Archivos','Warning_wireless'))
                shutil.move(os.path.join(root,'Archivos',file),os.path.join(root,'Archivos','Warning_wireless'))
            else:
                #Csv con columnas    
                now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if not os.path.exists(os.path.join(root,now+'.csv')):
                    df=pd.DataFrame(columns=['id','mac_dispositivo','dispositivo_idd','mac_nodo','potencia','potencia_porcentaje','distancia','created','updated','zona_id','modified','distancia2','en_horario'])
                    df.to_csv(os.path.join(root,now+'.csv'),index=False)

                for reg in jsArch['wifi_bt_data']['records']:
                    date_from=reg['from']
                    #timestamp check
                    fecha=datetime.fromtimestamp(date_from/1000)  if type(date_from)==type(1) else parse(date_from)

                    for dev in reg['devices']:
                        id= formatId(dev['id']) if len(dev['id'])==12 else dev['id']
                        idd=str(int(dev['id'],16))
                        potencia=dev['signal_strength']
                        potencia_p=float(potencia)+130
                        distancia=getDistance(potencia)
            
                        df=pd.DataFrame({'id':'null','mac_dispositivo':id,'dispositivo_idd':idd,'mac_nodo':mac_address,'potencia':potencia,'potencia_porcentaje':potencia_p,'distancia':distancia,'created':fecha.strftime('%Y-%m-%d'),'updated':fecha.strftime('%H:%M:%S'),'zona_id':zona,'modified':fecha.strftime('%Y-%m-%d %H:%M:%S'),'distancia2':0,'en_horario':1},index=[0])
                        df.to_csv(os.path.join(root,now+'.csv'),mode='a',header=False,index=False)
                
                #region Archivo valido
                if not os.path.exists(os.path.join(root,'Archivos','Buenos_wireless')):
                    os.mkdir(os.path.join(root,'Archivos','Buenos_wireless'))
                shutil.move(os.path.join(root,'Archivos',file),os.path.join(root,'Archivos','Buenos_wireless'))                
                buen+=1
                buenos+=file+'\n'
                #endregion
        
    except Exception as e:
        #Datos para el log
        mal+=1
        malos+=file+'\n'
        logging.critical(e)
        #Error en la lectura
        if not os.path.exists(os.path.join(root,'Archivos','Errores_wireless')):
                os.mkdir(os.path.join(root,'Archivos','Errores_wireless'))
        shutil.move(os.path.join(root,'Archivos',file),os.path.join(root,'Archivos','Errores_wireless'))

       
def main():
    #region Ajustes previos
    parser = argparse.ArgumentParser(description='Script para filtrar datos leidos de un sensor')
    parser.parse_args()
    logging.basicConfig(filename=os.path.join(root,"app.log"),level="DEBUG")
    #Creamos el archivo de log con los archivos leidos
    logging.info('\n\n---------------------------------\nHora de ejecución:'+ datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    #endregion
   
    #region Variables 
    root
    #user=getEnvironVar('MYSQL_USER')
    #password=getEnvironVar('MYSQL_PASSWORD')
    user='eddy'
    password='SYdhtW8C8b%Vig'

    #endregion
    
    [crudosWireless(file,user,password) for file in os.listdir(os.path.join(root,'Archivos')) if file.endswith('_wireless.txt') or file.endswith('_wifi.txt')]


    #region Reporte de logs
    if buen+mal+war==0:
        logging.info('\nNo se han leido datos en este periodo')
    else:
        if buen>0:
            logging.info('\nNúmero de archivos buenos: '+str(buen)+'\nLista de archivos buenos:'+buenos)   
        if mal>0:
            logging.error('\nNúmero de archivos malos: '+str(mal)+'\nLista de archivos malos:'+malos)
        if war>0:                                   
            logging.warning('\nNúmero de archivos sospechosos: '+str(war)+'\nLista de archivos sospechosos:'+warning)
    #endregion
    logging.info('\nFin de la ejecución '+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'\n---------------------------------\n')
    
    #Nota: NO funciona dentro del servidor, el mensaje a slack solo funciona en máquinas locales
    #slackMessage('Se ha terminado la ejecucion del script') 
if __name__ == '__main__':
    main()
    
    
