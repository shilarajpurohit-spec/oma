import { useState, useRef, useEffect } from "react";
import { api } from "../api";
import { Send, Loader2, Bot, User, Trash2 } from "lucide-react";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatInterfaceProps {
  context?: Record<string, any>;
}

export function ChatInterface({ context }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = { role: "user", content: input };
    const newHistory = [...messages, userMessage];
    setMessages(newHistory);
    setInput("");
    setIsLoading(true);

    try {
      const contextStr = context ? JSON.stringify(context) : undefined;
      const response = await api.chat({
        message: input,
        context: contextStr,
      });
      setMessages([...newHistory, { role: "assistant", content: response.reply }]);
    } catch (err) {
      console.error(err);
      setMessages([
        ...newHistory,
        { role: "assistant", content: "Sorry, I encountered an error. Please try again." }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => setMessages([]);

  return (
    <div className="flex flex-col h-full bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden shadow-xl">
      <div className="flex items-center justify-between px-4 py-3 bg-neutral-800 border-b border-neutral-700">
        <h2 className="text-lg font-semibold text-neutral-100 flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-400" />
          Migration Assistant
        </h2>
        <button 
          onClick={clearChat}
          className="text-neutral-400 hover:text-red-400 transition-colors p-1"
          title="Clear chat"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-neutral-500 space-y-3">
            <Bot className="w-12 h-12 opacity-50" />
            <p>Ask me about the migration or code issues.</p>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === "assistant" ? "items-start" : "items-start flex-row-reverse"}`}>
            <div className={`p-2 rounded-full flex-shrink-0 ${msg.role === "assistant" ? "bg-blue-500/20 text-blue-400" : "bg-emerald-500/20 text-emerald-400"}`}>
              {msg.role === "assistant" ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
            </div>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 ${
              msg.role === "assistant" 
                ? "bg-neutral-800 text-neutral-200 rounded-tl-sm border border-neutral-700" 
                : "bg-blue-600 text-white rounded-tr-sm"
            }`}>
              {/* Replace with markdown renderer later if needed */}
              <div className="whitespace-pre-wrap text-sm leading-relaxed font-sans">{msg.content}</div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 items-start">
            <div className="p-2 rounded-full bg-blue-500/20 text-blue-400">
              <Bot className="w-5 h-5" />
            </div>
            <div className="bg-neutral-800 border border-neutral-700 text-neutral-200 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
               <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></span>
               <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
               <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
            </div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      <div className="p-3 bg-neutral-800 border-t border-neutral-700">
        <form 
          className="flex items-center gap-2"
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
        >
          <input
            type="text"
            className="flex-1 bg-neutral-900 border border-neutral-700 text-neutral-100 rounded-full px-4 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white p-2 rounded-full transition-colors flex-shrink-0"
          >
             {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </form>
      </div>
    </div>
  );
}
