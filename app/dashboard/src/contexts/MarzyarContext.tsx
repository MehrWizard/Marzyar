import { useQuery } from "react-query";
import { fetch } from "service/http";
import {
  MarzyarAdminSettings,
  MarzyarAdminSettingsModify,
  MarzyarMyLimits,
} from "types/Admin";
import { create } from "zustand";

export const FetchMarzyarAdminsQueryKey = "fetch-marzyar-admins-key";
export const FetchMarzyarMyLimitsQueryKey = "fetch-marzyar-my-limits-key";

export type MarzyarStore = {
  adminSettings: Record<number, MarzyarAdminSettings>;
  adminSettingsByUsername: Record<string, MarzyarAdminSettings>;
  myLimits: MarzyarMyLimits | null;
  fetchAdmins: () => Promise<MarzyarAdminSettings[]>;
  fetchMyLimits: () => Promise<MarzyarMyLimits>;
  updateAdminSettings: (
    adminIdentifier: string | number,
    body: MarzyarAdminSettingsModify
  ) => Promise<MarzyarAdminSettings>;
  resetAdminQuota: (adminIdentifier: string | number) => Promise<MarzyarAdminSettings>;
};

export const useMarzyar = create<MarzyarStore>((set) => ({
  adminSettings: {},
  adminSettingsByUsername: {},
  myLimits: null,

  fetchAdmins() {
    return fetch<MarzyarAdminSettings[]>("/marzyar/admins").then((data) => {
      const byId: Record<number, MarzyarAdminSettings> = {};
      const byName: Record<string, MarzyarAdminSettings> = {};
      data.forEach((s) => {
        byId[s.admin_id] = s;
        byName[s.username] = s;
      });
      set({ adminSettings: byId, adminSettingsByUsername: byName });
      return data;
    });
  },

  fetchMyLimits() {
    return fetch<MarzyarMyLimits>("/marzyar/my_limits").then((data) => {
      set({ myLimits: data });
      return data;
    });
  },

  updateAdminSettings(adminIdentifier, body) {
    return fetch<MarzyarAdminSettings>(`/marzyar/admin/${adminIdentifier}/settings`, {
      method: "PUT",
      body,
    }).then((updated) => {
      set((state) => ({
        adminSettings: {
          ...state.adminSettings,
          [updated.admin_id]: updated,
        },
        adminSettingsByUsername: {
          ...state.adminSettingsByUsername,
          [updated.username]: updated,
        },
      }));
      return updated;
    });
  },

  resetAdminQuota(adminIdentifier) {
    return fetch<MarzyarAdminSettings>(`/marzyar/admin/${adminIdentifier}/reset_quota`, {
      method: "POST",
    }).then((updated) => {
      set((state) => ({
        adminSettings: {
          ...state.adminSettings,
          [updated.admin_id]: updated,
        },
        adminSettingsByUsername: {
          ...state.adminSettingsByUsername,
          [updated.username]: updated,
        },
      }));
      return updated;
    });
  },
}));

export const useMarzyarAdminsQuery = (isSudo?: boolean) => {
  return useQuery({
    queryKey: FetchMarzyarAdminsQueryKey,
    queryFn: useMarzyar.getState().fetchAdmins,
    enabled: !!isSudo,
    refetchInterval: 30000,
    refetchOnWindowFocus: false,
    staleTime: 20000,
  });
};

export const useMarzyarMyLimitsQuery = (enabled = true) => {
  return useQuery({
    queryKey: FetchMarzyarMyLimitsQueryKey,
    queryFn: useMarzyar.getState().fetchMyLimits,
    enabled,
    refetchInterval: 30000,
    refetchOnWindowFocus: false,
    staleTime: 15000,
  });
};
