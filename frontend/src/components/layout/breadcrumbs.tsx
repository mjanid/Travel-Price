"use client";

import { Fragment } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import type { ApiResponse, Trip, PriceWatch } from "@/lib/types";

interface Breadcrumb {
  label: string;
  href?: string;
}

function useBreadcrumbs(): Breadcrumb[] {
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const segments = pathname.split("/").filter(Boolean);
  const crumbs: Breadcrumb[] = [];

  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i];
    const href = "/" + segments.slice(0, i + 1).join("/");
    const isLast = i === segments.length - 1;

    if (segment === "dashboard") {
      // Skip — "Home" already covers this
      continue;
    }

    if (segment === "trips") {
      crumbs.push(isLast ? { label: "Trips" } : { label: "Trips", href: "/trips" });
      continue;
    }

    if (segment === "watches") {
      crumbs.push(isLast ? { label: "Watches" } : { label: "Watches", href: "/watches" });
      continue;
    }

    if (segment === "settings") {
      crumbs.push({ label: "Settings" });
      continue;
    }

    if (segment === "new") {
      crumbs.push({ label: "New" });
      continue;
    }

    if (segment === "edit") {
      crumbs.push({ label: "Edit" });
      continue;
    }

    // UUID segment — look up trip or watch name from cache
    const prevSegment = segments[i - 1];
    if (prevSegment === "trips") {
      const cached = queryClient.getQueryData<ApiResponse<Trip>>(["trip", segment]);
      const trip = cached?.data;
      const label = trip
        ? `${trip.origin} → ${trip.destination}`
        : segment.slice(0, 8);
      crumbs.push(isLast ? { label } : { label, href });
      continue;
    }

    if (prevSegment === "watches") {
      const cached = queryClient.getQueryData<ApiResponse<PriceWatch>>(["watch", segment]);
      const watch = cached?.data;
      const label = watch ? watch.provider : segment.slice(0, 8);
      crumbs.push(isLast ? { label } : { label, href });
      continue;
    }

    // Unknown segment
    crumbs.push(isLast ? { label: segment } : { label: segment, href });
  }

  return crumbs;
}

export function Breadcrumbs() {
  const crumbs = useBreadcrumbs();

  if (crumbs.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className="mb-6 flex items-center gap-2 text-sm">
      <Link href="/dashboard" className="text-muted transition-colors hover:text-primary">
        Home
      </Link>
      {crumbs.map((crumb, idx) => (
        <Fragment key={idx}>
          <span className="text-muted">/</span>
          {crumb.href ? (
            <Link
              href={crumb.href}
              className="text-muted transition-colors hover:text-primary"
            >
              {crumb.label}
            </Link>
          ) : (
            <span className="font-medium text-foreground">{crumb.label}</span>
          )}
        </Fragment>
      ))}
    </nav>
  );
}
