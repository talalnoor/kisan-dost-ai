"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, getToken } from "@/lib/api";

export default function ScanPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
      setResult(null);
      setError("");
    }
  }

  async function handleAnalyze() {
    if (!file) return;
    if (!getToken()) {
      router.push("/");
      return;
    }
    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("image", file);
    formData.append("crop_id", "357ee5c7-1da2-4299-8b49-a75b14346d83"); // demo crop
    formData.append("scan_type", "disease");

    // attach location for weather-risk if the browser allows it
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          formData.append("lat", String(pos.coords.latitude));
          formData.append("lon", String(pos.coords.longitude));
          await submit(formData);
        },
        async () => {
          await submit(formData); // no location permission — still works
        }
      );
    } else {
      await submit(formData);
    }
  }

  async function submit(formData: FormData) {
    try {
      const res = await apiFetch("/api/v1/disease/analyze", {
        method: "POST",
        body: formData,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err.message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#f7f5f0]">
      <header className="bg-[#2d4a2b] text-white px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Kisan Dost AI</h1>
        <Link href="/dashboard" className="text-sm opacity-90 hover:opacity-100">
          ← Back to Dashboard
        </Link>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8">
        <h2 className="text-2xl font-bold text-[#2d4a2b] mb-6">Scan a Crop</h2>

        {!result && (
          <div className="bg-white rounded-2xl border border-gray-200 p-6">
            <label className="block border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-[#2d4a2b] transition">
              {preview ? (
                <img src={preview} alt="preview" className="max-h-64 mx-auto rounded-lg" />
              ) : (
                <p className="text-gray-500">Click to upload a leaf photo (JPG/PNG)</p>
              )}
              <input type="file" accept="image/jpeg,image/png" onChange={handleFileChange} className="hidden" />
            </label>

            {error && <p className="text-sm text-red-600 mt-4">{error}</p>}

            <button
              onClick={handleAnalyze}
              disabled={!file || loading}
              className="w-full mt-4 bg-[#2d4a2b] text-white py-3 rounded-lg font-medium hover:bg-[#1f3520] transition disabled:opacity-50"
            >
              {loading ? "Analyzing..." : "Analyze"}
            </button>
          </div>
        )}

        {result && (
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
            {preview && <img src={preview} alt="scanned leaf" className="w-full h-48 object-cover" />}

            <div className="p-6">
              {result.low_confidence && (
                <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-lg px-3 py-2 mb-4">
                  We're not fully confident in this result — try a clearer photo for a more reliable diagnosis.
                </div>
              )}

              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-[#2d4a2b]">{result.disease}</h3>
                  <p className="text-sm text-gray-500 capitalize">{result.severity} severity</p>
                </div>
                <span className="text-2xl font-bold text-[#2d4a2b]">
                  {Math.round(result.confidence * 100)}%
                </span>
              </div>

              {result.weather_risk && (
                <div
                  className={`text-sm rounded-lg px-3 py-2 mb-4 ${
                    result.weather_risk.level === "high"
                      ? "bg-red-50 text-red-700 border border-red-200"
                      : result.weather_risk.level === "medium"
                      ? "bg-amber-50 text-amber-700 border border-amber-200"
                      : "bg-green-50 text-green-700 border border-green-200"
                  }`}
                >
                  <span className="font-semibold capitalize">{result.weather_risk.level} weather risk:</span>{" "}
                  {result.weather_risk.reason}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-1">Symptoms</h4>
                  <ul className="text-sm text-gray-600 list-disc list-inside space-y-0.5">
                    {result.symptoms.map((s: string, i: number) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-1">Treatment</h4>
                  <ul className="text-sm text-gray-600 list-disc list-inside space-y-0.5">
                    {result.treatment.map((t: string, i: number) => (
                      <li key={i}>{t}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 mb-1">Prevention</h4>
                  <ul className="text-sm text-gray-600 list-disc list-inside space-y-0.5">
                    {result.prevention.map((p: string, i: number) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <button
                onClick={() => {
                  setResult(null);
                  setFile(null);
                  setPreview(null);
                }}
                className="w-full mt-6 bg-gray-100 text-gray-700 py-2.5 rounded-lg font-medium hover:bg-gray-200 transition"
              >
                Scan Another
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}