from typing import Optional,List
from pydantic import BaseModel, Field

class General_Extract_Text(BaseModel):
    """
    Contains information about extracted data from research papers.
    """
    numeric_value: Optional[str] = Field(default=None, description="A numeric value extracted from a research paper, representing parameters like thickness, retention time, endurance cycles, or other quantitative data in the given field.")

class Genral_Data(BaseModel):
    
    data:List[General_Extract_Text]
    