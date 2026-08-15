"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Home" },
  { href: "/hiring-assistant", label: "1. Hiring Assistant" },
  { href: "/people-search", label: "2. People Search & Reachout" },
  { href: "/essay", label: "3. Attendance Essay" },
];

export function SiteNav() {
  const pathname = usePathname();
  return (
    <header className="border-b bg-background">
      <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-1 px-4 py-3">
        <span className="mr-4 text-sm font-semibold tracking-tight">
          Hunar.ai Assignment
        </span>
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm transition-colors hover:bg-muted",
              pathname === l.href
                ? "bg-muted font-medium text-foreground"
                : "text-muted-foreground"
            )}
          >
            {l.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
