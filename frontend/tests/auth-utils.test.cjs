const assert = require("node:assert/strict");
const test = require("node:test");

const { parseUsernameFromToken } = require("../.test-dist/auth-utils.js");

/** Helper: build a fake JWT with the given payload object. */
function fakeJwt(payload) {
  const header = Buffer.from(JSON.stringify({ alg: "HS256" })).toString("base64url");
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${header}.${body}.signature`;
}

test("parseUsernameFromToken: 正常なJWTからusernameを取得できる", () => {
  const token = fakeJwt({ sub: "yamada_taro" });
  assert.equal(parseUsernameFromToken(token), "yamada_taro");
});

test("parseUsernameFromToken: nullを渡すとnullを返す", () => {
  assert.equal(parseUsernameFromToken(null), null);
});

test("parseUsernameFromToken: 不正な文字列を渡すとnullを返す", () => {
  assert.equal(parseUsernameFromToken("not-a-jwt"), null);
});

test("parseUsernameFromToken: subフィールドがないJWTではnullを返す", () => {
  const token = fakeJwt({ name: "yamada" });
  assert.equal(parseUsernameFromToken(token), null);
});
