export type Experience = {
  company: string;
  title: string;
  start_date: string;
  end_date: string;
  description: string;
};

export type Education = {
  school: string;
  degree: string;
  start_date: string;
  end_date: string;
};

export type ResumePayload = {
  full_name: string;
  email: string;
  phone: string;
  summary: string;
  experiences: Experience[];
  educations: Education[];
  skills: string[];
};

export type ResumeResponse = ResumePayload & {
  id: string;
  created_at: string;
  updated_at: string;
};
