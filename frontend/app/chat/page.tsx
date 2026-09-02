"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, getToken } from "@/lib/api";
function renderMarkdown(text: string) {
  const html = text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
  return { __html: html };
}
type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState<"en" | "ur">("en");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!getToken()) router.push("/");
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim()) return;
    const userMessage = input;
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setLoading(true);

    try {
      const res = await apiFetch("/api/v1/chat", {
        method: "POST",
        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage,
          language,
        }),
      });
      setSessionId(res.data.session_id);
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.reply }]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#f7f5f0] flex flex-col">
      <header className="bg-[#2d4a2b] text-white px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">Kisan Dost AI</h1>
        <div className="flex items-center gap-4">
          <div className="flex bg-white/10 rounded-lg overflow-hidden text-sm">
            <button
              onClick={() => setLanguage("en")}
              className={`px-3 py-1 ${language === "en" ? "bg-white text-[#2d4a2b] font-medium" : ""}`}
            >
              EN
            </button>
            <button
              onClick={() => setLanguage("ur")}
              className={`px-3 py-1 ${language === "ur" ? "bg-white text-[#2d4a2b] font-medium" : ""}`}
            >
              اردو
            </button>
          </div>
          <Link href="/dashboard" className="text-sm opacity-90 hover:opacity-100">
            ← Back
          </Link>
        </div>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-6 flex flex-col">
        <div className="flex-1 space-y-4 mb-4">
          {messages.length === 0 && (
            <p className="text-center text-gray-400 text-sm mt-10">
              Ask me anything about your crops, diseases, fertilizers, or irrigation.
            </p>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                dir={language === "ur" ? "rtl" : "ltr"}
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-[#2d4a2b] text-white"
                    : "bg-white border border-gray-200 text-gray-800"
                }`}
              >
                <span dangerouslySetInnerHTML={renderMarkdown(msg.content)} />
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-2xl px-4 py-2.5 text-sm text-gray-400">
                Typing...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="flex gap-2 sticky bottom-4">
          <input
            dir={language === "ur" ? "rtl" : "ltr"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={language === "ur" ? "اپنا سوال لکھیں..." : "Ask a question..."}
            className="flex-1 px-4 py-2.5 rounded-full border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-[#2d4a2b]"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-[#2d4a2b] text-white px-5 py-2.5 rounded-full font-medium hover:bg-[#1f3520] transition disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </main>
    </div>
  );
}