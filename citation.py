from typing import List, Optional
from pydantic import BaseModel, Field, UUID4,ConfigDict
import json


class Citation(BaseModel):
    Source_ID: Optional[int] = Field(
        default=None,
        description="The integer ID of a SPECIFIC source.",
    )
    Article_ID: Optional[str] = Field(
        default=None,
        description="A unique identifier for the citation (UUID format). Example: 0ddf8f69-946e-427b-89a9-faa04da8be3d",
    )
    Article_Snippet: Optional[str] = Field(default=None,
        description = "A direct quote or excerpt from the source document, providing the relevant context for the citation."
    )
    Article_Title: Optional[str] = Field(
        default=None, description="The title or name of the research paper from which the data is extracted."
    )
    Article_Source: Optional[str] = Field(
        default=None,
        description="The filename of the PDF document from which the data was extracted. Examples might include 'Memory_characteristic.pdf' "
            "or simply '1.pdf'.",
    )
    model_config = ConfigDict(
        validate_assignment = False,  # Disable validation on assignment
        extra = 'allow' , # Allow extra fields
        arbitrary_types_allowed = True
    )


class Citations(BaseModel):
    citations: List[Citation] = Field(
        default_factory=list, description="A list of citations, each referencing a specific source and quote."
    )

    model_config = ConfigDict(
        validate_assignment = False,  # Disable validation on assignment
        extra = 'allow' , # Allow extra fields
        arbitrary_types_allowed = True
    )
    
    def to_json_string(self) -> str:
        """Converts the Citations object to a JSON string."""
        return json.dumps(self.model_dump(mode='json'), indent=4, ensure_ascii=False)
