import configparser
import requests
import uuid
from azure.cosmos import CosmosClient, exceptions, PartitionKey

config = configparser.ConfigParser()
config.read('config.ini')

endpoint = config.get('Database','endpoint')
key = config.get('Database','key')
database_name = config.get('Database','database_name')
container_name = config.get('Database','container_name')

# Initialize the Cosmos client
client = CosmosClient(endpoint, key)
database = client.create_database_if_not_exists(id=database_name)
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/azureid"),
    offer_throughput=400
)

# Iterate over the range of session IDs
for id_sesion in range(133299, 133317):
    resumen_sesion = []
    asistencia = []

    #********** GET ID ASISTENCIA ************
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
        'source': f'https://www.diputadosrd.gob.do/sil/sesion/{id_sesion}'
    })

    #*********************** GET LISTA ASISTENCIA ***************************************
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

    formatted_data = [{
        'id': str(uuid.uuid4()),  # Generate a unique ID for the document
        'sesion': {
            'resumen_sesion': resumen_sesion,
            'asistencia': asistencia
        }
    }]

    #************* Cosmos DB handling ************
    for item in formatted_data:
        try:
            container.create_item(body=item)
            print(f"Item for session {id_sesion} created successfully")
        except exceptions.CosmosResourceExistsError:
            print(f"Item for session {id_sesion} already exists")
        except exceptions.CosmosHttpResponseError as e:
            print(f"An error occurred for session {id_sesion}: {e.message}")

print("Upload complete")
