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

const STAGES = ["seedling", "growing", "flowering", "fruiting", "harvest"];

export default function CropsPage() {
  const router = useRouter();
  const [crops, setCrops] = useState<Crop[]>([]);
  const [cropType, setCropType] = useState("");
  const [stage, setStage] = useState("seedling");
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    if (!getToken()) {
    router.push("/login");
      return;
    }
    apiFetch("/api/v1/crops")
      .then((res) => setCrops(res.data.crops || []))
      .finally(() => setLoading(false));
  }, [router]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!cropType.trim()) return;
    setAdding(true);
    try {
      const res = await apiFetch("/api/v1/crops", {
        method: "POST",
        body: JSON.stringify({ crop_type: cropType, stage }),
      });
      setCrops((prev) => [...prev, res.data]);
      setCropType("");
      setStage("seedling");
    } catch {}
    setAdding(false);
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f8f6f0] to-[#eef0e5]">
      <header className="bg-[#1f3d1a] text-white px-6 py-4 flex items-center justify-between shadow-sm">
        <h1 className="font-heading text-xl font-bold flex items-center gap-2">🌾 Kisan Dost AI</h1>
        <nav className="flex items-center gap-5 text-sm">
          <Link href="/dashboard" className="opacity-90 hover:opacity-100 transition">Dashboard</Link>
          <Link href="/crops" className="font-semibold">Crops</Link>
          <Link href="/tasks" className="opacity-90 hover:opacity-100 transition">Tasks</Link>
          <Link href="/chat" className="opacity-90 hover:opacity-100 transition">Assistant</Link>
          <button onClick={() => { clearToken(); router.push("/"); }} className="opacity-90 hover:opacity-100 transition">
            Logout
          </button>
        </nav>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-10">
        <h2 className="font-heading text-3xl font-extrabold text-[#1f3d1a] mb-6">My Crops</h2>

        <form onSubmit={handleAdd} className="bg-white rounded-2xl p-5 border border-black/5 shadow-sm mb-8 flex gap-2">
          <input
            value={cropType}
            onChange={(e) => setCropType(e.target.value)}
            placeholder="e.g. Wheat, Cotton, Tomato"
            className="flex-1 px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1f3d1a]/40"
          />
          <select
            value={stage}
            onChange={(e) => setStage(e.target.value)}
            className="px-3 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#1f3d1a]/40 capitalize"
          >
            {STAGES.map((s) => (
              <option key={s} value={s} className="capitalize">{s}</option>
            ))}
          </select>
          <button
            type="submit"
            disabled={adding}
            className="bg-[#1f3d1a] text-white px-5 py-2.5 rounded-xl font-semibold hover:bg-[#2d5527] transition disabled:opacity-50"
          >
            Add
          </button>
        </form>

        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : crops.length === 0 ? (
          <p className="text-gray-500 text-sm">No crops added yet.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {crops.map((crop) => (
              <div key={crop.id} className="bg-white rounded-2xl p-4 border border-black/5 shadow-sm">
                <p className="font-semibold text-[#1f3d1a]">{crop.crop_type}</p>
                <span className="inline-block text-xs font-semibold capitalize px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200 mt-1">
                  {crop.stage}
                </span>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}