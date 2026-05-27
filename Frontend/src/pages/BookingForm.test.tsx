import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import BookingForm from "./BookingForm";

const apiFetchMock = vi.fn();

vi.mock("@/lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetchMock(...args),
}));

const navigateMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
    useParams: () => ({}),
  };
});

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    user: { role: "user", name: "Иван Клиент", email: "client@test.local" },
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

function renderBookingForm() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <BookingForm />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("BookingForm (UI)", () => {
  beforeEach(() => {
    apiFetchMock.mockReset();
    navigateMock.mockReset();
    apiFetchMock.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === "/api/services/") {
        return Promise.resolve([{ id: 1, service_name: "Стрижка", price: "1500.00" }]);
      }
      if (path === "/api/statuses/") {
        return Promise.resolve([{ id: 10, status_code: "pending", status_name: "Ожидает" }]);
      }
      if (path === "/api/users/?role=master") {
        return Promise.resolve([{ id: 2, full_name: "Мастер Иванов" }]);
      }
      if (path === "/api/appointments/" && options?.method === "POST") {
        return Promise.resolve({ id: 99 });
      }
      return Promise.resolve([]);
    });
  });

  it("U-05: Создание записи клиентом", async () => {
    renderBookingForm();

    await waitFor(() => {
      expect(screen.getByLabelText(/услуга/i)).toBeInTheDocument();
    });

    const future = new Date();
    future.setDate(future.getDate() + 3);
    const dateStr = future.toISOString().slice(0, 10);

    fireEvent.change(screen.getByLabelText(/услуга/i), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText(/мастер/i), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText(/дата/i), { target: { value: dateStr } });
    fireEvent.change(screen.getByLabelText(/время/i), { target: { value: "14:30" } });
    fireEvent.click(screen.getByRole("button", { name: /создать запись/i }));

    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenCalledWith(
        "/api/appointments/",
        expect.objectContaining({ method: "POST" }),
      );
    });

    const postCall = apiFetchMock.mock.calls.find(
      (call) => call[0] === "/api/appointments/" && (call[1] as { method?: string })?.method === "POST",
    );
    expect(postCall).toBeTruthy();
    const body = JSON.parse((postCall![1] as { body: string }).body);
    expect(body.master_id).toBe(2);
    expect(body.service_id).toBe(1);
    expect(body.start_datetime).toBe(`${dateStr}T14:30:00`);
  });
});
