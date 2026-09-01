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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.push("/");
      return;
    }
    async function load() {
      try {
        const cropsResult = await apiFetch("/api/v1/crops");
        setCrops(cropsResult.data.crops || []);
        const historyResult = await apiFetch("/api/v1/history");
        setScans(historyResult.data.scans || []);
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
    <div className="min-h-screen bg-[#f7f5f0]">
      <header className="bg-[#2d4a2b] text-white px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Kisan Dost AI</h1>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/dashboard" className="font-medium">Dashboard</Link>
          <Link href="/scan" className="opacity-90 hover:opacity-100">New Scan</Link>
          <Link href="/chat" className="opacity-90 hover:opacity-100">Assistant</Link>
          <button onClick={handleLogout} className="opacity-90 hover:opacity-100">
            Logout
          </button>
        </nav>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-[#2d4a2b]">Your Farm</h2>
          <Link
            href="/scan"
            className="bg-[#2d4a2b] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#1f3520]"
          >
            + Scan a Crop
          </Link>
        </div>

        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : (
          <>
            <section className="mb-10">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Your Crops
              </h3>
              {crops.length === 0 ? (
                <p className="text-gray-500 text-sm">No crops added yet.</p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {crops.map((crop) => (
                    <div key={crop.id} className="bg-white rounded-xl p-4 border border-gray-200">
                      <p className="font-semibold text-[#2d4a2b]">{crop.crop_type}</p>
                      <p className="text-sm text-gray-500">{crop.stage || "—"}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Recent Scans
              </h3>
              {scans.length === 0 ? (
                <p className="text-gray-500 text-sm">No scans yet — upload a leaf photo to get started.</p>
              ) : (
                <div className="space-y-3">
                  {scans.map((scan) => (
                    <div
                      key={scan.scan_id}
                      className="bg-white rounded-xl p-4 border border-gray-200 flex items-center justify-between"
                    >
                      <div>
                        <p className="font-semibold text-[#2d4a2b]">{scan.disease_display_name}</p>
                        <p className="text-sm text-gray-500 capitalize">{scan.severity} severity</p>
                      </div>
                      <span className="text-sm font-medium text-gray-400">
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