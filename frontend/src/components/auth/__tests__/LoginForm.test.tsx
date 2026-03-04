import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "../login-form";

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
// Mock useLogin hook
// ----------------------------------------------------------------
const mutateMock = vi.fn();
let isPendingValue = false;

vi.mock("@/hooks/use-auth", () => ({
  useLogin: () => ({
    mutate: mutateMock,
    isPending: isPendingValue,
  }),
}));

describe("LoginForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    isPendingValue = false;
  });

  it("renders email and password inputs and submit button", () => {
    render(<LoginForm />);

    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("shows validation errors for empty fields on submit", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    await user.click(submitButton);

    // The Zod schema requires email and password (min 8 chars)
    // An empty email should trigger "Please enter a valid email address"
    // An empty password should trigger "Password must be at least 8 characters"
    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
    });

    // mutate should NOT have been called
    expect(mutateMock).not.toHaveBeenCalled();
  });

  it("shows validation error for invalid email format", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    // Use "foo@bar" which passes HTML5 validation in jsdom but fails
    // Zod's stricter email check (no TLD).
    await user.type(screen.getByLabelText("Email"), "foo@bar");
    await user.type(screen.getByLabelText("Password"), "validpassword123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument();
    });

    expect(mutateMock).not.toHaveBeenCalled();
  });

  it("calls login mutation with correct payload on valid submit", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText("Email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mutateMock).toHaveBeenCalledTimes(1);
    });

    const [payload] = mutateMock.mock.calls[0] as [
      { email: string; password: string },
      { onSuccess: () => void; onError: (err: Error) => void },
    ];
    expect(payload).toEqual({
      email: "test@example.com",
      password: "password123",
    });
  });

  it("displays server error message on login failure", async () => {
    mutateMock.mockImplementation(
      (
        _data: { email: string; password: string },
        options: { onError: (err: Error) => void },
      ) => {
        options.onError(new Error("Invalid credentials"));
      },
    );

    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText("Email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "wrongpassword");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });
  });

  it("disables submit button while request is in-flight", () => {
    isPendingValue = true;
    render(<LoginForm />);

    const submitButton = screen.getByRole("button", { name: /sign in/i });
    expect(submitButton).toBeDisabled();
  });

  it("redirects to /dashboard on successful login", async () => {
    mutateMock.mockImplementation(
      (
        _data: { email: string; password: string },
        options: { onSuccess: () => void },
      ) => {
        options.onSuccess();
      },
    );

    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText("Email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("renders a link to the register page", () => {
    render(<LoginForm />);

    const registerLink = screen.getByRole("link", { name: /register/i });
    expect(registerLink).toHaveAttribute("href", "/register");
  });
});
