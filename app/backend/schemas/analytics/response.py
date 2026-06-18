from pydantic import BaseModel, Field


class OverviewRead(BaseModel):
    total_conversations: int = Field(
        description="Total number of conversations started across the scoped courses.",
        examples=[128],
    )
    active_students: int = Field(
        description="Number of distinct students who sent at least one message.",
        examples=[42],
    )
    total_messages: int = Field(
        description="Total number of student messages (assistant replies excluded).",
        examples=[531],
    )
    avg_questions_per_conversation: float = Field(
        description="Average number of student questions per conversation.",
        examples=[4.15],
    )


class ActivityPoint(BaseModel):
    date: str = Field(
        description="Calendar day for this bucket, formatted as YYYY-MM-DD.",
        examples=["2026-06-18"],
    )
    questions: int = Field(
        description="Number of student questions asked on this day.",
        examples=[17],
    )


class ActivityRead(BaseModel):
    data: list[ActivityPoint] = Field(
        description="Continuous daily series ordered by date (includes zero-valued days).",
    )


class CoursesRead(BaseModel):
    data: list[str] = Field(
        description="Course codes the caller is allowed to inspect.",
        examples=[["ed", "poo", "paw"]],
    )


class CourseOverviewRead(BaseModel):
    course: str = Field(
        description="Course code these metrics refer to.",
        examples=["ed"],
    )
    total_conversations: int = Field(
        description="Total number of conversations started in this course.",
        examples=[64],
    )
    active_students: int = Field(
        description="Number of distinct students active in this course.",
        examples=[25],
    )
    total_messages: int = Field(
        description="Total number of student messages in this course.",
        examples=[280],
    )
    avg_questions_per_conversation: float = Field(
        description="Average number of student questions per conversation in this course.",
        examples=[4.38],
    )


class TopicPoint(BaseModel):
    topic: str = Field(
        description="Topic label extracted from student questions.",
        examples=["binary search trees"],
    )
    count: int = Field(
        description="Number of times this topic was raised.",
        examples=[34],
    )


class CourseTopicsRead(BaseModel):
    course: str = Field(
        description="Course code these topics refer to.",
        examples=["ed"],
    )
    topics: list[TopicPoint] = Field(
        description="Topics ordered from most to least frequent.",
    )


class SourcePoint(BaseModel):
    filename: str = Field(
        description="Filename of the source document cited in tutor answers.",
        examples=["lecture-03-trees.pdf"],
    )
    references: int = Field(
        description="Number of times this source was cited.",
        examples=[58],
    )


class CourseSourcesRead(BaseModel):
    course: str = Field(
        description="Course code these sources refer to.",
        examples=["ed"],
    )
    sources: list[SourcePoint] = Field(
        description="Sources ordered from most to least referenced.",
    )
