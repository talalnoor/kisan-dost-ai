"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await apiFetch("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(result.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-[#f8f6f0] to-[#eef0e5] px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-3xl">🌾</span>
          <h1 className="font-heading text-3xl font-extrabold text-[#1f3d1a] tracking-tight">
            Kisan Dost AI
          </h1>
        </div>
        <p className="text-sm text-gray-500 mb-8 ml-1">Your farming assistant, in your hand.</p>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 bg-white/70 backdrop-blur-sm p-6 rounded-2xl border border-black/5 shadow-sm"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#1f3d1a]/40 transition"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#1f3d1a]/40 transition"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#1f3d1a] text-white py-2.5 rounded-xl font-semibold hover:bg-[#2d5527] transition disabled:opacity-50 shadow-sm"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>

          <p className="text-center text-sm text-gray-600">
            New here?{" "}
            <a href="/signup" className="text-[#1f3d1a] font-semibold hover:underline">
              Create an account
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}