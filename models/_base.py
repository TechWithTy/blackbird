"""
Base models for Blackbird API.

This module contains the base Pydantic models that other models will inherit from.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field
from pydantic.generics import GenericModel

# Generic Type Variables for response models
T = TypeVar('T')
E = TypeVar('E')


class BaseModel(PydanticBaseModel):
    """Base model with common configuration for all models."""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        allow_population_by_field_name = True
        use_enum_values = True
        extra = 'forbid'  # Forbid extra fields by default
        validate_assignment = True


class BaseResponse(GenericModel, Generic[T]):
    """Base response model for successful API responses."""
    success: bool = True
    data: T
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config(BaseModel.Config):
        json_encoders = {
            **BaseModel.Config.json_encoders,
        }


class BaseErrorResponse(GenericModel, Generic[E]):
    """Base error response model for API error responses."""
    success: bool = False
    error: E
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config(BaseModel.Config):
        json_encoders = {
            **BaseModel.Config.json_encoders,
        }
