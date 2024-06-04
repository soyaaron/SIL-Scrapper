import os
import requests
import json
import uuid
from azure.cosmos import CosmosClient, PartitionKey, exceptions

# Read environment variables
endpoint = os.getenv("ENDPOINT")
key = os.getenv("KEY")
database_name = os.getenv("DATABASE_NAME")
container_name = os.getenv("CONTAINER_NAME")

client = CosmosClient(endpoint, key)
database = client.create_database_if_not_exists(id=database_name)
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/azureid"),
    offer_throughput=400
)

resp = []
formatted_data = []
resumen_sesion = []
asistencia = []

# **************Consulta sesion mas reciente en BD *********************
query_sesion = f"""select top 1 c.sesion.resumen_sesion[0].id_sesion from c order by c.sesion.resumen_sesion[0].id_sesion desc"""
items = list(container.query_items(
    query=query_sesion,
    enable_cross_partition_query=True
))
id_last_sesion = items[0]['id_sesion']
print(items[0]['id_sesion'])

# ********** GET ID SESION ************
sesiones_url = "https://www.diputadosrd.gob.do/sil/api/sesion/sesiones?page=1&keyword="

response_sesiones = requests.get(sesiones_url)
r = response_sesiones.json()

id_sesion = str(r['results'][0]['sesionId']) 

# ******************** validacion sesion reciente. ***********
if id_sesion == id_last_sesion:
    print('funciono', id_sesion, id_last_sesion)

for id_sesion in range(int(id_last_sesion) + 1, int(id_sesion)):

    # ********** GET ID ASISTENCIA ************
    sesion_url = f"https://www.diputadosrd.gob.do/sil/api/asistencia/sesion/?sesionId={id_sesion}"

    response_resumen_asistencia = requests.get(sesion_url)
    r = response_resumen_asistencia.json()
    id_asistencia = str(r['id'])

    resumen_sesion.append({
        'id_asistencia': r['id'],
        'id_sesion': r['sesion']['id'],
        'numero': r['sesion']['numero'],
        'lugar': r['sesion']['lugar'],
        'fecha': r['fecha'],
        'cantidadDelegados': r['cantidadAsistencia']['cantidadDelegados'],
        'cantidadPresentes': r['cantidadAsistencia']['cantidadPresentes'],
        'cantidadAusentes': r['cantidadAsistencia']['cantidadAusentes'],
        'totalLegisladores': r['cantidadAsistencia']['totalLegisladores'],
        'source': 'https://www.diputadosrd.gob.do/sil/sesion/' + str(id_sesion)
    })
    # formatted_data.append({'resumen_sesion':resumen_sesion})

    # *********************** GET LISTA ASISTENCIA ***************************************

    for x in range(19):
        x_str = str(x + 1)
        asistencia_url = f'https://www.diputadosrd.gob.do/sil/api/asistencia/legisladores/?page={x_str}&id={id_asistencia}'

        response_asistencia = requests.get(asistencia_url)
        resp = response_asistencia.json()

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
        'sesion': ({
            'resumen_sesion': resumen_sesion,
            'asistencia': asistencia
        })
    })

    formatted_data = [
        {
            'id': str(uuid.uuid4()),
            'sesion': {
                'resumen_sesion': resumen_sesion,
                'asistencia': asistencia
            }
        }
    ]

    # ************* Cosmos DB handling ************

    for item in formatted_data:
        try:
            container.create_item(body=item)
            print("Item created successfully")
        except exceptions.CosmosResourceExistsError:
            print("Item already exists")
        except exceptions.CosmosHttpResponseError as e:
            print(f"An error occurred: {e.message}")

    print("Upload complete")
