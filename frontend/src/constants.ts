import type { CareerTechnologyStackCategory, ResumeHistory, BasicQualification } from "./types";
import type { CareerExperienceForm, CareerProjectForm } from "./payloadBuilders";
import type { CareerTechnologyStack } from "./types";

export const blankBasicQualification: BasicQualification = {
  acquired_date: "",
  name: "",
};

export const careerTechnologyStackCategories: CareerTechnologyStackCategory[] = [
  "言語",
  "フレームワーク",
  "OS",
  "DB",
  "クラウドリソース",
  "開発支援ツール",
];

export const blankCareerTechnologyStack: CareerTechnologyStack = {
  category: "言語",
  name: "",
};

export const blankCareerProject: CareerProjectForm = {
  name: "",
  role: "",
  description: "",
  achievements: "",
  scale: "",
  technology_stacks: [{ ...blankCareerTechnologyStack }],
};

export const blankCareerExperience: CareerExperienceForm = {
  company: "",
  business_description: "",
  start_date: "",
  end_date: "",
  is_current: false,
  employee_count: "",
  capital: "",
  projects: [{ ...blankCareerProject, technology_stacks: [{ ...blankCareerTechnologyStack }] }],
};

export const blankHistory: ResumeHistory = {
  date: "",
  name: "",
};
