import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RegisterForm } from "../register-form";

// ----------------------------------------------------------------
// Mock next/navigation
// ----------------------------------------------------------------
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

// ----------------------------------------------------------------
// Mock next/link (render as a plain anchor)
// ----------------------------------------------------------------
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// ----------------------------------------------------------------
// Mock useRegister hook
// ----------------------------------------------------------------
const mutateMock = vi.fn();
let isPendingValue = false;

vi.mock("@/hooks/use-auth", () => ({
  useRegister: () => ({
    mutate: mutateMock,
    isPending: isPendingValue,
  }),
}));

describe("RegisterForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    isPendingValue = false;
  });

  it("renders all required fields (name, email, password) and submit button", () => {
    render(<RegisterForm />);

    expect(screen.getByLabelText("Full name")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
  });

  it("validates required fields on empty submit", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/full name is required/i)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
    });

    expect(mutateMock).not.toHaveBeenCalled();
  });

  it("validates password minimum length", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText("Full name"), "Test User");
    await user.type(screen.getByLabelText("Email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "short");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
    });

    expect(mutateMock).not.toHaveBeenCalled();
  });

  it("validates email format", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText("Full name"), "Test User");
    // Use "foo@bar" which passes HTML5 validation in jsdom but fails
    // Zod's stricter email check (no TLD).
    await user.type(screen.getByLabelText("Email"), "foo@bar");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument();
    });

    expect(mutateMock).not.toHaveBeenCalled();
  });

  it("calls register API with correct payload on valid submit", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText("Full name"), "Test User");
    await user.type(screen.getByLabelText("Email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "securepassword");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(mutateMock).toHaveBeenCalledTimes(1);
    });

    const [payload] = mutateMock.mock.calls[0] as [
      { email: string; password: string; full_name: string },
      { onSuccess: () => void; onError: (err: Error) => void },
    ];
    expect(payload).toEqual({
      email: "test@example.com",
      password: "securepassword",
      full_name: "Test User",
    });
  });

  it("shows error for duplicate email (409 response)", async () => {
    mutateMock.mockImplementation(
      (
        _data: { email: string; password: string; full_name: string },
        options: { onError: (err: Error) => void },
      ) => {
        options.onError(new Error("Email already registered"));
      },
    );

    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText("Full name"), "Test User");
    await user.type(screen.getByLabelText("Email"), "existing@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText("Email already registered")).toBeInTheDocument();
    });
  });

  it("disables submit button while request is in-flight", () => {
    isPendingValue = true;
    render(<RegisterForm />);

    const submitButton = screen.getByRole("button", { name: /create account/i });
    expect(submitButton).toBeDisabled();
  });

  it("redirects to /dashboard on successful registration", async () => {
    mutateMock.mockImplementation(
      (
        _data: { email: string; password: string; full_name: string },
        options: { onSuccess: () => void },
      ) => {
        options.onSuccess();
      },
    );

    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText("Full name"), "Test User");
    await user.type(screen.getByLabelText("Email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("renders a link to the login page", () => {
    render(<RegisterForm />);

    const loginLink = screen.getByRole("link", { name: /sign in/i });
    expect(loginLink).toHaveAttribute("href", "/login");
  });
});
