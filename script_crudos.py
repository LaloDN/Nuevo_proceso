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


#region Variables de log globales
buen=0
buenos='\n'
mal=0
malos='\n'
war=0
warning='\n'
#endregion

def crudosWireless(file: str, user_db: str ,password_db: str,args: any) -> None:
    """ Funcion para extraer los datos de los archivos que terminen con _wireless"""
    #region variables
    global buen
    global buenos
    global mal
    global malos
    global war
    global warning
    #endregion
    try:
        with open(os.path.join(args.ruta_archivos,file)) as f:

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
                if not os.path.exists(args.ruta_warning):
                    os.mkdir(args.ruta_warning)
                shutil.move(os.path.join(args.ruta_archivos,file),args.ruta_warning)
            else:
                #Csv con columnas    
                now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if not os.path.exists(os.path.join(args.ruta_output,now+'.csv')):
                    df=pd.DataFrame(columns=['id','mac_dispositivo','dispositivo_idd','mac_nodo','potencia','potencia_porcentaje','distancia','created','updated','zona_id','modified','distancia2','en_horario'])
                    df.to_csv(os.path.join(args.ruta_output,now+'.csv'),index=False)

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
                        df.to_csv(os.path.join(args.ruta_output,now+'.csv'),mode='a',header=False,index=False)
                
                #region Archivo valido
                if not os.path.exists(args.ruta_buenos):
                    os.mkdir(args.ruta_buenos)
                shutil.move(os.path.join(args.ruta_archivos,file),args.ruta_buenos)                
                buen+=1
                buenos+=file+'\n'
                #endregion
        
    except Exception as e:
        #Datos para el log
        mal+=1
        malos+=file+'\n'
        logging.critical(e)
        #Error en la lectura
        if not os.path.exists(args.ruta_malos):
                os.mkdir(args.ruta_malos)
        shutil.move(os.path.join(args.ruta_malos,file),args.ruta_malos)

       
def main():
    
    
    #region Ajustes previos
    
    root = os.path.dirname(os.path.realpath(__file__))
    
    parser = argparse.ArgumentParser(description='Script para filtrar datos leidos de un sensor')
    parser.add_argument('--ruta_archivos',type=str,nargs='?',const=1,default=os.path.join(root,'Archivos'),help='Ruta con los archivos .json a procesar')
    parser.add_argument('--ruta_buenos',type=str,nargs='?',const=1,default=os.path.join(root,'Archivos','Buenos_wireless'),help='Ruta de la carpeta hacía donde se van a mover los archivos .json válidos')
    parser.add_argument('--ruta_malos',type=str,nargs='?',const=1,default=os.path.join(root,'Archivos','Errores_wireless'),help='Ruta de la carpeta hacía dodne se van a mover los archivos .json con errores en la lectura')
    parser.add_argument('--ruta_warning',type=str,nargs='?',const=1,default=os.path.join(root,'Archivos','Warning_wireless'),help='Ruta de la carpeta hacía donde se van a mover los archivos .json con errores en la lógica')
    parser.add_argument('--ruta_output',type=str,nargs='?',const=1,default=root,help='Ruta de la carpeta en donde se generarán los csv y el ouput de los logs')
    args=parser.parse_args()
    
    logging.basicConfig(filename=os.path.join(args.ruta_output,"app.log"),level="DEBUG")
    #Creamos el archivo de log con los archivos leidos
    logging.info('\n\n---------------------------------\nHora de ejecución:'+ datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    #endregion
   
    #region Variables 
    #user=getEnvironVar('MYSQL_USER')
    #password=getEnvironVar('MYSQL_PASSWORD')
    user='eddy'
    password='SYdhtW8C8b%Vig'

    #endregion
    if not os.path.exists(args.ruta_archivos):
        print('Error: Al parecer no existe la ruta '+args.ruta_archivos+' con los archivos a leer, intente revisar la ruta o crear el directorio de manera manual')
        logging.info('\nFin de la ejecución '+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'\n---------------------------------\n')
        quit()
    
    [crudosWireless(file,user,password,args) for file in os.listdir(args.ruta_archivos) if file.endswith('_wireless.txt') or file.endswith('_wifi.txt')]


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
    
    
