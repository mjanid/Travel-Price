"use client";

import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground">Travel Price</h1>
          <p className="mt-2 text-sm text-muted">
            Sign in to monitor travel prices
          </p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
