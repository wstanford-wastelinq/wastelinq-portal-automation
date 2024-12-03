import json
import os
import psycopg2

def lambda_handler(event, context):
   try:
       if not event.get('queryStringParameters', {}).get('id'):
           return {'statusCode': 400, 'body': 'missing id parameter'}

       id = event['queryStringParameters']['id']
       conn = get_db_connection()
       cur = conn.cursor()
       
       # Get all tables' data
       waste_name = get_table_data(cur, 'network', 'generator_customerprofile', id, id_param='id')
       waste_description = get_table_data(cur, 'network', 'generator_generatingprocessandmaterialcomposition', id, id_param='CustomerProfile_id')
       print(waste_description)
       waste_profile = get_multi_value_table_data(cur, 'network', 'generator_wasteprofilechemical', id, id_param='GeneratingProcessAndMaterialComposition_id')
       print(waste_profile)
       physical_properties = get_table_data(cur, 'network', 'generator_physicalandchemicalproperties', id, id_param='CustomerProfile_id')
       print(physical_properties)
       regulatory_info = get_table_data(cur, 'network', 'generator_regulatoryinformation', id, id_param='CustomerProfile_id')
       print(regulatory_info)
       shipping_info = get_table_data(cur, 'network', 'generator_shippingandpackaginginformation', id, id_param='CustomerProfile_id')
       print(shipping_info)
       #frequency_info = get_table_data(cur, 'network', 'communication_pricingrequeststream', id, id_param='CustomerProfile_id')
       #print(frequency_info)

       # Combine all results
       combined_result = {**waste_name, **waste_description, **waste_profile, **physical_properties, **regulatory_info, **shipping_info} # **frequency_info,  **epa_rcra_info, **land_ban_info}
       
       if combined_result:
           return {
               'statusCode': 200,
               'body': json.dumps(combined_result, default=str)
           }
       return {
           'statusCode': 404,
           'body': f'ID {id} not found'
       }

   except Exception as e:
       return {'statusCode': 500, 'body': str(e)}
   finally:
       if 'conn' in locals():
           cur.close()
           conn.close()

def get_db_connection():

    # Connect using credentials
    connection = psycopg2.connect(
        host=os.environ['DB_PROXY'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        dbname=os.environ['DB_NAME'],
        port=int(os.environ['DB_PORT']),
        connect_timeout=5)

    return connection

def get_table_data(cursor, schema, table, id, id_param='id'):
   sql_command = f'SELECT * FROM {schema}.{table} WHERE "{id_param}" = {id}'
   print(sql_command)
   cursor.execute(f'SELECT * FROM {schema}.{table} WHERE "{id_param}" = %s', (id,))
   columns = [desc[0] for desc in cursor.description]
   row = cursor.fetchone()
   return dict(zip(columns, row)) if row else {}

def get_multi_value_table_data(cursor, schema, table, id, id_param='id'):
   cursor.execute(f"""
       SELECT string_agg(CAST(id AS TEXT), ',') as ids,
              string_agg(CAST("ChemicalPhysicalComposion" AS TEXT), ',') as "ChemicalPhysicalComposion",
              string_agg(CAST("CAS" AS TEXT), ',') as "CAS",
              string_agg(CAST("Typical" AS TEXT), ',') as "Typical",
              string_agg(CAST("Min" AS TEXT), ',') as "Min",
              string_agg(CAST("Max" AS TEXT), ',') as "Max",
              MAX("UnitType") as "UnitType"
       FROM {schema}.{table}
       WHERE "{id_param}" = %s
       GROUP BY "{id_param}"
   """, (id,))
   
   columns = [desc[0] for desc in cursor.description]
   row = cursor.fetchone()
   return dict(zip(columns, row)) if row else {}