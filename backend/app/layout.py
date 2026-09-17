"""Validate editable layout data before generating markup and CSS."""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

class Element(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: str = Field(pattern=r'^[a-zA-Z][a-zA-Z0-9_-]{0,79}$')
    type: Literal['container', 'input', 'button', 'text', 'image']
    x: float = Field(ge=0, le=10000, allow_inf_nan=False)
    y: float = Field(ge=0, le=10000, allow_inf_nan=False)
    width: float = Field(gt=0, le=10000, allow_inf_nan=False)
    height: float = Field(gt=0, le=10000, allow_inf_nan=False)
    text: str = Field(default='', max_length=10000)
    background: str = Field(default='#ffffff', pattern=r'^#[0-9a-fA-F]{6}$')
    border: str = Field(default='#cbd5e1', pattern=r'^#[0-9a-fA-F]{6}$')
    color: str | None = Field(default=None, pattern=r'^#[0-9a-fA-F]{6}$')
    font_size: float | None = Field(default=None, ge=1, le=500, allow_inf_nan=False)
    border_width: float = Field(default=1, ge=0, le=50, allow_inf_nan=False)
    radius: float = Field(default=0, ge=0, le=5000, allow_inf_nan=False)
    geometry: Literal['rounded-rectangle', 'ellipse'] = 'rounded-rectangle'
    parent_id: str | None = None
    src: str | None = Field(default=None, max_length=200000, pattern=r'^data:image/png;base64,[A-Za-z0-9+/=]+$')

class Viewport(BaseModel):
    width: int = Field(gt=0, le=10000)
    height: int = Field(gt=0, le=10000)

class Layout(BaseModel):
    version: Literal[1] = 1
    viewport: Viewport
    background: str = Field(pattern=r'^#[0-9a-fA-F]{6}$')
    elements: list[Element] = Field(max_length=500)
    limitations: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode='after')
    def unique_ids(self):
        if len({e.id for e in self.elements}) != len(self.elements):
            raise ValueError('Element IDs must be unique.')
        return self
