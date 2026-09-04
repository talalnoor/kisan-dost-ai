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
  const [listening, setListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (!getToken()) router.push("/login");
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      setVoiceSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setListening(false);
      };
      recognition.onerror = () => setListening(false);
      recognition.onend = () => setListening(false);
      recognitionRef.current = recognition;
    }
  }, []);

  useEffect(() => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = language === "ur" ? "ur-PK" : "en-US";
    }
  }, [language]);

  function toggleListening() {
    if (!recognitionRef.current) return;
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      recognitionRef.current.start();
      setListening(true);
    }
  }

  function speak(text: string) {
    if (!("speechSynthesis" in window)) return;
    const plain = text.replace(/\*\*/g, "").replace(/\n/g, " ");
    const utterance = new SpeechSynthesisUtterance(plain);
    utterance.lang = language === "ur" ? "ur-PK" : "en-US";
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

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
      speak(res.data.reply);
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
    <div className="min-h-screen bg-gradient-to-b from-[#f8f6f0] to-[#eef0e5] flex flex-col">
      <header className="bg-[#1f3d1a] text-white px-6 py-4 flex items-center justify-between shadow-sm">
        <h1 className="font-heading text-xl font-bold flex items-center gap-2">🌾 Kisan Dost AI</h1>
        <div className="flex items-center gap-4">
          <div className="flex bg-white/10 rounded-full overflow-hidden text-sm p-0.5">
            <button
              onClick={() => setLanguage("en")}
              className={`px-3 py-1 rounded-full transition ${language === "en" ? "bg-white text-[#1f3d1a] font-semibold" : ""}`}
            >
              EN
            </button>
            <button
              onClick={() => setLanguage("ur")}
              className={`px-3 py-1 rounded-full transition ${language === "ur" ? "bg-white text-[#1f3d1a] font-semibold" : ""}`}
            >
              اردو
            </button>
          </div>
          <Link href="/dashboard" className="text-sm opacity-90 hover:opacity-100 transition">
            ← Back
          </Link>
        </div>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-6 flex flex-col">
        <div className="flex-1 space-y-4 mb-4">
          {messages.length === 0 && (
            <div className="text-center mt-16">
              <div className="text-4xl mb-3">💬</div>
              <p className="text-gray-400 text-sm">
                Ask me anything about your crops, diseases, fertilizers, or irrigation.
                {voiceSupported && " Tap the mic to speak."}
              </p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                dir={language === "ur" ? "rtl" : "ltr"}
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm shadow-sm ${
                  msg.role === "user"
                    ? "bg-[#1f3d1a] text-white"
                    : "bg-white border border-black/5 text-gray-800"
                }`}
              >
                <span dangerouslySetInnerHTML={renderMarkdown(msg.content)} />
                {msg.role === "assistant" && (
                  <button
                    onClick={() => speak(msg.content)}
                    className="ml-2 text-gray-400 hover:text-[#1f3d1a] align-middle"
                    title="Read aloud"
                  >
                    🔊
                  </button>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-black/5 rounded-2xl px-4 py-2.5 text-sm text-gray-400 shadow-sm">
                Typing...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="flex gap-2 sticky bottom-4">
          {voiceSupported && (
            <button
              onClick={toggleListening}
              className={`px-4 py-2.5 rounded-full font-semibold shadow-sm transition ${
                listening ? "bg-red-600 text-white animate-pulse" : "bg-white border border-gray-300 text-[#1f3d1a]"
              }`}
              title="Speak your question"
            >
              🎤
            </button>
          )}
          <input
            dir={language === "ur" ? "rtl" : "ltr"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder={language === "ur" ? "اپنا سوال لکھیں یا بولیں..." : "Ask or speak a question..."}
            className="flex-1 px-4 py-2.5 rounded-full border border-gray-300 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-[#1f3d1a]/40 transition"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-[#1f3d1a] text-white px-5 py-2.5 rounded-full font-semibold hover:bg-[#2d5527] transition disabled:opacity-50 shadow-sm"
          >
            Send
          </button>
        </div>
      </main>
    </div>
  );
}