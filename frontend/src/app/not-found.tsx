import Link from "next/link";
import { BarChart3, Home } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-muted mb-4">
        <BarChart3 className="h-6 w-6 text-muted-foreground" />
      </div>
      <h1 className="text-2xl font-bold text-foreground">Page not found</h1>
      <p className="mt-2 text-sm text-muted-foreground text-center max-w-sm">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <Button className="mt-6" asChild>
        <Link href="/dashboard">
          <Home className="mr-2 h-4 w-4" />
          Go to dashboard
        </Link>
      </Button>
    </div>
  );
}
