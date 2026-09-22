import { z } from "zod";

export const AdminSchema = z.object({
  username: z.string().min(1, { message: "Required" }),
  is_sudo: z.boolean(),
  telegram_id: z.number().nullable().optional(),
  discord_webhook: z.string().nullable().optional(),
  users_usage: z.number().nullable().optional(),
  users_count: z.number().nullable().optional(),
  active_users_count: z.number().nullable().optional(),
});

export type Admin = z.infer<typeof AdminSchema>;

export const AdminCreateSchema = z.object({
  username: z
    .string()
    .min(1, { message: "Required" })
    .regex(/^[a-zA-Z0-9_-]+$/, {
      message: "Only letters, numbers, underscores and hyphens allowed",
    }),
  password: z.string().min(1, { message: "Required" }),
  is_sudo: z.boolean().default(false),
  telegram_id: z.coerce.number().nullable().optional(),
  discord_webhook: z.string().nullable().optional(),
});

export type AdminCreate = z.infer<typeof AdminCreateSchema>;

export const AdminModifySchema = z.object({
  password: z.string().optional().or(z.literal("")),
  is_sudo: z.boolean(),
  telegram_id: z.coerce.number().nullable().optional(),
  discord_webhook: z.string().nullable().optional(),
});

export type AdminModify = z.infer<typeof AdminModifySchema>;

export interface MarzyarAdminSettings {
  admin_id: number;
  username: string;
  is_sudo: boolean;
  users_limit: number | null;
  traffic_limit: number | null;
  oversell_allowed: boolean;
  allowed_inbounds: string[] | null;
  quota_used_traffic: number;
  current_users_count: number;
  current_allocated_traffic: number;
  current_consumed_traffic: number;
  is_quota_exceeded: boolean;
  is_user_limit_exceeded: boolean;
  locked_users_count: number;
}

export interface MarzyarAdminSettingsModify {
  users_limit?: number | null;
  traffic_limit?: number | null;
  oversell_allowed?: boolean;
  allowed_inbounds?: string[] | null;
}

export interface MarzyarMyLimits {
  username: string;
  is_sudo: boolean;
  users_limit: number | null;
  traffic_limit: number | null;
  oversell_allowed: boolean;
  allowed_inbounds: string[] | null;
  current_users_count: number;
  current_allocated_traffic: number;
  current_consumed_traffic: number;
  is_quota_exceeded: boolean;
  is_user_limit_exceeded: boolean;
  is_allocation_limit_reached?: boolean;
  locked_users_count: number;
}
