from pydantic import BaseModel


class OverviewRead(BaseModel):
    total_conversations: int
    active_students: int
    total_messages: int
    avg_questions_per_conversation: float


class ActivityPoint(BaseModel):
    date: str
    questions: int


class ActivityRead(BaseModel):
    data: list[ActivityPoint]


class CoursesRead(BaseModel):
    data: list[str]


class CourseOverviewRead(BaseModel):
    course: str
    total_conversations: int
    active_students: int
    total_messages: int
    avg_questions_per_conversation: float


class TopicPoint(BaseModel):
    topic: str
    count: int


class CourseTopicsRead(BaseModel):
    course: str
    topics: list[TopicPoint]


class SourcePoint(BaseModel):
    filename: str
    references: int


class CourseSourcesRead(BaseModel):
    course: str
    sources: list[SourcePoint]
