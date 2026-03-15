export type PageKey = "basic" | "career" | "Resume" | "github" | "blog";

export type BasicTextFieldKey = "full_name" | "record_date";

export type CareerTextFieldKey = "career_summary" | "self_pr";
export type CareerExperienceFieldKey =
  | "company"
  | "business_description"
  | "start_date"
  | "end_date"
  | "is_current"
  | "employee_count"
  | "capital";
export type CareerProjectFieldKey = "name" | "role" | "description" | "achievements" | "scale";

export type ResumeTextFieldKey =
  | "postal_code"
  | "prefecture"
  | "address"
  | "email"
  | "phone"
  | "motivation"
  | "personal_preferences";
