from typing import List,Optional
from pydantic import BaseModel, Field

class Extract_Text(BaseModel):
    """
    Contains information about extracted data from research papers.
    """
    numeric_value: Optional[str] = Field(default=None, description="A numeric value extracted from a research paper, representing parameters like thickness, retention time, endurance cycles, or other quantitative data in the given field.")
    switching_layer_material: Optional[str] = Field(default=None, description="Material of the switching layer (TYM_Class).")
    synthesis_method: Optional[str] = Field(default=None, description="Synthesis method used (SM_Class).")
    top_electrode: Optional[str] = Field(default=None, description="Material of the top electrode (TE_Class).")
    top_electrode_thickness: Optional[float] = Field(default=None, description="Thickness of the top electrode in nanometers (TTE in nm).")
    bottom_electrode: Optional[str] = Field(default=None, description="Material of the bottom electrode (BE_Class).")
    bottom_electrode_thickness: Optional[float] = Field(default=None, description="Thickness of the bottom electrode in nanometers (TBE in nm).")
    switching_layer_thickness: Optional[float] = Field(default=None, description="Thickness of the switching layer in nanometers (TSL in nm).")
    switching_type: Optional[str] = Field(default=None, description="Type of switching (TSUB_Class).")
    endurance_cycles: Optional[int] = Field(default=None, description="Endurance cycles (EC).")
    retention_time: Optional[float] = Field(default=None, description="Retention time in seconds (RT in seconds).")
    memory_window: Optional[float] = Field(default=None, description="Memory window in volts (MW in V).")
    num_states: Optional[str] = Field(default=None, description="Number of states (MRS_Class).")
    conduction_mechanism: Optional[str] = Field(default=None, description="Type of conduction mechanism (CM_Class).")
    resistive_switching_mechanism: Optional[str] = Field(default=None, description="Resistive switching mechanism (RSM_Class).")
    paper_name: Optional[str] = Field(default=None, description="Name of the research paper.")
    doi: Optional[str] = Field(default=None, description="DOI of the research paper.")
    year: Optional[int] = Field(default=None, description="Publication year of the research paper.")
    
class Data(BaseModel):
    
    data:List[Extract_Text]
    