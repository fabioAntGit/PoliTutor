export const COURSE_CODE_MAX_LENGTH = 64;
export const COURSE_NAME_MAX_LENGTH = 255;
export const COURSE_SCOPE_MAX_LENGTH = 2000;
export const USER_TEXT_MAX_LENGTH = 255;
export const PASSWORD_MIN_LENGTH = 8;
export const QUESTION_MIN_CHARS = 2;
export const QUESTION_MAX_CHARS = 1500;

export function isQuestionReady(value: string) {
  const length = value.trim().length;
  return length >= QUESTION_MIN_CHARS && length <= QUESTION_MAX_CHARS;
}
