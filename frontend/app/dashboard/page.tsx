"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, getToken, clearToken } from "@/lib/api";

type Crop = {
  id: string;
  crop_type: string;
  planted_date: string | null;
  stage: string | null;
};

type Scan = {
  scan_id: string;
  disease_display_name: string;
  severity: string;
  confidence: number;
  created_at: string;
};

export default function DashboardPage() {
  const router = useRouter();
  const [crops, setCrops] = useState<Crop[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [weather, setWeather] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    async function load() {
      try {
        const cropsResult = await apiFetch("/api/v1/crops");
        setCrops(cropsResult.data.crops || []);
        const historyResult = await apiFetch("/api/v1/history");
        setScans(historyResult.data.scans || []);

        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(async (pos) => {
            try {
              const w = await apiFetch(`/api/v1/weather?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`);
              setWeather(w.data);
            } catch {}
          });
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [router]);

  function handleLogout() {
    clearToken();
    router.push("/");
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f8f6f0] to-[#eef0e5]">
      <header className="bg-[#1f3d1a] text-white px-6 py-4 flex items-center justify-between shadow-sm">
        <h1 className="font-heading text-xl font-bold flex items-center gap-2">🌾 Kisan Dost AI</h1>
       <nav className="flex items-center gap-5 text-sm">
  <Link href="/dashboard" className="font-semibold">Dashboard</Link>
  <Link href="/tasks" className="opacity-90 hover:opacity-100 transition">Tasks</Link>
  <Link href="/scan" className="opacity-90 hover:opacity-100 transition">New Scan</Link>
  <Link href="/crops" className="opacity-90 hover:opacity-100 transition">Crops</Link>
          <Link href="/chat" className="opacity-90 hover:opacity-100 transition">Assistant</Link>
          <button onClick={handleLogout} className="opacity-90 hover:opacity-100 transition">
            Logout
          </button>
        </nav>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <h2 className="font-heading text-3xl font-extrabold text-[#1f3d1a]">Your Farm</h2>
          <Link
            href="/scan"
            className="bg-[#1f3d1a] text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-[#2d5527] transition shadow-sm"
          >
            + Scan a Crop
          </Link>
        </div>

        {loading ? (
         <div className="space-y-8 animate-pulse">
  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
    {[1, 2, 3].map((i) => (
      <div key={i} className="bg-white rounded-2xl p-5 border border-black/5 h-24">
        <div className="h-3 w-16 bg-gray-200 rounded mb-3" />
        <div className="h-7 w-12 bg-gray-200 rounded" />
      </div>
    ))}
  </div>
  <div className="h-4 w-24 bg-gray-200 rounded" />
  <div className="bg-white rounded-2xl p-4 border border-black/5 h-16" />
</div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
              <div className="bg-white rounded-2xl p-5 border border-black/5 shadow-sm">
                <p className="text-xs font-bold text-[#8a7a5c] uppercase tracking-widest mb-1">Crops</p>
                <p className="font-heading text-3xl font-extrabold text-[#1f3d1a]">{crops.length}</p>
              </div>
              <div className="bg-white rounded-2xl p-5 border border-black/5 shadow-sm">
                <p className="text-xs font-bold text-[#8a7a5c] uppercase tracking-widest mb-1">Total Scans</p>
                <p className="font-heading text-3xl font-extrabold text-[#1f3d1a]">{scans.length}</p>
              </div>
              <div className="bg-white rounded-2xl p-5 border border-black/5 shadow-sm">
                <p className="text-xs font-bold text-[#8a7a5c] uppercase tracking-widest mb-1">Weather</p>
                {weather ? (
                  <p className="font-heading text-3xl font-extrabold text-[#1f3d1a]">
                    {Math.round(weather.temperature)}°C
                    <span className="text-sm font-normal text-gray-500 ml-2 capitalize">{weather.condition}</span>
                  </p>
                ) : (
                  <p className="text-sm text-gray-400 mt-2">Enable location to see weather</p>
                )}
              </div>
            </div>

            <section className="mb-10">
              <h3 className="text-xs font-bold text-[#8a7a5c] uppercase tracking-widest mb-3">
                Your Crops
              </h3>
              {crops.length === 0 ? (
  <div className="bg-white rounded-2xl p-8 border border-dashed border-gray-300 text-center">
    <div className="text-3xl mb-2">🌱</div>
    <p className="text-gray-500 text-sm mb-3">No crops added yet.</p>
    <Link href="/crops" className="text-[#1f3d1a] text-sm font-semibold hover:underline">
      + Add your first crop
    </Link>
  </div>
) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {crops.map((crop) => (
                    <div key={crop.id} className="bg-white rounded-2xl p-4 border border-black/5 shadow-sm hover:shadow-md transition">
                      <p className="font-semibold text-[#1f3d1a]">{crop.crop_type}</p>
                      <p className="text-sm text-gray-500 capitalize">{crop.stage || "—"}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="text-xs font-bold text-[#8a7a5c] uppercase tracking-widest mb-3">
                Recent Scans
              </h3>
              {scans.length === 0 ? (
                <p className="text-gray-500 text-sm">No scans yet — upload a leaf photo to get started.</p>
              ) : (
                <div className="space-y-3">
                  {scans.map((scan) => (
                    <div
                      key={scan.scan_id}
                      className="bg-white rounded-2xl p-4 border border-black/5 shadow-sm hover:shadow-md transition flex items-center justify-between"
                    >
                      <div>
                        <p className="font-semibold text-[#1f3d1a]">{scan.disease_display_name}</p>
                        <p className="text-sm text-gray-500 capitalize">{scan.severity} severity</p>
                      </div>
                      <span className="text-sm font-bold text-[#d97706]">
                        {Math.round(scan.confidence * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}