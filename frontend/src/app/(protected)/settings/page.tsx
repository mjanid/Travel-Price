"use client";

import { useState, useEffect } from "react";
import { useCurrentUser, useUpdateProfile } from "@/hooks/use-auth";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  const { data: user } = useCurrentUser();
  const updateProfile = useUpdateProfile();

  const [fullName, setFullName] = useState("");
  const [nameInitialized, setNameInitialized] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Initialize full_name from user data once loaded
  useEffect(() => {
    if (user && !nameInitialized) {
      setFullName(user.full_name);
      setNameInitialized(true);
    }
  }, [user, nameInitialized]);

  function handleProfileSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    setSuccessMessage("");

    const newErrors: Record<string, string> = {};
    if (!fullName.trim()) {
      newErrors.full_name = "Name is required";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    updateProfile.mutate(
      { full_name: fullName.trim() },
      {
        onSuccess: () => setSuccessMessage("Profile updated."),
        onError: () => setErrors({ form: "Failed to update profile." }),
      },
    );
  }

  function handlePasswordSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrors({});
    setSuccessMessage("");

    const newErrors: Record<string, string> = {};
    if (password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }
    if (password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    updateProfile.mutate(
      { password },
      {
        onSuccess: () => {
          setSuccessMessage("Password updated.");
          setPassword("");
          setConfirmPassword("");
        },
        onError: () => setErrors({ form: "Failed to update password." }),
      },
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-foreground">Settings</h1>

      {successMessage && (
        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          {successMessage}
        </div>
      )}

      {errors.form && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {errors.form}
        </div>
      )}

      <Card>
        <h2 className="mb-4 text-lg font-medium text-foreground">Profile</h2>
        <form onSubmit={handleProfileSubmit} className="space-y-4">
          <Input
            label="Email"
            value={user?.email ?? ""}
            disabled
          />
          <Input
            label="Full Name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            error={errors.full_name}
          />
          <div className="flex justify-end">
            <Button type="submit" loading={updateProfile.isPending}>
              Save Profile
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <h2 className="mb-4 text-lg font-medium text-foreground">
          Change Password
        </h2>
        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <Input
            label="New Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={errors.password}
          />
          <Input
            label="Confirm Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={errors.confirmPassword}
          />
          <div className="flex justify-end">
            <Button type="submit" loading={updateProfile.isPending}>
              Update Password
            </Button>
          </div>
        </form>
      </Card>

      <Card>
        <h2 className="mb-4 text-lg font-medium text-foreground">
          Account Info
        </h2>
        <div className="space-y-2 text-sm text-muted">
          <p>
            <span className="font-medium text-foreground">Account ID:</span>{" "}
            {user?.id}
          </p>
          <p>
            <span className="font-medium text-foreground">Member since:</span>{" "}
            {user?.created_at
              ? new Date(user.created_at).toLocaleDateString("en-US", {
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                })
              : "—"}
          </p>
        </div>
      </Card>
    </div>
  );
}
