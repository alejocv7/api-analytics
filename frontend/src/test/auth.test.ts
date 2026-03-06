import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  isAuthenticated,
} from "../lib/auth";

describe("auth lib", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  it("should store and retrieve tokens", () => {
    setTokens("access", "refresh");
    expect(getAccessToken()).toBe("access");
    expect(getRefreshToken()).toBe("refresh");
  });

  it("should clear tokens", () => {
    setTokens("access", "refresh");
    clearTokens();
    expect(getAccessToken()).toBe(null);
    expect(getRefreshToken()).toBe(null);
  });

  it("should check authentication status", () => {
    expect(isAuthenticated()).toBe(false);
    setTokens("access", "refresh");
    expect(isAuthenticated()).toBe(true);
  });
});
