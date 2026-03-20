import Link from "next/link";
import { HomeAuthRedirect } from "@/components/auth/home-auth-redirect";
import {
  BarChart3,
  Key,
  ShieldCheck,
  Users,
  Zap,
  LineChart,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: LineChart,
    title: "Real-time analytics",
    description:
      "Track request counts, response times, and error rates with live time-series charts and configurable granularity.",
  },
  {
    icon: Key,
    title: "Secure API keys",
    description:
      "Generate scoped keys per environment. Keys are hashed at rest and displayed only once, with rotation support.",
  },
  {
    icon: Users,
    title: "Team collaboration",
    description:
      "Invite teammates as owners, members, or viewers. Role-based access ensures the right people see the right data.",
  },
  {
    icon: Zap,
    title: "Instant integration",
    description:
      "Send metrics from any service in seconds with a single HTTP call. No agent, no complex setup.",
  },
  {
    icon: BarChart3,
    title: "Endpoint insights",
    description:
      "Drill into per-endpoint performance. Sort by request count, error rate, or response time to find bottlenecks fast.",
  },
  {
    icon: ShieldCheck,
    title: "Production-grade security",
    description:
      "Argon2 password hashing, JWT with refresh, rate limiting, and timing-attack prevention built in.",
  },
] as const;

export default function LandingPage() {
  return (
    <>
      <HomeAuthRedirect />
      <div className="min-h-screen bg-background">
      {/* Nav */}
      <header className="border-b border-border">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary">
              <BarChart3 className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-semibold text-sm tracking-tight">
              API Analytics
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <Button
              variant="secondary"
              className="border border-primary/20 bg-primary/5 text-primary hover:bg-primary/10 hover:text-primary"
              size="sm"
              asChild
            >
              <Link href="/login">Sign in</Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/register">Get started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-medium mb-6">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary" />
          Open source · Self-hosted ready
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-foreground max-w-3xl mx-auto leading-tight">
          Monitor your APIs with clarity
        </h1>
        <p className="mt-5 text-lg text-muted-foreground max-w-xl mx-auto">
          A lightweight, multi-tenant analytics platform for tracking API
          performance. Get dashboards, endpoint insights, and team access
          controls in minutes.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button size="lg" asChild>
            <Link href="/register">Start for free</Link>
          </Button>
          <Button
            size="lg"
            variant="secondary"
            className="border border-primary/20 bg-primary/5 text-primary hover:bg-primary/10 hover:text-primary"
            asChild
          >
            <Link href="/login">Sign in</Link>
          </Button>
        </div>
      </section>

      {/* Feature grid */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="p-6 rounded-xl bg-card border border-border"
            >
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 mb-4">
                <feature.icon className="h-5 w-5 text-primary" />
              </div>
              <h3 className="text-sm font-semibold text-foreground mb-1.5">
                {feature.title}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-border">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
          <h2 className="text-2xl font-bold text-foreground">
            Ready to monitor your APIs?
          </h2>
          <p className="mt-2 text-muted-foreground">
            Create an account and add your first project in under 5 minutes.
          </p>
          <Button className="mt-6" size="lg" asChild>
            <Link href="/register">Get started — it&apos;s free</Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-12 flex items-center justify-center text-xs text-muted-foreground">
          API Analytics — built with FastAPI + Next.js
        </div>
      </footer>
    </div>
    </>
  );
}
