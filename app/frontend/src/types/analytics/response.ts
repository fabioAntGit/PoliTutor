export interface OverviewRead {
  total_conversations: number;
  active_students: number;
  total_messages: number;
  avg_questions_per_conversation: number;
}

export interface ActivityPoint {
  date: string;
  questions: number;
}

export interface ActivityRead {
  data: ActivityPoint[];
}

export interface CourseOverviewRead {
  total_conversations: number;
  active_students: number;
  total_messages: number;
  avg_questions_per_conversation: number;
}

export interface TopicPoint {
  topic: string;
  count: number;
}

export interface CourseTopicsRead {
  topics: TopicPoint[];
}

export interface SourcePoint {
  filename: string;
  references: number;
}

export interface CourseSourcesRead {
  sources: SourcePoint[];
}
