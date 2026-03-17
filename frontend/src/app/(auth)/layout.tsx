import Link from "next/link";
import { BarChart3 } from "lucide-react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-8">
        {/* Logo */}
        <div className="flex flex-col items-center space-y-2">
          <Link
            href="/"
            className="flex items-center gap-3 text-foreground hover:opacity-80 transition-opacity"
          >
            <div className="flex items-center justify-center w-10 h-10 sm:w-11 sm:h-11 rounded-3xl bg-primary">
              <BarChart3 className="h-5 w-5 sm:h-6 sm:w-6 text-primary-foreground" />
            </div>
            <span className="font-bold text-xl sm:text-2xl tracking-tight">
              API Analytics
            </span>
          </Link>
        </div>

        {children}
      </div>
    </div>
  );
}
