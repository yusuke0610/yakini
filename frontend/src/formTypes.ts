export type PageKey = "basic" | "career" | "Resume" | "github" | "blog";

export type BasicTextFieldKey = "full_name" | "name_furigana" | "record_date";

export type CareerTextFieldKey = "career_summary" | "self_pr";
export type CareerExperienceFieldKey =
  | "company"
  | "business_description"
  | "start_date"
  | "end_date"
  | "is_current"
  | "employee_count"
  | "capital";
export type CareerClientFieldKey = "name";
export type CareerProjectFieldKey = "name" | "start_date" | "end_date" | "is_current" | "role" | "description" | "challenge" | "action" | "result";

export type ResumeTextFieldKey =
  | "gender"
  | "prefecture"
  | "address"
  | "address_furigana"
  | "email"
  | "phone"
  | "motivation"
  | "personal_preferences";
