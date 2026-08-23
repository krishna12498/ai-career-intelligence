from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Skill(BaseModel):
    name: str
    category: Optional[str] = None  # e.g. "language", "framework", "cloud", "tool"
    level: Optional[SkillLevel] = None


class Experience(BaseModel):
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    technologies: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None


class Project(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: list[str] = Field(default_factory=list)
    url: Optional[str] = None


class Certification(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None


class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None


class StructuredResume(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = None
    skills: list[Skill] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    raw_text: Optional[str] = None
    extraction_metadata: dict = Field(default_factory=dict)


class ResumeParseResponse(BaseModel):
    success: bool
    resume: Optional[StructuredResume] = None
    error: Optional[str] = None
    page_count: int = 0
