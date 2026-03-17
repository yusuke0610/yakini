export type BasicQualification = {
  acquired_date: string;
  name: string;
};

export type BasicInfoPayload = {
  full_name: string;
  name_furigana: string;
  record_date: string;
  qualifications: BasicQualification[];
};

export type BasicInfoResponse = BasicInfoPayload & {
  id: string;
  created_at: string;
  updated_at: string;
};

export type CareerTechnologyStackCategory =
  | "language"
  | "framework"
  | "os"
  | "db"
  | "cloud_resource"
  | "dev_tool";

export type CareerTechnologyStack = {
  category: CareerTechnologyStackCategory;
  name: string;
};

export type CareerProject = {
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  role: string;
  description: string;
  challenge: string;
  action: string;
  result: string;
  scale: string;
  technology_stacks: CareerTechnologyStack[];
};

export type CareerClient = {
  name: string;
  projects: CareerProject[];
};

export type CareerExperience = {
  company: string;
  business_description: string;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  employee_count: string;
  capital: string;
  clients: CareerClient[];
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
  gender: "male" | "female";
  prefecture: string;
  address: string;
  address_furigana: string;
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

export type MasterItem = {
  id: string;
  name: string;
  sort_order: number;
};

export type TechStackMasterItem = {
  id: string;
  category: string;
  name: string;
  sort_order: number;
};

export type BlogAccount = {
  id: string;
  platform: "zenn" | "note";
  username: string;
  created_at: string;
};

export type BlogArticle = {
  id: string;
  platform: string;
  title: string;
  url: string;
  published_at: string | null;
  likes_count: number;
  summary: string | null;
  tags: string[];
};
