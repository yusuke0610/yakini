import type { CareerTechnologyStackCategory, ResumeHistory, BasicQualification } from "./types";
import type { CareerExperienceForm, CareerProjectForm } from "./payloadBuilders";
import type { CareerTechnologyStack } from "./types";

export const blankBasicQualification: BasicQualification = {
  acquired_date: "",
  name: "",
};

export const careerTechnologyStackCategories: CareerTechnologyStackCategory[] = [
  "language",
  "framework",
  "os",
  "db",
  "cloud_resource",
  "dev_tool",
];

export const careerTechnologyStackCategoryLabels: Record<CareerTechnologyStackCategory, string> = {
  language: "言語",
  framework: "フレームワーク",
  os: "OS",
  db: "DB",
  cloud_resource: "クラウドリソース",
  dev_tool: "開発支援ツール",
};

export const blankCareerTechnologyStack: CareerTechnologyStack = {
  category: "language",
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
