"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRegister } from "@/hooks/use-auth";
import { registerSchema } from "@/lib/validators";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function RegisterForm() {
  const router = useRouter();
  const register = useRegister();
  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});

    const result = registerSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: Record<string, string> = {};
      for (const issue of result.error.issues) {
        const key = String(issue.path[0]);
        if (!fieldErrors[key]) fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    register.mutate(result.data, {
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
        label="Full name"
        value={form.full_name}
        onChange={(e) => setForm({ ...form, full_name: e.target.value })}
        error={errors.full_name}
        autoComplete="name"
      />
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
        autoComplete="new-password"
      />
      <Button
        type="submit"
        className="w-full"
        loading={register.isPending}
      >
        Create account
      </Button>
      <p className="text-center text-sm text-muted">
        Already have an account?{" "}
        <Link href="/login" className="text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
