"use client";

import { createContext, useContext, useState, useCallback } from "react";

interface ActiveProjectContextValue {
  projectKey: string;
  setProjectKey: (key: string) => void;
  clearProjectKey: () => void;
}

const ActiveProjectContext = createContext<ActiveProjectContextValue>({
  projectKey: "",
  setProjectKey: () => {},
  clearProjectKey: () => {},
});

export function ActiveProjectProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [projectKey, setKeyState] = useState("");
  const setProjectKey = useCallback((key: string) => setKeyState(key), []);
  const clearProjectKey = useCallback(() => setKeyState(""), []);

  return (
    <ActiveProjectContext.Provider
      value={{ projectKey, setProjectKey, clearProjectKey }}
    >
      {children}
    </ActiveProjectContext.Provider>
  );
}

export function useActiveProject() {
  return useContext(ActiveProjectContext);
}