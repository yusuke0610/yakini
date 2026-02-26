import type {
  BasicInfoPayload,
  BasicQualification,
  CareerExperience,
  CareerResumePayload,
  CareerTechnologyStack,
  ResumeHistory,
  ResumePayload
} from "./types";

export type BasicFormState = {
  full_name: string;
  record_date: string;
  qualifications: BasicQualification[];
};

export type CareerExperienceForm = {
  company: string;
  title: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  description: string;
  achievements: string;
  employee_count: string;
  capital: string;
  technology_stacks: CareerTechnologyStack[];
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
  educations: ResumeHistory[];
  work_histories: ResumeHistory[];
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
        name: qualification.name.trim()
      }))
      .filter((qualification) => hasAnyText([qualification.acquired_date, qualification.name]))
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
      title: exp.title.trim(),
      start_date: exp.start_date.trim(),
      end_date: exp.is_current ? null : exp.end_date.trim(),
      is_current: exp.is_current,
      description: exp.description.trim(),
      achievements: exp.achievements.trim(),
      employee_count: exp.employee_count.trim(),
      capital: exp.capital.trim(),
      technology_stacks: exp.technology_stacks
        .map((stack) => ({
          category: stack.category,
          name: stack.name.trim()
        }))
        .filter((stack) => Boolean(stack.name))
    }))
    .filter((exp) =>
      hasAnyText([
        exp.company,
        exp.title,
        exp.start_date,
        exp.end_date ?? "",
        exp.description,
        exp.achievements,
        exp.employee_count,
        exp.capital,
        ...exp.technology_stacks.map((stack) => stack.name)
      ])
    );

  for (const exp of experiences) {
    if (
      !exp.company ||
      !exp.title ||
      !exp.start_date ||
      !exp.description ||
      !exp.achievements ||
      !exp.employee_count ||
      !exp.capital
    ) {
      throw new Error("職務経歴は入力する場合、必須項目をすべて埋めてください。");
    }
    if (!exp.is_current && !exp.end_date) {
      throw new Error("職務経歴の離職年月を入力するか、在職を選択してください。");
    }
  }

  return {
    career_summary,
    self_pr,
    experiences
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
    educations: state.educations
      .map((education) => ({
        date: education.date.trim(),
        name: education.name.trim()
      }))
      .filter((education) => hasAnyText([education.date, education.name])),
    work_histories: state.work_histories
      .map((workHistory) => ({
        date: workHistory.date.trim(),
        name: workHistory.name.trim()
      }))
      .filter((workHistory) => hasAnyText([workHistory.date, workHistory.name]))
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
