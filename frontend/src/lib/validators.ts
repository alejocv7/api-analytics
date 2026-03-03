import { z } from "zod";
import { MAX_DATE_RANGE_DAYS, MIN_DATE_RANGE_MINUTES } from "@/lib/constants";

// ============================================================
// Auth
// ============================================================

export const loginSchema = z.object({
  username: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

export const registerSchema = z
  .object({
    email: z.string().email("Please enter a valid email address"),
    full_name: z.string().min(1, "Full name is required").max(100),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[0-9]/, "Password must contain at least one number"),
    confirm_password: z.string(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export type RegisterFormValues = z.infer<typeof registerSchema>;

// ============================================================
// Project
// ============================================================

export const createProjectSchema = z.object({
  name: z
    .string()
    .min(1, "Project name is required")
    .max(100, "Project name must be 100 characters or less"),
  description: z.string().max(500).optional(),
});

export type CreateProjectFormValues = z.infer<typeof createProjectSchema>;

export const updateProjectSchema = z.object({
  name: z
    .string()
    .min(1, "Project name is required")
    .max(100, "Project name must be 100 characters or less"),
  description: z.string().max(500).optional(),
  is_active: z.boolean(),
});

export type UpdateProjectFormValues = z.infer<typeof updateProjectSchema>;

// ============================================================
// API Key
// ============================================================

export const createApiKeySchema = z.object({
  name: z
    .string()
    .min(1, "Key name is required")
    .max(100, "Key name must be 100 characters or less"),
  expires_at: z.string().nullable().optional(),
});

export type CreateApiKeyFormValues = z.infer<typeof createApiKeySchema>;

// ============================================================
// Member
// ============================================================

export const inviteMemberSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  role: z.enum(["member", "viewer"]),
});

export type InviteMemberFormValues = z.infer<typeof inviteMemberSchema>;

// ============================================================
// Date Range
// ============================================================

export const dateRangeSchema = z
  .object({
    start_time: z.date(),
    end_time: z.date(),
  })
  .refine(
    (data) => data.end_time >= data.start_time,
    "End date must be after start date",
  )
  .refine((data) => {
    const diffMinutes =
      (data.end_time.getTime() - data.start_time.getTime()) / 60000;
    return diffMinutes >= MIN_DATE_RANGE_MINUTES;
  }, `Date range must be at least ${MIN_DATE_RANGE_MINUTES} minute`)
  .refine((data) => {
    const diffDays =
      (data.end_time.getTime() - data.start_time.getTime()) / 86400000;
    return diffDays <= MAX_DATE_RANGE_DAYS;
  }, `Date range cannot exceed ${MAX_DATE_RANGE_DAYS} days`)
  .refine((data) => data.end_time <= new Date(), "End date cannot be in the future");

// ============================================================
// Profile
// ============================================================

export const updateProfileSchema = z.object({
  full_name: z.string().min(1, "Full name is required").max(100),
});

export type UpdateProfileFormValues = z.infer<typeof updateProfileSchema>;
