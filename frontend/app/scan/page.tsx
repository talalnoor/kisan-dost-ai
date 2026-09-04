"use client";

import { useState, useEffect } from "react";
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
  const [cropId, setCropId] = useState<string | null>(null);
  const [scanType, setScanType] = useState<"disease" | "pest">("disease");

  useEffect(() => {
    if (!getToken()) {
      router.push("/");
      return;
    }
    apiFetch("/api/v1/crops")
      .then((res) => {
        const crops = res.data.crops || [];
        if (crops.length > 0) {
          setCropId(crops[0].id);
        } else {
          // No crops yet — create a default one so scanning still works
          return apiFetch("/api/v1/crops", {
            method: "POST",
            body: JSON.stringify({ crop_type: "My Crop", stage: "growing" }),
          }).then((created) => setCropId(created.data.id));
        }
      })
      .catch(() => {});
  }, [router]);

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
    formData.append("crop_id", cropId || "");
    formData.append("scan_type", scanType);

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

  const severityColor: Record<string, string> = {
    none: "bg-green-50 text-green-700 border-green-200",
    mild: "bg-yellow-50 text-yellow-700 border-yellow-200",
    moderate: "bg-orange-50 text-orange-700 border-orange-200",
    severe: "bg-red-50 text-red-700 border-red-200",
    unknown: "bg-gray-50 text-gray-600 border-gray-200",
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f8f6f0] to-[#eef0e5]">
      <header className="bg-[#1f3d1a] text-white px-6 py-4 flex items-center justify-between shadow-sm">
        <h1 className="font-heading text-xl font-bold flex items-center gap-2">🌾 Kisan Dost AI</h1>
        <Link href="/dashboard" className="text-sm opacity-90 hover:opacity-100 transition">
          ← Back to Dashboard
        </Link>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-10">
        <h2 className="font-heading text-3xl font-extrabold text-[#1f3d1a] mb-4">Scan a Crop</h2>

        {!result && (
          <div className="mb-4">
            <div className="flex bg-white rounded-xl border border-black/5 shadow-sm p-1 w-fit">
              <button
                onClick={() => setScanType("disease")}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${scanType === "disease" ? "bg-[#1f3d1a] text-white" : "text-gray-500"}`}
              >
                🍃 Disease
              </button>
              <button
                onClick={() => setScanType("pest")}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${scanType === "pest" ? "bg-[#1f3d1a] text-white" : "text-gray-500"}`}
              >
                🐛 Pest
              </button>
            </div>
            {scanType === "pest" && (
              <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mt-2">
                Pest-specific detection is in early development — results currently come from our disease-focused model and may be less accurate for pest damage.
              </p>
            )}
          </div>
        )}

        {!result && (
          <div className="bg-white rounded-2xl border border-black/5 shadow-sm p-6">
            <label className="block border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-[#1f3d1a] hover:bg-[#f8f6f0] transition">
              {preview ? (
                <img src={preview} alt="preview" className="max-h-64 mx-auto rounded-lg shadow-sm" />
              ) : (
                <div className="text-gray-400">
                  <div className="text-4xl mb-2">📷</div>
                  <p className="text-gray-500 font-medium">Click to upload a leaf photo</p>
                  <p className="text-xs text-gray-400 mt-1">JPG or PNG, up to 5MB</p>
                </div>
              )}
              <input type="file" accept="image/jpeg,image/png" onChange={handleFileChange} className="hidden" />
            </label>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mt-4">{error}</p>
            )}

            <button
              onClick={handleAnalyze}
              disabled={!file || loading}
              className="w-full mt-4 bg-[#1f3d1a] text-white py-3 rounded-xl font-semibold hover:bg-[#2d5527] transition disabled:opacity-50 shadow-sm"
            >
              {loading ? "Analyzing..." : "Analyze"}
            </button>
          </div>
        )}

        {result && (
          <div className="bg-white rounded-2xl border border-black/5 shadow-sm overflow-hidden">
            {preview && <img src={preview} alt="scanned leaf" className="w-full h-48 object-cover" />}

            <div className="p-6">
              {result.low_confidence && (
                <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-lg px-3 py-2 mb-4">
                  We're not fully confident in this result — try a clearer photo for a more reliable diagnosis.
                </div>
              )}

              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-heading text-xl font-bold text-[#1f3d1a]">{result.disease}</h3>
                  <span className={`inline-block text-xs font-semibold capitalize px-2 py-0.5 rounded-full border mt-1 ${severityColor[result.severity] || severityColor.unknown}`}>
                    {result.severity} severity
                  </span>
                </div>
                <span className="text-2xl font-heading font-extrabold text-[#1f3d1a]">
                  {Math.round(result.confidence * 100)}%
                </span>
              </div>

              {result.weather_risk && (
                <div
                  className={`text-sm rounded-lg px-3 py-2 mb-4 border ${
                    result.weather_risk.level === "high"
                      ? "bg-red-50 text-red-700 border-red-200"
                      : result.weather_risk.level === "medium"
                      ? "bg-amber-50 text-amber-700 border-amber-200"
                      : "bg-green-50 text-green-700 border-green-200"
                  }`}
                >
                  <span className="font-semibold capitalize">{result.weather_risk.level} weather risk:</span>{" "}
                  {result.weather_risk.reason}
                </div>
              )}

              <div className="space-y-4">
                {result.symptoms?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-bold text-[#1f3d1a] mb-1">Symptoms</h4>
                    <ul className="text-sm text-gray-600 list-disc list-inside space-y-0.5">
                      {result.symptoms.map((s: string, i: number) => <li key={i}>{s}</li>)}
                    </ul>
                  </div>
                )}
                {result.treatment?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-bold text-[#1f3d1a] mb-1">Treatment</h4>
                    <ul className="text-sm text-gray-600 list-disc list-inside space-y-0.5">
                      {result.treatment.map((t: string, i: number) => <li key={i}>{t}</li>)}
                    </ul>
                  </div>
                )}
                {result.prevention?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-bold text-[#1f3d1a] mb-1">Prevention</h4>
                    <ul className="text-sm text-gray-600 list-disc list-inside space-y-0.5">
                      {result.prevention.map((p: string, i: number) => <li key={i}>{p}</li>)}
                    </ul>
                  </div>
                )}
              </div>

              <button
                onClick={() => {
                  const text = `Kisan Dost AI — Scan Report\n\nDisease: ${result.disease}\nConfidence: ${Math.round(result.confidence * 100)}%\nSeverity: ${result.severity}\n\nSymptoms:\n${result.symptoms.map((s: string) => "- " + s).join("\n")}\n\nTreatment:\n${result.treatment.map((t: string) => "- " + t).join("\n")}\n\nPrevention:\n${result.prevention.map((p: string) => "- " + p).join("\n")}\n\nGenerated by Kisan Dost AI`;
                  const blob = new Blob([text], { type: "text/plain" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `kisan-dost-report-${result.scan_id.slice(0, 8)}.txt`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="w-full mt-3 bg-[#f3f1e9] text-[#1f3d1a] py-2.5 rounded-xl font-semibold hover:bg-[#e8e5d8] transition"
              >
                📄 Download Report
              </button>

              <button
                onClick={() => {
                  setResult(null);
                  setFile(null);
                  setPreview(null);
                }}
                className="w-full mt-3 bg-[#f3f1e9] text-[#1f3d1a] py-2.5 rounded-xl font-semibold hover:bg-[#e8e5d8] transition"
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