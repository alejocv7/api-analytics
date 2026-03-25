"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import Link from "next/link";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/shared/password-input";
import { useAuth } from "@/providers/auth-provider";
import { apiClient, ApiClientError } from "@/lib/api-client";
import { registerSchema, type RegisterFormValues } from "@/lib/validators";
import type { User } from "@/types/api";

export function RegisterForm() {
  const { login } = useAuth();
  const router = useRouter();

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      full_name: "",
      password: "",
      confirm_password: "",
    },
  });

  async function onSubmit(values: RegisterFormValues) {
    try {
      // Register account
      await apiClient.post<User>("/auth/register", {
        email: values.email,
        full_name: values.full_name,
        password: values.password,
      });

      // Auto-login
      await login({ email: values.email, password: values.password });

      toast.success("Account created! Welcome aboard.");
      router.push("/projects");
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 400 || err.status === 409) {
          toast.error("Registration failed. Please try again.");
        } else if (err.status === 422 && Array.isArray(err.details)) {
          // Map backend validation errors to their form fields
          let handled = false;
          for (const detail of err.details as {
            field: unknown[];
            message: string;
          }[]) {
            const field = detail.field?.at(-1);
            const message = detail.message.replace(/^Value error,\s*/i, "");
            if (field === "password") {
              form.setError("password", { message });
              handled = true;
            } else if (field === "email") {
              form.setError("email", { message });
              handled = true;
            }
          }
          if (!handled) {
            toast.error("Registration failed. Please check your details.");
          }
        } else if (err.status === 429) {
          toast.error(err.message);
        } else {
          toast.error(err.message || "Registration failed. Please try again.");
        }
      } else {
        toast.error("An unexpected error occurred.");
      }
    }
  }

  return (
    <Card className="border-border shadow-sm">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-semibold">Create account</CardTitle>
        <CardDescription>
          Get started monitoring your APIs in minutes
        </CardDescription>
      </CardHeader>

      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Full name</FormLabel>
                  <FormControl>
                    <Input autoComplete="name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" autoComplete="email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <PasswordInput
                      placeholder="Min 8 chars, 1 uppercase, 1 number"
                      autoComplete="new-password"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm password</FormLabel>
                  <FormControl>
                    <PasswordInput autoComplete="new-password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button
              type="submit"
              className="w-full"
              disabled={form.formState.isSubmitting}
            >
              {form.formState.isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account…
                </>
              ) : (
                "Create account"
              )}
            </Button>
          </form>
        </Form>
      </CardContent>

      <CardFooter className="flex justify-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link
          href="/login"
          className="ml-1 font-medium text-primary hover:underline"
        >
          Sign in
        </Link>
      </CardFooter>
    </Card>
  );
}
