from pydantic import BaseModel
from hololinked.server.td import JSONSchema

class TriggerReader(BaseModel):
    instance_name: str
    address: str
    protocol : str

    def json(self):
        return self.model_dump(mode='json')
    
JSONSchema.register_type_replacement(TriggerReader, 'object', TriggerReader.model_json_schema())



toggle_shot_counting_schema = {
    'type' : 'object', 
    'properties' : {
        'value' : {'type' : 'boolean'}
    }, 
    'required' : ['value']
}