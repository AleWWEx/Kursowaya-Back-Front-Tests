import { describe, it, expect } from "vitest";
import { appointmentToRow, type AppointmentApi } from "./appointmentsApi";

const baseAppointment = (): AppointmentApi => ({
  id: 42,
  client: { id: 1, full_name: "Иван Петров", email: "ivan@test.local" },
  master: { id: 2, full_name: "Мастер Сидоров" },
  service: { id: 3, service_name: "Стрижка", price: "1200.00" },
  status: { id: 4, status_code: "confirmed", status_name: "Подтверждена" },
  ai_data: null,
  start_datetime: "2026-06-15T14:30:00+03:00",
  end_datetime: "2026-06-15T15:30:00+03:00",
  comment: "",
  payment_status: "unpaid",
});

describe("appointmentsApi (UI)", () => {
  it("U-06: appointmentToRow maps core fields", () => {
    const row = appointmentToRow(baseAppointment());
    expect(row.id).toBe("42");
    expect(row.clientName).toBe("Иван Петров");
    expect(row.masterName).toBe("Мастер Сидоров");
    expect(row.service).toBe("Стрижка");
    expect(row.status).toBe("confirmed");
    expect(row.price).toBe(1200);
    expect(row.date).toMatch(/2026-06-15/);
    expect(row.time).toMatch(/\d{2}:\d{2}/);
  });

  it("U-07: appointmentToRow strips phone line from notes", () => {
    const row = appointmentToRow({
      ...baseAppointment(),
      comment: "Тел: +79991234567\n\nПожелания клиента",
    });
    expect(row.notes).toBe("Пожелания клиента");
    expect(row.notes).not.toMatch(/7999/);
  });
});
