"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useLogin } from "@/hooks/use-auth";
import { loginSchema } from "@/lib/validators";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function LoginForm() {
  const router = useRouter();
  const login = useLogin();
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});

    const result = loginSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of result.error.issues) {
        const key = String(issue.path[0]);
        if (!fieldErrors[key]) fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    login.mutate(result.data, {
      onSuccess: () => router.push("/dashboard"),
      onError: (err) => setErrors({ form: err.message }),
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {errors.form && (
        <p className="rounded-lg bg-red-50 p-3 text-sm text-danger">
          {errors.form}
        </p>
      )}
      <Input
        label="Email"
        type="email"
        value={form.email}
        onChange={(e) => setForm({ ...form, email: e.target.value })}
        error={errors.email}
        autoComplete="email"
      />
      <Input
        label="Password"
        type="password"
        value={form.password}
        onChange={(e) => setForm({ ...form, password: e.target.value })}
        error={errors.password}
        autoComplete="current-password"
      />
      <Button
        type="submit"
        className="w-full"
        loading={login.isPending}
      >
        Sign in
      </Button>
      <p className="text-center text-sm text-muted">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="text-primary hover:underline">
          Register
        </Link>
      </p>
    </form>
  );
}
