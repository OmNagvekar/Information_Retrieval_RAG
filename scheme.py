from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator
import json

class Extract_Text(BaseModel):
    """
    Contains information about extracted data from research papers.
    """
    numeric_value: Optional[str] = Field(default=None, description="A numeric value extracted from a research paper, representing parameters like thickness, retention time, endurance cycles, or other quantitative data in the given field.")
    switching_layer_material: Optional[str] = Field(default=None, description="Material of the switching layer (TYM_Class).")
    synthesis_method: Optional[str] = Field(default=None, description="Synthesis method used (SM_Class).")
    top_electrode: Optional[str] = Field(default=None, description="Material of the top electrode (TE_Class).")
    top_electrode_thickness: Optional[Union[str, float]] = Field(default=None, description="Thickness of the top electrode in nanometers (TTE in nm).")
    bottom_electrode: Optional[str] = Field(default=None, description="Material of the bottom electrode (BE_Class).")
    bottom_electrode_thickness: Optional[Union[str, float]] = Field(default=None, description="Thickness of the bottom electrode in nanometers (TBE in nm).")
    switching_layer_thickness: Optional[Union[str, float]] = Field(default=None, description="Thickness of the switching layer in nanometers (TSL in nm).")
    switching_type: Optional[str] = Field(default=None, description="Type of switching (TSUB_Class).")
    endurance_cycles: Optional[int] = Field(default=None, description="Endurance cycles (EC).")
    retention_time: Optional[Union[str, int]] = Field(default=None, description="Retention time in seconds (RT in seconds).")
    memory_window: Optional[Union[str, float]] = Field(default=None, description="Memory window in volts (MW in V).")
    num_states: Optional[str] = Field(default=None, description="Number of states (MRS_Class).")
    conduction_mechanism: Optional[str] = Field(default=None, description="Type of conduction mechanism (CM_Class).")
    resistive_switching_mechanism: Optional[str] = Field(default=None, description="Resistive switching mechanism (RSM_Class).")
    paper_name: Optional[str] = Field(default=None, description="Name of the research paper.")
    doi: Optional[str] = Field(default=None, description="DOI of the research paper.")
    year: Optional[int] = Field(default=None, description="Publication year of the research paper.")
    source: Optional[str] =Field(default=None,drescription="PDF File Name like Memory_characteristic.pdf or path to pdf file like C:\\Users\\Om Nagvekar\\OneDrive\\Documents\\KIT Assaignment & Notes& ISRO\\Shivaji University Nanoscience Dept. Projects\\IRP\\PDF\\8.pdf")
    custom: Optional[str]= Field(default=None,description="contains information does not fit into the specified format but it is usefull to the user query")
    
    # New fields to handle nested data
    input_data: Optional[Dict[str, Any]] = Field(default=None)
    output_data: Optional[Dict[str, Any]] = Field(default=None)
    reference_information: Optional[Dict[str, Any]] = Field(default=None)
    
    model_config = ConfigDict(
        validate_assignment = False,  # Disable validation on assignment
        extra = 'allow' , # Allow extra fields
        arbitrary_types_allowed = True
    )
    @model_validator(mode='before')
    @classmethod
    def transform_input(cls, data):
        """
        Transform input data to map nested fields
        """
        if isinstance(data, dict):
            # Map input_data fields
            if 'input_data' in data:
                input_mapping = {
                    'switching_layer_material': ['input_data', 'device_material'],
                    'top_electrode': ['input_data', 'top_electrodes'],
                    'bottom_electrode': ['input_data', 'bottom_electrodes'],
                    'top_electrode_thickness': ['input_data', 'thickness_of_top_electrode'],
                    'bottom_electrode_thickness': ['input_data', 'thickness_of_bottom_electrode'],
                    'switching_layer_thickness': ['input_data', 'thickness_of_switching_layer']
                }
                
                for model_key, nested_path in input_mapping.items():
                    try:
                        # Navigate through nested dictionary
                        current = data
                        for key in nested_path[:-1]:
                            current = current.get(key, {})
                        
                        # Set the value, handling potential list inputs
                        value = current.get(nested_path[-1])
                        if isinstance(value, list):
                            # If it's a list, take the first item or join
                            value = value[[0]] if value else None
                        
                        data[model_key] = value
                    except Exception:
                        pass
            
            # Map output_data fields
            if 'output_data' in data:
                output_mapping = {
                    'switching_type': ['output_data', 'type_of_switching'],
                    'endurance_cycles': ['output_data', 'endurance_cycles'],
                    'retention_time': ['output_data', 'retention_time'],
                    'memory_window': ['output_data', 'memory_window'],
                    'num_states': ['output_data', 'number_of_states'],
                    'conduction_mechanism': ['output_data', 'conduction_mechanism_type'],
                    'resistive_switching_mechanism': ['output_data', 'resistive_switching_mechanism']
                }
                
                for model_key, nested_path in output_mapping.items():
                    try:
                        # Navigate through nested dictionary
                        current = data
                        for key in nested_path[:-1]:
                            current = current.get(key, {})
                        
                        # Set the value
                        data[model_key] = current.get(nested_path[-1])
                    except Exception:
                        pass
            
            # Map reference information
            if 'reference_information' in data:
                ref_mapping = {
                    'paper_name': ['reference_information', 'name_of_paper'],
                    'doi': ['reference_information', 'doi'],
                    'year': ['reference_information', 'year'],
                    'source': ['reference_information', 'source']
                }
                
                for model_key, nested_path in ref_mapping.items():
                    try:
                        # Navigate through nested dictionary
                        current = data
                        for key in nested_path[:-1]:
                            current = current.get(key, {})
                        
                        # Set the value
                        data[model_key] = current.get(nested_path[-1])
                    except Exception:
                        pass
        
        return data
    
class Data(BaseModel):
    
    data:Optional[List[Extract_Text]]
    
    model_config = ConfigDict(
        validate_assignment = False,  # Disable validation on assignment
        extra = 'allow' , # Allow extra fields
        arbitrary_types_allowed = True
    )
    
    def to_json_string(self):
        """Converts the Data object to a JSON string."""
        return json.dumps(self.model_dump(mode='json'), indent=4)
    
    
    
    
# if __name__=="__main__":
#     example = {
#         "data": [{"input_data": {"device_material": "Silicon Nanowire", "electrode_shape": "Triangular", "bottom_electrodes": ["SiNi", "SiO2"], "top_electrodes": ["Pt"], "thickness_of_top_electrode": 10, "thickness_of_bottom_electrode": [5, 2], "thickness_of_switching_layer": 30}, "output_data": {"type_of_switching": "Resistive", "endurance_cycles": 1000, "retention_time": 86400, "memory_window": 2.5, "number_of_states": "Binary", "conduction_mechanism_type": "Filamentary", "resistive_switching_mechanism": "Oxide Formation"}, "reference_information": {"name_of_paper": "Flexible Resistive Switching Devices with Triangular-Shaped Silicon Nanowire Bottom Electrodes", "doi": "10.2145/SSSE.S080716", "year": 2016}}]
#     }
#     try:
#         raw = json.dumps(example["data"][0],indent=2)
#         b = Extract_Text(**dict(json.loads(raw)))
#         l=Data(data=[b])
#         print("\n-----------------------------------------------\n",l,"\n---------------------------------------\n")
#         print("\n-----------------------------------------------------------------\n",raw,"\n----------------------------------------------------------------------\n")
#         print("\n-----------------------------------------------------------------\n",l.to_json_string(),"\n----------------------------------------------------------------------\n")
#     except Exception as e:
#         print(e)