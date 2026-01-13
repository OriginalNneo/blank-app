"use client";

import { useEffect } from "react";
import { AuthProvider } from "@/contexts/AuthContext";
import { applyTheme, applyThemeSync } from "@/utils/theme";

// Client component to handle theme application and provide context
export default function ClientProviders({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    // Apply theme synchronously first to avoid flash
    applyThemeSync();
    // Then apply async version for dynamic loading
    applyTheme().catch(console.error);
  }, []);

  return (
    <AuthProvider>
      {children}
    </AuthProvider>
  );
}