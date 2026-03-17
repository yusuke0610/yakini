import type { CareerTechnologyStackCategory, ResumeHistory, BasicQualification } from "./types";
import type { CareerClientForm, CareerExperienceForm, CareerProjectForm } from "./payloadBuilders";
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
  framework: "FW",
  os: "OS",
  db: "DB",
  cloud_resource: "NW",
  dev_tool: "Tool",
};

export const blankCareerTechnologyStack: CareerTechnologyStack = {
  category: "language",
  name: "",
};

export const blankCareerProject: CareerProjectForm = {
  name: "",
  start_date: "",
  end_date: "",
  is_current: false,
  role: "",
  description: "",
  challenge: "",
  action: "",
  result: "",
  scale: "",
  technology_stacks: [{ ...blankCareerTechnologyStack }],
};

export const blankCareerClient: CareerClientForm = {
  name: "",
  projects: [{ ...blankCareerProject, technology_stacks: [{ ...blankCareerTechnologyStack }] }],
};

export const blankCareerExperience: CareerExperienceForm = {
  company: "",
  business_description: "",
  start_date: "",
  end_date: "",
  is_current: false,
  employee_count: "",
  capital: "",
  clients: [{ ...blankCareerClient }],
};

export const blankHistory: ResumeHistory = {
  date: "",
  name: "",
};
