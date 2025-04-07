from typing import List, Optional,get_args
from pydantic import create_model, Field, ConfigDict
import json
import logging
logger = logging.getLogger(__name__)

class DynamicGenSchema():
    
    def __init__(self,fields: dict) -> None:
        self.__fields = fields
        logger.info("Initializing DynamicGenSchema with fields")
        
        # Dynamically generate the Extract_Data model.
        Extract_Data = self.generate_dynamic_model(self.__fields)
        logger.info("Extract_Data model generated successfully")

        # Now, create the Data_Objects model dynamically
        self.__pydantic_model= self.generate_data_objects_model(Extract_Data)
        logger.info("Data_Objects model generated successfully")
    
    def generate_dynamic_model(self,fields: dict):
        """
        Dynamically creates a Pydantic model based on user-defined fields.
        Parameters:
            fields (dict): Mapping from field names to their description strings.
        Returns:
            A new Pydantic model class.
        """
        field_definitions = {
            field_name: (Optional[str], Field(default=None, description=description))
            for field_name, description in fields.items()
        }
        model = create_model('Extract_Data', **field_definitions)
        logger.debug("Dynamic model Extract_Data created with definitions")
        return model


    def generate_data_objects_model(self,Extract_Data):
        """
        Dynamically creates a Data_Objects model that holds a list of Extract_Data objects.
        """
        logger.debug("Generating Data_Objects model using inner model: %s", Extract_Data)
        Data_Objects = create_model(
            'Data_Objects',
            data=(List[Extract_Data], Field(default_factory=list, description="A list of extracted data objects."))
        )
        
        # Apply the custom configuration.
        Data_Objects.model_config = ConfigDict(
            validate_assignment=False,    # Disable validation on assignment
            extra='allow',                # Allow extra fields
            arbitrary_types_allowed=True  # Allow arbitrary types
        )
        logger.debug("Custom configuration applied to Data_Objects model")
        
        # Add the to_json_string method to the model.
        def to_json_string(self):
            logger.debug("Converting model to JSON string")
            return json.dumps(self.model_dump(mode='json'), indent=4)
        
        setattr(Data_Objects, 'to_json_string', to_json_string)
        logger.debug("to_json_string method attached to Data_Objects model")
        
        return Data_Objects
    
    @classmethod
    def create_model(cls, fields: dict):
        """Factory method to return the generated Pydantic model."""
        instance = cls(fields)
        return instance.__pydantic_model
# Example usage:
if __name__ == "__main__":
    # Create an instance of the dynamically generated Data_Objects with one Extract_Data object.
    # Example dynamic fields (user input)
    import re
    def validate_keys_are_snake_case(user_fields):
        """
        Validates that all keys in the user_fields dictionary adhere to snake_case naming conventions.

        Parameters:
            user_fields (dict): A dictionary with keys to validate.

        Returns:
            bool: True if all keys are valid; raises ValueError otherwise.
        """
        snake_case_pattern = re.compile(r'^[a-z]+(_[a-z\d]+)*$')
        for key in user_fields.keys():
            if not snake_case_pattern.match(key):
                raise ValueError(f"Invalid key '{key}': Keys must be in snake_case format.")
        return True
    
    user_fields = {
        'numeric_value': (
            "A numeric value extracted from the research paper. This may represent a measured parameter such as thickness, "
            "retention time, or endurance cycles."
        ),
        'switching_layer_material': (
            "The material used in the switching layer of the device. For example, it could be a metal oxide such as TiO2 or HfO2."
        ),
        # ... add other fields as needed.
    }
    try:
        if validate_keys_are_snake_case(user_fields):
            print("All keys are valid snake_case identifiers.")
    except ValueError as e:
        raise e
    dynamic_schema = DynamicGenSchema.create_model(user_fields)
    DataObjectModel = dynamic_schema
    # Use get_args to extract the type of the inner model from the 'data' field annotation.
    ExtractDataModel = get_args(DataObjectModel.model_fields['data'].annotation)[0]
    
    # Create an instance of the inner model.
    extract_data_instance = ExtractDataModel(numeric_value='123.45', switching_layer_material='TiO2')
    
    # Now create an instance of the DataObjectModel containing the inner instance.
    data_instance = DataObjectModel(data=[extract_data_instance])
    print(data_instance.to_json_string())
    print(DataObjectModel.model_json_schema())
    # Optionally, view the generated JSON schema
    print("\n\n-----------------------------")
    def generate_dynamic_prompt(fields: dict):
        """
        Generates a dynamic prompt and mapping dictionary based on schema fields.
        
        Parameters:
            fields (dict): A dictionary where keys are schema variable names and
                        values are descriptions (not used for the prompt here).
        
        Returns:
            tuple: (prompt: str, mapping: dict) where:
                - prompt is a string containing the dynamically generated extraction prompt.
                - mapping is a dictionary mapping lower-case, space-separated keys to schema variable names.
        """
        mapping = {}
        prompt_items = []
        for field in fields:
            # Convert field names to a more readable format.
            display_key = field.replace('_', ' ')
            mapping[display_key] = field
            prompt_items.append(f"- {display_key}")
        
        prompt = f"""
    Please read the provided PDF thoroughly and extract the following quantities. Your output must be a table with two columns: "Quantity" and "Extracted Value". For each of the items listed below, provide the extracted value exactly as it appears in the document. If an item is not found, simply enter "N/A" for that field. Ensure that any numerical values include their associated units (if applicable) and that you handle multiple values consistently.

    Extract the following items:
    {chr(10).join(prompt_items)}

    Instructions:
    1. Analyze the entire PDF document to locate all references to the above items.
    2. Extract each quantity with precision; include any units and relevant details.
    3. If multiple values are present for a single item, list them clearly (e.g., separated by commas).
    4. Format your output strictly as a table with two columns: one for the "Quantity" and one for the "Extracted Value".
    5. Do not include any extra text, headings, or commentary—only the table is required.
    6. If an item cannot be found, record it as "N/A" in the "Extracted Value" column.
    """
        return prompt, mapping
    temp1,temp2=generate_dynamic_prompt(user_fields)
    print(temp1,"\n\n",temp2)
    # print(Data_Objects.model_json_schema(indent=4))
