from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import json

class Extract_Data(BaseModel):
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
    endurance_cycles: Optional[Union[int,str]] = Field(default=None, description=(
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
    additionalProperties: Optional[str]= Field(default=None,description=(
            "Additional information or notes that do not fit into the predefined fields but are relevant to the user's query. "
            "This field is used for capturing any extra details from the research paper."
        )
    )
    paper_name: Optional[str] = Field(default=None, description="The title or name of the research paper from which the data is extracted.")
    source: Optional[str] =Field(default=None,description=(
            "The filename of the PDF document from which the data was extracted. Examples might include 'Memory_characteristic.pdf' "
            "or simply '1.pdf'."
        )
    )
    
    model_config = ConfigDict(
        validate_assignment = False,  # Disable validation on assignment
        extra = 'allow' , # Allow extra fields
        arbitrary_types_allowed = True
    )

class Data_Objects(BaseModel):
    
    data:List[Extract_Data] = Field(default_factory=list,description="A list of extracted data objects.")
    model_config = ConfigDict(
        validate_assignment = False,  # Disable validation on assignment
        extra = 'allow' , # Allow extra fields
        arbitrary_types_allowed = True
    )
    
    def to_json_string(self):
        """Converts the Data object to a JSON string."""
        return json.dumps(self.model_dump(mode='json'), indent=4)
    
    
    
    
if __name__=="__main__":
    temp ={'switching_layer_material': 'CuxO', 'synthesis_method': 'solution-processed', 'top_electrode': 'Au', 'top_electrode_thickness': None, 'bottom_electrode': 'ITO', 'bottom_electrode_thickness': None, 'switching_layer_thickness': None, 'switching_type': None, 'endurance_cycles': 200, 'retention_time': 104, 'memory_window': None, 'num_states': None, 'conduction_mechanism': 'mixed ionic electronic conduction (MIEC)', 'resistive_switching_mechanism': 'formation of Cu filaments', 'paper_name': 'Resistive Switching Characteristics in Solution-Processed Copper Oxide (CuxO) by Stoichiometry Tuning', 'source': '10.pdf'}
    print(Data_Objects(data=[Extract_Data(**temp)]).to_json_string())
    print("\n\n-----------------------------")
    # print(Data_Objects.model_json_schema())
    print(Data_Objects.model_json_schema())