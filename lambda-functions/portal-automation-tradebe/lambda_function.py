from typing import Dict, Any, List, Optional, Tuple
import json
import re

from mapper_factory import MapperFactory

def lambda_handler(event, context):

    print(event['body'])
    try:
        # Get data from the event
        data = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        
        # Get target portal
        target_portal = data.pop('targetPortal', None)  # Remove portal from data and store it
        print(f'Target portal: {target_portal}')
        if not target_portal:
            raise ValueError("Target portal not specified in request")
            
        # Get appropriate mapper from factory
        mapper = MapperFactory.get_mapper(target_portal)
        
        # Map the profile data
        mapped_data = mapper.map_profile(data)

        # Return successful response with mapped data
        return {
            'statusCode': 200,
            'body': json.dumps(mapped_data),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        # Return error response
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
