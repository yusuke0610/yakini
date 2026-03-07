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
        title: "  バックエンドエンジニア  ",
        start_date: "2020-04",
        end_date: "",
        is_current: true,
        description: "  API開発  ",
        achievements: "  パフォーマンス改善  ",
        employee_count: "  300名  ",
        capital: "  1億円  ",
        technology_stacks: [
          {
            category: "フレームワーク",
            name: "  FastAPI  "
          },
          {
            category: "言語",
            name: "   "
          }
        ]
      }
    ]
  });

  assert.equal(payload.career_summary, "職務要約テスト");
  assert.equal(payload.self_pr, "自己PRテスト");
  assert.equal(payload.experiences.length, 1);
  assert.equal(payload.experiences[0].is_current, true);
  assert.deepEqual(payload.experiences[0].technology_stacks, [
    {
      category: "フレームワーク",
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
            title: "エンジニア",
            start_date: "2022-04",
            end_date: "",
            is_current: false,
            description: "開発",
            achievements: "改善",
            employee_count: "100名",
            capital: "5000万円",
            technology_stacks: []
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
        postal_code: "",
        prefecture: "東京都",
        address: "渋谷区",
        email: "test@example.com",
        phone: "09012345678",
        motivation: "志望動機",
        educations: [],
        work_histories: []
      }),
    /郵便番号、都道府県、住所、メールアドレス、電話番号、志望動機は必須です。/
  );
});
