import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { describe, it, expect } from "vitest";
import { PrivateRoute, PublicRoute, type AuthUser } from "./guards";

const testUser: AuthUser = {
  username: "test-user-001",
  isGitHubUser: true,
};

function renderWithRoutes(user: AuthUser | null, initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route
          element={<PrivateRoute user={user} authLoading={false} />}
        >
          <Route
            path="/basic_info"
            element={<div>BasicInfo</div>}
          />
        </Route>
        <Route
          element={<PublicRoute user={user} authLoading={false} />}
        >
          <Route path="/login" element={<div>Login</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("PrivateRoute", () => {
  it("未認証ユーザーは /login にリダイレクトされる", () => {
    renderWithRoutes(null, "/basic_info");
    expect(screen.getByText("Login")).toBeInTheDocument();
    expect(screen.queryByText("BasicInfo")).not.toBeInTheDocument();
  });

  it("認証済みユーザーはコンテンツが表示される", () => {
    renderWithRoutes(testUser, "/basic_info");
    expect(screen.getByText("BasicInfo")).toBeInTheDocument();
  });

  it("authLoading 中はローディング表示される", () => {
    render(
      <MemoryRouter initialEntries={["/basic_info"]}>
        <Routes>
          <Route
            element={
              <PrivateRoute user={null} authLoading={true} />
            }
          >
            <Route
              path="/basic_info"
              element={<div>BasicInfo</div>}
            />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("読み込み中...")).toBeInTheDocument();
    expect(screen.queryByText("BasicInfo")).not.toBeInTheDocument();
  });
});

describe("PublicRoute", () => {
  it("認証済みユーザーが /login にアクセスすると /basic_info にリダイレクト", () => {
    renderWithRoutes(testUser, "/login");
    expect(screen.getByText("BasicInfo")).toBeInTheDocument();
    expect(screen.queryByText("Login")).not.toBeInTheDocument();
  });

  it("未認証ユーザーはログイン画面が表示される", () => {
    renderWithRoutes(null, "/login");
    expect(screen.getByText("Login")).toBeInTheDocument();
  });
});
