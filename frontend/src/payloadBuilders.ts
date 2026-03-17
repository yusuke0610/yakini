import type {
  BasicInfoPayload,
  BasicQualification,
  CareerClient,
  CareerExperience,
  CareerProject,
  CareerResumePayload,
  CareerTechnologyStack,
  ProjectTeam,
  ResumeHistory,
  ResumePayload,
  TeamMember,
} from "./types";

export type TeamMemberForm = {
  role: string;
  count: string;
};

export type CareerProjectForm = {
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  role: string;
  description: string;
  challenge: string;
  action: string;
  result: string;
  team: {
    total: string;
    members: TeamMemberForm[];
  };
  technology_stacks: CareerTechnologyStack[];
  phases: string[];
};

export type CareerClientForm = {
  name: string;
  projects: CareerProjectForm[];
};

export type CareerExperienceForm = {
  company: string;
  business_description: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
  employee_count: string;
  capital: string;
  clients: CareerClientForm[];
};

export type BasicFormState = {
  full_name: string;
  name_furigana: string;
  record_date: string;
  qualifications: BasicQualification[];
};

export type CareerFormState = {
  career_summary: string;
  self_pr: string;
  experiences: CareerExperienceForm[];
};

export type ResumeFormState = {
  gender: "male" | "female" | "";
  birthday: string;
  postal_code: string;
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

export function hasAnyText(values: Array<string | null | undefined>): boolean {
  return values.some((value) => Boolean(value?.trim()));
}

const HIRAGANA_RE = /^[ぁ-ゖー\s\u3000]+$/;

export function buildBasicPayload(state: BasicFormState): BasicInfoPayload {
  const payload: BasicInfoPayload = {
    full_name: state.full_name.trim(),
    name_furigana: state.name_furigana.trim(),
    record_date: state.record_date.trim(),
    qualifications: state.qualifications
      .map((qualification) => ({
        acquired_date: qualification.acquired_date.trim(),
        name: qualification.name.trim(),
      }))
      .filter((qualification) => hasAnyText([qualification.acquired_date, qualification.name])),
  };

  if (!payload.full_name || !payload.name_furigana || !payload.record_date) {
    throw new Error("ふりがな、氏名、記載日は必須です。");
  }

  if (!HIRAGANA_RE.test(payload.name_furigana)) {
    throw new Error("ふりがなはひらがなで入力してください。");
  }

  for (const qualification of payload.qualifications) {
    if (!qualification.acquired_date || !qualification.name) {
      throw new Error("資格は取得日と名称を両方入力してください。");
    }
  }

  return payload;
}

function buildTeam(team: CareerProjectForm["team"]): ProjectTeam {
  const members: TeamMember[] = team.members
    .filter((m) => m.role.trim() && m.count.trim())
    .map((m) => ({ role: m.role.trim(), count: Number(m.count) }));
  return {
    total: team.total.trim(),
    members,
  };
}

function buildProject(proj: CareerProjectForm): CareerProject {
  return {
    name: proj.name.trim(),
    start_date: proj.start_date.trim(),
    end_date: proj.is_current ? "" : proj.end_date.trim(),
    is_current: proj.is_current,
    role: proj.role.trim(),
    description: proj.description.trim(),
    challenge: proj.challenge.trim(),
    action: proj.action.trim(),
    result: proj.result.trim(),
    team: buildTeam(proj.team),
    technology_stacks: proj.technology_stacks
      .map((stack) => ({
        category: stack.category,
        name: stack.name.trim(),
      }))
      .filter((stack) => Boolean(stack.name)),
    phases: proj.phases.filter((p) => Boolean(p)),
  };
}

function buildClient(client: CareerClientForm): CareerClient {
  return {
    name: client.name.trim(),
    projects: client.projects
      .map(buildProject)
      .filter((p) => hasAnyText([p.name, p.description, p.challenge, p.action, p.result])),
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
      clients: exp.clients
        .map(buildClient)
        .filter((c) => c.name.trim() || c.projects.length > 0),
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
    gender: state.gender as "male" | "female",
    birthday: state.birthday.trim(),
    postal_code: state.postal_code.trim(),
    prefecture: state.prefecture.trim(),
    address: state.address.trim(),
    address_furigana: state.address_furigana.trim(),
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
    !payload.gender ||
    !payload.prefecture ||
    !payload.address ||
    !payload.address_furigana ||
    !payload.email ||
    !payload.phone
  ) {
    throw new Error("性別、都道府県、住所、住所ふりがな、メールアドレス、電話番号は必須です。");
  }

  if (!HIRAGANA_RE.test(payload.address_furigana)) {
    throw new Error("住所ふりがなはひらがなで入力してください。");
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
