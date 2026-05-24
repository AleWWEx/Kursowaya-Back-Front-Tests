import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Dashboard from "./Dashboard";
import type { BookingRow } from "@/lib/appointmentsApi";

const fetchAppointmentsMock = vi.fn();

vi.mock("@/lib/appointmentsApi", () => ({
  fetchAppointments: (...args: unknown[]) => fetchAppointmentsMock(...args),
  confirmAppointment: vi.fn(),
  cancelAppointment: vi.fn(),
}));

vi.mock("@/lib/mastersApi", () => ({
  fetchMasterNoShowStats: vi.fn(() => Promise.resolve([])),
}));

vi.mock("@/lib/aiApi", () => ({
  predictNoShowForAppointment: vi.fn(),
}));

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children?: React.ReactNode }) =>
      React.createElement("div", props, children),
  },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    user: { role: "master", name: "Мастер Сидоров", email: "master@test.local" },
    bootstrapping: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }),
  addLog: vi.fn(),
}));

vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

const sampleBooking: BookingRow = {
  id: "1",
  clientName: "Петров Иван",
  masterName: "Сидоров",
  service: "Стрижка",
  date: "2026-06-20",
  time: "10:00",
  status: "confirmed",
  price: 1200,
};

function renderDashboard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Dashboard (UI)", () => {
  beforeEach(() => {
    fetchAppointmentsMock.mockReset();
  });

  it("U-07: master cabinet displays appointments in the list", async () => {
    fetchAppointmentsMock.mockResolvedValue([sampleBooking]);
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Петров Иван")).toBeInTheDocument();
    });
    expect(screen.getByText("Стрижка")).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: /прогноз ии/i })).toBeInTheDocument();
  });

  it("U-10: master sees AI risk label and probability for a booking", async () => {
    fetchAppointmentsMock.mockResolvedValue([
      { ...sampleBooking, aiRiskColor: "yellow", aiProbability: 25 },
    ]);
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Средний")).toBeInTheDocument();
    });
    expect(screen.getByText("25%")).toBeInTheDocument();
  });
});
