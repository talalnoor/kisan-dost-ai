"use client";

import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f8f6f0] to-[#eef0e5]">
      <header className="px-6 py-5 flex items-center justify-between max-w-6xl mx-auto">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🌾</span>
          <span className="font-heading text-xl font-extrabold text-[#1f3d1a]">Kisan Dost AI</span>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <Link href="/login" className="text-[#1f3d1a] font-semibold hover:underline">Sign In</Link>
          <Link
            href="/signup"
            className="bg-[#1f3d1a] text-white px-4 py-2 rounded-xl font-semibold hover:bg-[#2d5527] transition shadow-sm"
          >
            Get Started
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 pt-16 pb-20 text-center">
        <div className="inline-block bg-white/70 backdrop-blur-sm border border-black/5 rounded-full px-4 py-1.5 text-xs font-semibold text-[#1f3d1a] mb-6 shadow-sm">
          🇵🇰 Built for Pakistan's Farmers · Alibaba Cloud AI Hackathon 2026
        </div>
        <h1 className="font-heading text-5xl sm:text-6xl font-extrabold text-[#1f3d1a] leading-tight mb-5">
          Your farming assistant,
          <br />in your hand.
        </h1>
        <p className="text-lg text-gray-600 max-w-xl mx-auto mb-10">
          Photograph a diseased leaf and get an instant AI diagnosis, weather-aware risk, and a
          bilingual farming assistant — in Urdu or English, by voice or text.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link
            href="/signup"
            className="bg-[#1f3d1a] text-white px-8 py-3.5 rounded-xl font-semibold hover:bg-[#2d5527] transition shadow-md text-base"
          >
            Try It Free →
          </Link>
          <Link
            href="/login"
            className="bg-white text-[#1f3d1a] px-8 py-3.5 rounded-xl font-semibold hover:bg-gray-50 transition shadow-sm border border-black/5 text-base"
          >
            Sign In
          </Link>
        </div>
      </main>

      <section className="max-w-5xl mx-auto px-6 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {[
            ["📷", "Instant Diagnosis", "Real AI classifies crop diseases across 38 categories — not a guess, a trained model."],
            ["🌦️", "Weather-Aware Risk", "Live weather combines with your diagnosis to flag real outbreak risk."],
            ["💬", "Bilingual Assistant", "Ask follow-up questions in Urdu or English — by voice or text."],
          ].map(([icon, title, desc]) => (
            <div key={title} className="bg-white rounded-2xl p-6 border border-black/5 shadow-sm text-left hover:shadow-md transition">
              <div className="text-3xl mb-3">{icon}</div>
              <h3 className="font-heading font-bold text-[#1f3d1a] mb-1.5">{title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="text-center text-xs text-gray-400 pb-10">
        Kisan Dost AI · Built with FastAPI, Next.js, Supabase, and Qwen
      </footer>
    </div>
  );
}