import requests
import json
#********** GET ID SESION ************
sesiones_url = "https://www.diputadosrd.gob.do/sil/api/sesion/sesiones?page=1&keyword="

response_sesiones = requests.get(sesiones_url)
r  = response_sesiones.json()

id_sesion = str(r['results'][0]['sesionId'])
print(id_sesion)

#********** GET ID ASISTENCIA ************
sesiones_url = "https://www.diputadosrd.gob.do/sil/api/asistencia/sesion/?sesionId="+id_sesion

response_resumen_asistencia = requests.get(sesiones_url)
r  = response_resumen_asistencia.json()

id_asistencia = str(r['id'])
print(id_asistencia) 

#*********************** GET LISTA ASISTENCIA ***************************************
resp = []
formatted_data = []

for x in range(19):
    
    x_str = str(x+1)  
    asistencia_url = 'https://www.diputadosrd.gob.do/sil/api/asistencia/legisladores/?page='+x_str+'&id='+id_asistencia

    response_asistencia = requests.get(asistencia_url)
    resp= response_asistencia.json()


    for result in resp['results']:
        legislador = result['legislador']
        legislador_id = legislador['legisladorId']
        nombre_completo = legislador['nombreCompleto']
        presente = result['presente']
        excusa = result['excusa']
        
        
        formatted_data.append({
            'legisladorId': legislador_id,
            'nombreCompleto': nombre_completo,
            'presente': presente,
            'excusa': excusa
        })

with open("gente.json","w") as write_file:
    json.dump(formatted_data, write_file, indent=4)

print(formatted_data)