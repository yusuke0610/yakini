import type {
  BasicInfoPayload,
  BasicQualification,
  CareerExperience,
  CareerProject,
  CareerResumePayload,
  CareerTechnologyStack,
  ResumeHistory,
  ResumePayload,
} from "./types";

export type CareerProjectForm = {
  name: string;
  role: string;
  description: string;
  achievements: string;
  scale: string;
  technology_stacks: CareerTechnologyStack[];
};

export type CareerExperienceForm = {
  company: string;
  business_description: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  employee_count: string;
  capital: string;
  projects: CareerProjectForm[];
};

export type BasicFormState = {
  full_name: string;
  record_date: string;
  qualifications: BasicQualification[];
};

export type CareerFormState = {
  career_summary: string;
  self_pr: string;
  experiences: CareerExperienceForm[];
};

export type ResumeFormState = {
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

export function hasAnyText(values: Array<string | null | undefined>): boolean {
  return values.some((value) => Boolean(value?.trim()));
}

export function buildBasicPayload(state: BasicFormState): BasicInfoPayload {
  const payload: BasicInfoPayload = {
    full_name: state.full_name.trim(),
    record_date: state.record_date.trim(),
    qualifications: state.qualifications
      .map((qualification) => ({
        acquired_date: qualification.acquired_date.trim(),
        name: qualification.name.trim(),
      }))
      .filter((qualification) => hasAnyText([qualification.acquired_date, qualification.name])),
  };

  if (!payload.full_name || !payload.record_date) {
    throw new Error("氏名と記載日は必須です。");
  }

  for (const qualification of payload.qualifications) {
    if (!qualification.acquired_date || !qualification.name) {
      throw new Error("資格は取得日と名称を両方入力してください。");
    }
  }

  return payload;
}

function buildProject(proj: CareerProjectForm): CareerProject {
  return {
    name: proj.name.trim(),
    role: proj.role.trim(),
    description: proj.description.trim(),
    achievements: proj.achievements.trim(),
    scale: proj.scale.trim(),
    technology_stacks: proj.technology_stacks
      .map((stack) => ({
        category: stack.category,
        name: stack.name.trim(),
      }))
      .filter((stack) => Boolean(stack.name)),
  };
}

export function buildCareerPayload(state: CareerFormState): CareerResumePayload {
  const career_summary = state.career_summary.trim();
  if (!career_summary) {
    throw new Error("職務要約を入力してください。");
  }

  const self_pr = state.self_pr.trim();
  if (!self_pr) {
    throw new Error("自己PRを入力してください。");
  }

  const experiences: CareerExperience[] = state.experiences
    .map((exp) => ({
      company: exp.company.trim(),
      business_description: exp.business_description.trim(),
      start_date: exp.start_date.trim(),
      end_date: exp.is_current ? null : exp.end_date.trim(),
      is_current: exp.is_current,
      employee_count: exp.employee_count.trim(),
      capital: exp.capital.trim(),
      projects: exp.projects
        .map(buildProject)
        .filter((p) => hasAnyText([p.name, p.description, p.achievements])),
    }))
    .filter((exp) =>
      hasAnyText([exp.company, exp.business_description, exp.start_date, exp.end_date ?? ""]),
    );

  for (const exp of experiences) {
    if (!exp.company || !exp.business_description || !exp.start_date) {
      throw new Error("職務経歴は会社名、事業内容、開始年月を入力してください。");
    }
    if (!exp.is_current && !exp.end_date) {
      throw new Error("職務経歴の離職年月を入力するか、在職を選択してください。");
    }
  }

  return {
    career_summary,
    self_pr,
    experiences,
  };
}

export function buildResumePayload(state: ResumeFormState): ResumePayload {
  const payload: ResumePayload = {
    postal_code: state.postal_code.trim(),
    prefecture: state.prefecture.trim(),
    address: state.address.trim(),
    email: state.email.trim(),
    phone: state.phone.trim(),
    motivation: state.motivation.trim(),
    personal_preferences: state.personal_preferences.trim(),
    photo: state.photo || null,
    educations: state.educations
      .map((education) => ({
        date: education.date.trim(),
        name: education.name.trim(),
      }))
      .filter((education) => hasAnyText([education.date, education.name])),
    work_histories: state.work_histories
      .map((workHistory) => ({
        date: workHistory.date.trim(),
        name: workHistory.name.trim(),
      }))
      .filter((workHistory) => hasAnyText([workHistory.date, workHistory.name])),
  };

  if (
    !payload.postal_code ||
    !payload.prefecture ||
    !payload.address ||
    !payload.email ||
    !payload.phone ||
    !payload.motivation
  ) {
    throw new Error("郵便番号、都道府県、住所、メールアドレス、電話番号、志望動機は必須です。");
  }

  for (const education of payload.educations) {
    if (!education.date || !education.name) {
      throw new Error("学歴は日付と名称を両方入力してください。");
    }
  }

  for (const workHistory of payload.work_histories) {
    if (!workHistory.date || !workHistory.name) {
      throw new Error("職歴は日付と名称を両方入力してください。");
    }
  }

  return payload;
}
