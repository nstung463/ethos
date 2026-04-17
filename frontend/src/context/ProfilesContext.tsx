import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { ProviderProfile } from "../types";
import { loadProfiles, saveProfiles as persistProfiles } from "../utils/profiles";

function getInitialProfiles(): ProviderProfile[] {
  if (typeof window === "undefined") return [];
  return loadProfiles();
}

type ProfilesContextValue = {
  profiles: ProviderProfile[];
  activeProfileId: string;
  setActiveProfileId: (id: string) => void;
  saveProfiles: (nextProfiles: ProviderProfile[], nextActiveId: string) => void;
};

const ProfilesContext = createContext<ProfilesContextValue | null>(null);

export function ProfilesProvider({ children }: { children: ReactNode }) {
  const [profiles, setProfiles] = useState<ProviderProfile[]>(getInitialProfiles);
  const [activeProfileId, setActiveProfileId] = useState<string>(
    () => getInitialProfiles()[0]?.id ?? "",
  );

  // Fallback: if active profile was deleted, select first available
  useEffect(() => {
    if (profiles.length > 0 && !profiles.find((p) => p.id === activeProfileId)) {
      setActiveProfileId(profiles[0].id);
    }
  }, [profiles, activeProfileId]);

  function saveProfiles(nextProfiles: ProviderProfile[], nextActiveId: string) {
    setProfiles(nextProfiles);
    setActiveProfileId(nextActiveId);
    persistProfiles(nextProfiles);
  }

  return (
    <ProfilesContext.Provider value={{ profiles, activeProfileId, setActiveProfileId, saveProfiles }}>
      {children}
    </ProfilesContext.Provider>
  );
}

export function useProfiles() {
  const ctx = useContext(ProfilesContext);
  if (!ctx) throw new Error("useProfiles must be used within ProfilesProvider");
  return ctx;
}
