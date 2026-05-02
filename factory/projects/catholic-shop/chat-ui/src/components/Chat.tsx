import { useEffect, useRef, useState, useCallback } from 'react';
import { useChatStore, useAuthStore, useCartStore } from '../store';
import { ProductCard } from './ProductCard';
import { QuickActions } from './QuickActions';
import { ConversationList } from './ConversationList';
import { CartDrawer } from './CartDrawer';
import { Icon } from './Icon';
import type { Message, Product, Occasion, Conversation } from '../types';

const API_BASE = '/catholic-shop';

const WELCOME_SUGGESTIONS: { label: string; occasion: Occasion; prompt: string; icon: string }[] = [
  { label: 'Baptism',      occasion: 'baptism',         prompt: "I'm looking for a baptism gift",       icon: 'baptism' },
  { label: 'Wedding',      occasion: 'wedding',         prompt: "I'm looking for a wedding gift",       icon: 'wedding' },
  { label: 'Healing',      occasion: 'healing',         prompt: "I'm looking for a healing gift",       icon: 'healing' },
  { label: 'Communion',    occasion: 'first_communion', prompt: "I'm looking for a first communion gift", icon: 'first_communion' },
];

export function Chat() {
  const [input, setInput] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [cartOpen, setCartOpen] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const userScrolledUp = useRef(false);

  const {
    conversations,
    activeConversationId,
    isStreaming,
    createConversation,
    addMessage,
    updateLastAssistantMessage,
    setStreaming,
  } = useChatStore();

  const { isAuthenticated } = useAuthStore();
  const cart = useCartStore();

  const activeConversation = conversations.find((c) => c.id === activeConversationId);
  const messages = activeConversation?.messages ?? [];

  // ── Close panels with Escape ──────────────────────
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (cartOpen) setCartOpen(false);
        else if (sidebarOpen) setSidebarOpen(false);
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [cartOpen, sidebarOpen]);

  // ── Scroll management ─────────────────────────────
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const onScroll = () => {
      const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
      userScrolledUp.current = !nearBottom;
    };
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  // Auto-scroll during streaming (only if user hasn't scrolled up)
  useEffect(() => {
    if (!isStreaming) return;
    const el = scrollRef.current;
    if (!el || userScrolledUp.current) return;

    // Use requestAnimationFrame to batch scrolls
    const raf = requestAnimationFrame(() => {
      el.scrollTo({ top: el.scrollHeight, behavior: 'instant' });
    });
    return () => cancelAnimationFrame(raf);
  }, [messages, isStreaming]);

  // ── Focus input after streaming ───────────────────
  useEffect(() => {
    if (!isStreaming && inputRef.current) {
      // Delay focus to avoid keyboard-jank during transition
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isStreaming]);

  // ── Load conversations from backend on mount ──────
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/chat/conversations`);
        if (!res.ok) return;
        const data = await res.json();
        const raw = data.conversations || [];
        if (raw.length === 0) {
          createConversation();
          return;
        }
        const mapped: Conversation[] = raw.map((c: any) => ({
          id: c.id,
          title: c.title || 'Pilgrimage',
          messages: (c.messages || []).map((m: any, i: number) => ({
            id: m.id || `msg_${c.id}_${i}`,
            role: m.role,
            content: m.content || '',
            timestamp: typeof m.timestamp === 'string'
              ? new Date(m.timestamp).getTime()
              : m.timestamp || Date.now(),
          })),
          createdAt: typeof c.created_at === 'string'
            ? new Date(c.created_at).getTime()
            : c.created_at || Date.now(),
          updatedAt: typeof c.updated_at === 'string'
            ? new Date(c.updated_at).getTime()
            : c.updated_at || Date.now(),
          productCount: c.product_count || 0,
        }));
        useChatStore.getState().loadConversations(mapped);
        useChatStore.getState().setActiveConversation(mapped[0].id);
      } catch {
        createConversation();
      }
    };
    fetchConversations();
  }, []);

  // ── Send message ──────────────────────────────────
  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || isStreaming || !activeConversationId) return;

    setInput('');
    userScrolledUp.current = false;

    const userMsg: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };
    addMessage(activeConversationId, userMsg);
    setStreaming(true);

    const assistantMsgId = `msg_${Date.now() + 1}`;
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    };
    addMessage(activeConversationId, assistantMsg);

    abortRef.current = new AbortController();

    try {
      const context = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const response = await fetch(`${API_BASE}/api/v1/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(isAuthenticated
            ? { Authorization: `Bearer ${useAuthStore.getState().token}` }
            : {}),
        },
        body: JSON.stringify({
          conversation_id: activeConversationId,
          message: text,
          context,
          occasion: useChatStore.getState().selectedOccasion,
        }),
        signal: abortRef.current.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No stream');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;
            try {
              const parsed = JSON.parse(data);
              if (parsed.type === 'text') {
                updateLastAssistantMessage(activeConversationId, parsed.content);
              } else if (parsed.type === 'product_cards') {
                updateLastAssistantMessage(
                  activeConversationId,
                  '',
                  parsed.products as Product[]
                );
              } else if (parsed.type === 'error') {
                updateLastAssistantMessage(
                  activeConversationId,
                  `\n\n*Forgive me, pilgrim — I encountered a difficulty. ${parsed.message}*`
                );
              }
            } catch {}
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        updateLastAssistantMessage(activeConversationId, ' *(journey paused)*');
      } else {
        const msg = err instanceof Error ? err.message : 'Unknown error';
        updateLastAssistantMessage(activeConversationId, `\n\n*Forgive me — ${msg}. Shall we try again?*`);
      }
    } finally {
      setStreaming(false);
      abortRef.current = null;
    }
  }, [input, isStreaming, activeConversationId, messages, isAuthenticated]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (prompt: string) => {
    setInput(prompt);
    inputRef.current?.focus();
  };

  // ── Layout classes ─────────────────────────────────
  // dvh = dynamic viewport height (handles Safari toolbar)
  // flex layout ensures input stays pinned at bottom,
  // scroll area fills the gap
  return (
    <div className="h-dvh flex flex-col overflow-hidden bg-parchment-50">
      {/* Header — fixed height */}
      <header className="shrink-0 flex items-center justify-between px-4 py-2.5 border-b border-ink-100">
        <button
          onClick={() => setSidebarOpen(true)}
          className="flex items-center gap-1.5 text-ink-500 hover:text-ink-800 transition-colors"
        >
          <Icon name="menu" size={18} />
          <span className="text-sm font-display tracking-wide">Journeys</span>
        </button>

        <h1 className="font-display text-base text-ink-700 tracking-wider">
          Pilgrimage Concierge
        </h1>

        <button
          onClick={() => setCartOpen(true)}
          className="relative text-ink-500 hover:text-ink-800 transition-colors"
        >
          <Icon name="cart" size={20} />
          {cart.items.length > 0 && (
            <span className="absolute -top-1.5 -right-1.5 bg-gold-600 text-parchment-50 text-[10px] rounded-full w-4 h-4 flex items-center justify-center font-sans font-medium">
              {cart.items.length}
            </span>
          )}
        </button>
      </header>

      {/* Occasion chips — fixed height, no reflow */}
      <QuickActions />

      {/* Messages area — flex-1 fills remaining space */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto overflow-x-hidden overscroll-contain custom-scrollbar"
        style={{ WebkitOverflowScrolling: 'touch' }}
      >
        {!activeConversationId || messages.length === 0 ? (
          /* Welcome */
          <div className="px-5 py-10 max-w-lg mx-auto">
            <Icon name="cross" size={28} className="text-gold-500 mb-4" />
            <h2 className="font-display text-xl text-ink-800 mb-2">
              Welcome, Pilgrim
            </h2>
            <p className="font-body text-ink-600 leading-relaxed text-[15px] max-w-sm">
              I am your guide across the sacred sites of Christendom. Tell me what
              brings you here, and I will help you find something truly blessed.
            </p>
            <div className="mt-6 flex flex-wrap gap-2">
              {WELCOME_SUGGESTIONS.map((s) => (
                <button
                  key={s.occasion}
                  onClick={() => handleSuggestionClick(s.prompt)}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 text-sm border border-ink-200
                             text-ink-600 active:bg-gold-50 active:border-gold-300
                             rounded-full transition-colors duration-200 font-body"
                >
                  <Icon name={s.icon as any} size={14} />
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Messages — no bubbles, stable word-wrap */
          <div className="px-4 py-4 max-w-2xl mx-auto space-y-5">
            {messages.map((msg) => (
              <div key={msg.id} className={msg.role === 'user' ? 'flex justify-end' : 'flex'}>
                <div className={msg.role === 'user' ? 'max-w-[80%]' : 'max-w-full'}>
                  {msg.role === 'user' && msg.content && (
                    <p className="font-body font-medium text-[15px] text-ink-800 leading-relaxed
                                  break-words whitespace-pre-wrap text-right">
                      {msg.content}
                    </p>
                  )}

                  {msg.role === 'assistant' && (
                    <div className="pl-3 border-l-2 border-gold-200">
                      {msg.content && (
                        <p className="font-body text-[15px] text-ink-700 leading-relaxed
                                      break-words whitespace-pre-wrap">
                          {msg.content}
                        </p>
                      )}
                      {msg.productCards && msg.productCards.length > 0 && (
                        <div className="mt-3 grid gap-3 grid-cols-1 sm:grid-cols-2">
                          {msg.productCards.map((product) => (
                            <ProductCard key={product.id} product={product} />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Streaming indicator */}
            {isStreaming && (
              <div className="pl-3 border-l-2 border-gold-200">
                <div className="flex items-center gap-1.5 h-5">
                  <span className="w-1.5 h-1.5 bg-gold-400 rounded-full animate-pulse" />
                  <span className="w-1.5 h-1.5 bg-gold-400 rounded-full animate-pulse"
                        style={{ animationDelay: '200ms' }} />
                  <span className="w-1.5 h-1.5 bg-gold-400 rounded-full animate-pulse"
                        style={{ animationDelay: '400ms' }} />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input — pinned at bottom, shrink-0 prevents squish */}
      <div className="shrink-0 px-3 pb-3 pt-2 border-t border-ink-100 bg-parchment-50">
        <div className="max-w-2xl mx-auto flex gap-2 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Share your intention..."
            className="scriptorium-input flex-1 resize-none min-h-[42px] max-h-[100px]"
            rows={1}
            disabled={isStreaming}
          />
          <button
            onClick={sendMessage}
            disabled={isStreaming || !input.trim()}
            className="scriptorium-button-gold shrink-0 !py-2 !px-3.5 disabled:opacity-30
                       disabled:cursor-not-allowed flex items-center gap-1.5 text-sm"
          >
            <Icon name="send" size={14} />
            Send
          </button>
        </div>
      </div>

      {/* Panels */}
      {sidebarOpen && <ConversationList onClose={() => setSidebarOpen(false)} />}
      {cartOpen && <CartDrawer onClose={() => setCartOpen(false)} />}
    </div>
  );
}
