import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";

const items = [
  {
    href: "/hiring-assistant",
    title: "1. AI Hiring Assistant",
    description:
      "Trigger a live Hunar.ai voice screening call to a candidate and watch the structured results land in real time.",
  },
  {
    href: "/people-search",
    title: "2. People Search & Reachout",
    description:
      "Paste a job description, get matching candidates, reach out by voice, and see every response in one dashboard.",
  },
  {
    href: "/essay",
    title: "3. Attendance-tracking thought experiment",
    description:
      "How would you track attendance for 1,000 people across 100 locations, daily, with only LLMs and no smartphone apps?",
  },
];

export default function Home() {
  return (
    <div className="flex flex-col gap-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          Hunar.ai Take-Home Assignment
        </h1>
        <p className="max-w-2xl text-muted-foreground">
          Three parts, built with Next.js + TypeScript + shadcn/ui on the
          frontend and FastAPI (Python) on the backend, talking to Hunar&apos;s
          Voice Agents API for real outbound calls.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {items.map((item) => (
          <Card key={item.href} className="flex flex-col justify-between">
            <CardHeader>
              <CardTitle>{item.title}</CardTitle>
              <CardDescription>{item.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Link href={item.href} className={buttonVariants({ size: "sm" })}>
                Open
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
