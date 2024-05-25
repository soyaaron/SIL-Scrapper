import requests
import json 
import uuid
from azure.cosmos import CosmosClient, PartitionKey, exceptions


resp = []
formatted_data = []
resumen_sesion = []
asistencia = []

#********** GET ID SESION ************
sesiones_url = "https://www.diputadosrd.gob.do/sil/api/sesion/sesiones?page=1&keyword="

response_sesiones = requests.get(sesiones_url)
r  = response_sesiones.json()

id_sesion = str(r['results'][0]['sesionId'])

#********** GET ID ASISTENCIA ************
sesiones_url = "https://www.diputadosrd.gob.do/sil/api/asistencia/sesion/?sesionId="+id_sesion

response_resumen_asistencia = requests.get(sesiones_url)
r  = response_resumen_asistencia.json()
id_asistencia = str(r['id'])

resumen_sesion.append({
    'id_asistencia': r['id'],
    'id_sesion': r['sesion']['id'],
    'numero': r['sesion']['numero'],
    'lugar': r['sesion']['lugar'],
    'fecha':r['fecha'],
    'cantidadDelegados':r['cantidadAsistencia']['cantidadDelegados'],
    'cantidadPresentes':r['cantidadAsistencia']['cantidadPresentes'],
    'cantidadAusentes':r['cantidadAsistencia']['cantidadAusentes'],
    'totalLegisladores':r['cantidadAsistencia']['totalLegisladores'],
})
#formatted_data.append({'resumen_sesion':resumen_sesion})


#*********************** GET LISTA ASISTENCIA ***************************************


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
        
        asistencia.append({
            'legisladorId': legislador_id,
            'nombreCompleto': nombre_completo,
            'presente': presente,
            'excusa': excusa
        })
    
formatted_data.append({
    'sesion':({
    'resumen_sesion':resumen_sesion,
    'asistencia':asistencia 
    })
    })

formatted_data = [
    {
        'id': str(uuid.uuid4()),  # Generate a unique ID for the document
        'sesion': {
            'resumen_sesion': resumen_sesion,
            'asistencia': asistencia 
        }
    }
]


#with open("gente.json","w", encoding='utf-8') as write_file:
#    json.dump(formatted_data, write_file, ensure_ascii=False, indent=4)

#************* Cosmos DB handling ************

endpoint = "https://sil-bot-db.documents.azure.com:443/"
key="o5YF7FZfkqIJWAG8vqh5LciXwPst5IwloqPqszb4LMB9gkFQXo73MMFWuzeCjF5pw9ggHpP9FYJxACDbtbdGHw=="
database_name="ToDoList"
container_name="Sesiones"

client = CosmosClient(endpoint, key)
database = client.create_database_if_not_exists(id=database_name)
container = database.create_container_if_not_exists(
 id=container_name,
 partition_key=PartitionKey(path="/azureid"),
 offer_throughput=400   
)

for item in formatted_data:
    try:
        container.create_item(body=item)
        print("Item created successfully")
    except exceptions.CosmosResourceExistsError:
        print("Item already exists")
    except exceptions.CosmosHttpResponseError as e:
        print(f"An error occurred: {e.message}")

print("Upload complete")
