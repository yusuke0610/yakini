const assert = require("node:assert/strict");
const test = require("node:test");

const {
  buildBasicPayload,
  buildCareerPayload,
  buildResumePayload
} = require("../.test-dist/payloadBuilders.js");

test("buildBasicPayload trims values and excludes empty資格", () => {
  const payload = buildBasicPayload({
    full_name: "  山田 太郎  ",
    name_furigana: "  やまだ たろう  ",
    record_date: "2026-02-21",
    qualifications: [
      {
        acquired_date: "2020-04-01",
        name: "応用情報技術者"
      },
      {
        acquired_date: "  ",
        name: "  "
      }
    ]
  });

  assert.equal(payload.full_name, "山田 太郎");
  assert.equal(payload.qualifications.length, 1);
  assert.deepEqual(payload.qualifications[0], {
    acquired_date: "2020-04-01",
    name: "応用情報技術者"
  });
});

test("buildBasicPayload throws when a 資格 is partially filled", () => {
  assert.throws(
    () =>
      buildBasicPayload({
        full_name: "山田 太郎",
        name_furigana: "やまだ たろう",
        record_date: "2026-02-21",
        qualifications: [
          {
            acquired_date: "2020-04-01",
            name: ""
          }
        ]
      }),
    /資格は取得日と名称を両方入力してください。/
  );
});

test("buildCareerPayload trims data and keeps only non-empty technology stacks", () => {
  const payload = buildCareerPayload({
    career_summary: "  職務要約テスト  ",
    self_pr: "  自己PRテスト  ",
    experiences: [
      {
        company: "  Example株式会社  ",
        business_description: "  SES事業  ",
        start_date: "2020-04",
        end_date: "",
        is_current: true,
        employee_count: "  300名  ",
        capital: "  1億円  ",
        clients: [
          {
            has_client: true,
            name: "  クライアントA  ",
            projects: [
              {
                name: "  プロジェクトA  ",
                start_date: "2020-04",
                end_date: "2021-03",
                is_current: false,
                role: "  メンバー  ",
                description: "  API開発  ",
                challenge: "  課題テスト  ",
                action: "  行動テスト  ",
                result: "  パフォーマンス改善  ",
                team: {
                  total: "  5  ",
                  members: [
                    { role: "SE", count: "3" },
                    { role: "PG", count: "2" },
                    { role: "  ", count: "  " }
                  ]
                },
                phases: ["要件定義", "開発", ""],
                technology_stacks: [
                  {
                    category: "framework",
                    name: "  FastAPI  "
                  },
                  {
                    category: "language",
                    name: "   "
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  });

  assert.equal(payload.career_summary, "職務要約テスト");
  assert.equal(payload.self_pr, "自己PRテスト");
  assert.equal(payload.experiences.length, 1);
  assert.equal(payload.experiences[0].is_current, true);
  assert.equal(payload.experiences[0].business_description, "SES事業");
  assert.equal(payload.experiences[0].clients.length, 1);
  assert.equal(payload.experiences[0].clients[0].name, "クライアントA");
  assert.equal(payload.experiences[0].clients[0].projects.length, 1);
  assert.equal(payload.experiences[0].clients[0].projects[0].name, "プロジェクトA");
  assert.equal(payload.experiences[0].clients[0].projects[0].role, "メンバー");
  assert.deepEqual(payload.experiences[0].clients[0].projects[0].technology_stacks, [
    {
      category: "framework",
      name: "FastAPI"
    }
  ]);
});

test("buildCareerPayload throws when 離職で終了年月がない", () => {
  assert.throws(
    () =>
      buildCareerPayload({
        career_summary: "職務要約",
        self_pr: "自己PR",
        experiences: [
          {
            company: "Example株式会社",
            business_description: "SES事業",
            start_date: "2022-04",
            end_date: "",
            is_current: false,
            employee_count: "100名",
            capital: "5000万円",
            clients: []
          }
        ]
      }),
    /職務経歴の離職年月を入力するか、在職を選択してください。/
  );
});

test("buildResumePayload throws when required fields are empty", () => {
  assert.throws(
    () =>
      buildResumePayload({
        gender: "male",
        birthday: "",
        postal_code: "",
        prefecture: "",
        address: "渋谷区",
        address_furigana: "",
        email: "test@example.com",
        phone: "09012345678",
        motivation: "",
        personal_preferences: "",
        educations: [],
        work_histories: [],
        photo: null
      }),
    /性別、都道府県、住所、住所ふりがな、メールアドレス、電話番号は必須です。/
  );
});
