export type BasicQualification = {
  acquired_date: string;
  name: string;
};

export type BasicInfoPayload = {
  full_name: string;
  record_date: string;
  qualifications: BasicQualification[];
};

export type BasicInfoResponse = BasicInfoPayload & {
  id: string;
  created_at: string;
  updated_at: string;
};

export type CareerTechnologyStackCategory =
  | "言語"
  | "フレームワーク"
  | "OS"
  | "DB"
  | "クラウドリソース"
  | "開発支援ツール";

export type CareerTechnologyStack = {
  category: CareerTechnologyStackCategory;
  name: string;
};

export type CareerProject = {
  name: string;
  role: string;
  description: string;
  achievements: string;
  scale: string;
  technology_stacks: CareerTechnologyStack[];
};

export type CareerExperience = {
  company: string;
  business_description: string;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  employee_count: string;
  capital: string;
  projects: CareerProject[];
};

export type CareerResumePayload = {
  career_summary: string;
  self_pr: string;
  experiences: CareerExperience[];
};

export type CareerResumeResponse = CareerResumePayload & {
  id: string;
  created_at: string;
  updated_at: string;
};

export type ResumeHistory = {
  date: string;
  name: string;
};

export type ResumePayload = {
  postal_code: string;
  prefecture: string;
  address: string;
  email: string;
  phone: string;
  motivation: string;
  personal_preferences: string;
  educations: ResumeHistory[];
  work_histories: ResumeHistory[];
  photo: string | null;
};

export type ResumeResponse = ResumePayload & {
  id: string;
  created_at: string;
  updated_at: string;
};
