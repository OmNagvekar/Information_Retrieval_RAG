from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator
import json

class Extract_Text(BaseModel):
    """
    Contains information about extracted data from research papers.
    """
    numeric_value: Optional[str] = Field(default=None, description=(
            "A numeric value extracted from the research paper. This may represent a measured "
            "parameter such as thickness, retention time, or endurance cycles. Stored as a string "
            "to accommodate diverse numeric formats or additional formatting (e.g., including units)."
        )
    )
    switching_layer_material: Optional[str] = Field(default=None, description=(
            "The material used in the switching layer of the device. For example, it could be a metal "
            "oxide such as TiO2 or HfO2, or another compound known for resistive switching behavior."
        )
    )
    synthesis_method: Optional[str] = Field(default=None, description=(
            "The method or process used to synthesize or fabricate the material. Common examples include "
            "chemical vapor deposition (CVD), sol–gel processes, sputtering, or thermal evaporation."
        )
    )
    top_electrode: Optional[str] = Field(default=None, description=(
            "The material of the top electrode in the device. This typically includes metals like platinum, "
            "gold, or other conductive materials used to form the top contact."
        )
    )
    top_electrode_thickness: Optional[Union[str, float]] = Field(default=None, description=(
            "The thickness of the top electrode. Typically measured in nanometers (nm), this field supports both "
            "numerical values and string representations (if units or additional comments are included)."
        )
    )
    bottom_electrode: Optional[str] = Field(default=None, description=(
            "The material of the bottom electrode, which is another key component in the device structure. "
            "Common materials might include metals or metal oxides depending on the device design."
        )
    )
    bottom_electrode_thickness: Optional[Union[str, float]] = Field(default=None, description=(
            "The thickness of the bottom electrode, measured in nanometers (nm). As with the top electrode, "
            "this field can be either a numeric value or a string if additional context is needed."
        )
    )
    switching_layer_thickness: Optional[Union[str, float]] = Field(default=None, description=(
            "The thickness of the switching layer, which is critical for device performance. "
            "Typically expressed in nanometers (nm), this parameter influences the device's electrical characteristics."
        )
    )
    switching_type: Optional[str] = Field(default=None, description=(
            "The mode or type of switching observed in the device. Examples include bipolar or unipolar switching, "
            "or other specific classifications used to describe the resistive behavior."
        )
    )
    endurance_cycles: Optional[int] = Field(default=None, description=(
            "The number of switching cycles the device can endure before failure. This integer value indicates "
            "the durability and reliability of the device under repeated use."
        )
    )
    retention_time: Optional[Union[str, int]] = Field(default=None, description=(
            "The duration for which the device can retain its resistive state, usually measured in seconds. "
            "This field can be provided as an integer or a string, especially if additional units or qualifiers are included."
        )
    )
    memory_window: Optional[Union[str, float]] = Field(default=None, description=(
            "The voltage difference between the high-resistance state and low-resistance state of the device, "
            "commonly known as the memory window. It is typically measured in volts (V) and may be expressed "
            "as a numerical value or a string with units."
        )
    )
    num_states: Optional[str] = Field(default=None, description=(
            "The number of distinct resistive states that the device can exhibit. This may be represented as a "
            "string to allow for descriptive categorizations such as 'binary', 'multilevel', etc."
        )
    )
    conduction_mechanism: Optional[str] = Field(default=None, description=(
            "A description of the conduction mechanism observed in the device. Examples include filamentary conduction, "
            "interface conduction, or other theories that explain how electrical current passes through the device."
        )
    )
    resistive_switching_mechanism: Optional[str] = Field(default=None, description=(
            "A detailed explanation of the resistive switching mechanism. This field may describe processes such as "
            "oxygen vacancy migration, redox reactions, or the formation and rupture of conductive filaments."
        )
    )
    paper_name: Optional[str] = Field(default=None, description="The title or name of the research paper from which the data is extracted.")
    doi: Optional[str] = Field(default=None, description="The Digital Object Identifier (DOI) of the research paper, providing a persistent link to its online location.")
    year: Optional[int] = Field(default=None, description="The publication year of the research paper.")
    source: Optional[str] =Field(default=None,drescription=(
            "The filename of the PDF document from which the data was extracted. Examples might include 'Memory_characteristic.pdf' "
            "or simply '1.pdf'."
        )
    )
    additionalProperties: Optional[str]= Field(default=None,description=(
            "Additional information or notes that do not fit into the predefined fields but are relevant to the user's query. "
            "This field is used for capturing any extra details from the research paper."
        )
    )
    
    
    model_config = ConfigDict(
        validate_assignment = False,  # Disable validation on assignment
        extra = 'allow' , # Allow extra fields
        arbitrary_types_allowed = True
    )
    
    
class Data_Objects(BaseModel):
    
    data:List[Extract_Text] = Field(default_factory=list,description="A list of extracted data objects.")
    
    model_config = ConfigDict(
        validate_assignment = False,  # Disable validation on assignment
        extra = 'allow' , # Allow extra fields
        arbitrary_types_allowed = True
    )
    
    def to_json_string(self):
        """Converts the Data object to a JSON string."""
        return json.dumps(self.model_dump(mode='json'), indent=4)
    
    
    
    
if __name__=="__main__":
    # example = {
    #     "data": [{"input_data": {"device_material": "Silicon Nanowire", "electrode_shape": "Triangular", "bottom_electrodes": ["SiNi", "SiO2"], "top_electrodes": ["Pt"], "thickness_of_top_electrode": 10, "thickness_of_bottom_electrode": [5, 2], "thickness_of_switching_layer": 30}, "output_data": {"type_of_switching": "Resistive", "endurance_cycles": 1000, "retention_time": 86400, "memory_window": 2.5, "number_of_states": "Binary", "conduction_mechanism_type": "Filamentary", "resistive_switching_mechanism": "Oxide Formation"}, "reference_information": {"name_of_paper": "Flexible Resistive Switching Devices with Triangular-Shaped Silicon Nanowire Bottom Electrodes", "doi": "10.2145/SSSE.S080716", "year": 2016}}]
    # }
    # try:
    #     raw = json.dumps(example["data"][0],indent=2)
    #     b = Extract_Text(**dict(json.loads(raw)))
    #     l=Data(data=[b])
    #     print("\n-----------------------------------------------\n",l,"\n---------------------------------------\n")
    #     print("\n-----------------------------------------------------------------\n",raw,"\n----------------------------------------------------------------------\n")
    #     print("\n-----------------------------------------------------------------\n",l.to_json_string(),"\n----------------------------------------------------------------------\n")
    # except Exception as e:
    #     print(e)
    print(Data.model_json_schema())
