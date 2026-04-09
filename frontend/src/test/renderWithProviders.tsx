/**
 * テスト用レンダリングヘルパー。
 * Redux Provider と MemoryRouter をラップして提供する。
 */
import { type ReactElement } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { Provider } from "react-redux";
import { MemoryRouter } from "react-router-dom";
import { configureStore } from "@reduxjs/toolkit";
import formCacheReducer from "../store/formCacheSlice";

interface Options extends Omit<RenderOptions, "wrapper"> {
  initialEntries?: string[];
}

export function renderWithProviders(
  ui: ReactElement,
  { initialEntries = ["/"], ...options }: Options = {},
) {
  const store = configureStore({
    reducer: { formCache: formCacheReducer },
  });

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <Provider store={store}>
        <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
      </Provider>
    );
  }

  return { store, ...render(ui, { wrapper: Wrapper, ...options }) };
}
