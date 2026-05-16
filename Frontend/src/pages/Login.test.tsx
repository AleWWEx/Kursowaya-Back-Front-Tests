import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Login from "./Login";

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children?: React.ReactNode }) =>
      React.createElement("div", props, children),
  },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    user: null,
    bootstrapping: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

function renderLogin() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>,
  );
}

describe("Login page (UI)", () => {
  it("U-08: shows Email, Password and sign-in button", () => {
    renderLogin();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/пароль/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^войти$/i })).toBeInTheDocument();
  });

  it("U-09: register mode shows last name, first name, patronymic", () => {
    renderLogin();
    fireEvent.click(screen.getByRole("button", { name: /зарегистрироваться/i }));
    expect(screen.getByLabelText(/фамилия/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^имя$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/отчество/i)).toBeInTheDocument();
  });

  it("U-10: brand STEEL and BLADE is visible", () => {
    renderLogin();
    expect(screen.getByText(/STEEL/i)).toBeInTheDocument();
    expect(screen.getByText(/BLADE/i)).toBeInTheDocument();
  });
});
