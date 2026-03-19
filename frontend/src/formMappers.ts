import {
  blankBasicQualification,
  blankCareerClient,
  blankCareerExperience,
  blankCareerProject,
  blankCareerTechnologyStack,
  blankHistory,
} from "./constants";
import type { CareerFormState, ResumeFormState, BasicFormState } from "./payloadBuilders";
import type { BasicInfoResponse, CareerResumeResponse, ResumeResponse } from "./types";

export function createInitialBasicForm(): BasicFormState {
  return {
    full_name: "",
    name_furigana: "",
    record_date: "",
    qualifications: [{ ...blankBasicQualification }],
  };
}

export function mapBasicInfoToForm(response: BasicInfoResponse): BasicFormState {
  return {
    full_name: response.full_name,
    name_furigana: response.name_furigana,
    record_date: response.record_date,
    qualifications:
      response.qualifications.length > 0
        ? response.qualifications
        : [{ ...blankBasicQualification }],
  };
}

export function createInitialResumeForm(): ResumeFormState {
  return {
    gender: "",
    birthday: "",
    postal_code: "",
    prefecture: "",
    address: "",
    address_furigana: "",
    email: "",
    phone: "",
    motivation: "",
    personal_preferences: "",
    educations: [{ ...blankHistory }],
    work_histories: [{ ...blankHistory }],
    photo: null,
  };
}

export function mapResumeToForm(response: ResumeResponse): ResumeFormState {
  return {
    gender: response.gender,
    birthday: response.birthday,
    postal_code: response.postal_code,
    prefecture: response.prefecture,
    address: response.address,
    address_furigana: response.address_furigana,
    email: response.email,
    phone: response.phone,
    motivation: response.motivation,
    personal_preferences: response.personal_preferences ?? "",
    educations:
      response.educations.length > 0
        ? response.educations
        : [{ ...blankHistory }],
    work_histories:
      response.work_histories.length > 0
        ? response.work_histories
        : [{ ...blankHistory }],
    photo: response.photo ?? null,
  };
}

export function createInitialCareerForm(): CareerFormState {
  return {
    career_summary: "",
    self_pr: "",
    experiences: [{ ...blankCareerExperience }],
  };
}

export function mapCareerResumeToForm(response: CareerResumeResponse): CareerFormState {
  return {
    career_summary: response.career_summary,
    self_pr: response.self_pr,
    experiences:
      response.experiences.length > 0
        ? response.experiences.map((experience) => ({
          ...experience,
          end_date: experience.end_date ?? "",
          clients:
            experience.clients.length > 0
              ? experience.clients.map((client) => ({
                ...client,
                projects:
                  client.projects.length > 0
                    ? client.projects.map((project) => ({
                      ...project,
                      end_date: project.end_date ?? "",
                      team: {
                        total: project.team.total ?? "",
                        members: project.team.members.map((member) => ({
                          ...member,
                          count: String(member.count),
                        })),
                      },
                      technology_stacks:
                        project.technology_stacks.length > 0
                          ? project.technology_stacks
                          : [{ ...blankCareerTechnologyStack }],
                      phases: project.phases ?? [],
                    }))
                    : [{ ...blankCareerProject, technology_stacks: [{ ...blankCareerTechnologyStack }] }],
              }))
              : [{ ...blankCareerClient }],
        }))
        : [{ ...blankCareerExperience }],
  };
}
