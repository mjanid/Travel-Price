"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCurrentUser, useLogout } from "@/hooks/use-auth";
import { classNames } from "@/lib/utils";

const navLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/trips", label: "Trips" },
];

export function Header() {
  const { data: user } = useCurrentUser();
  const logout = useLogout();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="border-b border-border bg-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link href="/dashboard" className="text-lg font-semibold text-primary">
            Travel Price
          </Link>
          <nav className="hidden gap-6 sm:flex">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={classNames(
                  "text-sm font-medium transition-colors hover:text-primary",
                  pathname.startsWith(link.href)
                    ? "text-primary"
                    : "text-muted",
                )}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="hidden items-center gap-4 sm:flex">
          {user && (
            <span className="text-sm text-muted">{user.full_name}</span>
          )}
          <button
            onClick={logout}
            className="text-sm font-medium text-muted hover:text-foreground transition-colors"
          >
            Logout
          </button>
        </div>

        <button
          className="sm:hidden p-2"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
        >
          <svg
            className="h-6 w-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            {menuOpen ? (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            ) : (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            )}
          </svg>
        </button>
      </div>

      {menuOpen && (
        <div className="border-t border-border px-4 py-3 sm:hidden">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="block py-2 text-sm font-medium text-muted hover:text-primary"
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <button
            onClick={() => {
              setMenuOpen(false);
              logout();
            }}
            className="block w-full py-2 text-left text-sm font-medium text-muted hover:text-foreground"
          >
            Logout
          </button>
        </div>
      )}
    </header>
  );
}
