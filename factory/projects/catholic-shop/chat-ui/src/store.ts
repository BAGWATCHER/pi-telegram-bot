import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { CartItem, Conversation, Message, Product, User, Occasion } from './types';

// ── Auth Store ──────────────────────────────────────────
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  updatePreferences: (prefs: User['preferences']) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  login: (user, token) => {
    localStorage.setItem('catholic-chat-token', token);
    localStorage.setItem('catholic-chat-user', JSON.stringify(user));
    set({ user, token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('catholic-chat-token');
    localStorage.removeItem('catholic-chat-user');
    set({ user: null, token: null, isAuthenticated: false });
  },
  updatePreferences: (prefs) =>
    set((s) => ({
      user: s.user ? { ...s.user, preferences: { ...s.user.preferences, ...prefs } } : null,
    })),
}));

// ── Chat Store ──────────────────────────────────────────
interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
  isStreaming: boolean;
  selectedOccasion: Occasion | null;

  setActiveConversation: (id: string) => void;
  createConversation: () => string;
  addMessage: (conversationId: string, message: Message) => void;
  updateLastAssistantMessage: (conversationId: string, content: string, products?: Product[]) => void;
  setStreaming: (value: boolean) => void;
  setSelectedOccasion: (occasion: Occasion | null) => void;
  loadConversations: (conversations: Conversation[]) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  activeConversationId: null,
  isStreaming: false,
  selectedOccasion: null,

  setActiveConversation: (id) => set({ activeConversationId: id }),

  createConversation: () => {
    const id = `conv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const conv: Conversation = {
      id,
      title: 'New Pilgrimage',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      productCount: 0,
    };
    set((s) => ({
      conversations: [conv, ...s.conversations],
      activeConversationId: id,
    }));
    return id;
  },

  addMessage: (conversationId, message) =>
    set((s) => {
      const conversations = s.conversations.map((c) => {
        if (c.id !== conversationId) return c;
        return {
          ...c,
          messages: [...c.messages, message],
          updatedAt: Date.now(),
          productCount: c.productCount + (message.productCards?.length ?? 0),
          // Set title from first user message
          title: c.messages.length === 0 && message.role === 'user'
            ? message.content.slice(0, 60)
            : c.title,
        };
      });
      return { conversations };
    }),

  updateLastAssistantMessage: (conversationId, content, products) =>
    set((s) => {
      const conversations = s.conversations.map((c) => {
        if (c.id !== conversationId) return c;
        const messages = [...c.messages];
        const lastMsg = messages[messages.length - 1];
        if (lastMsg && lastMsg.role === 'assistant') {
          messages[messages.length - 1] = {
            ...lastMsg,
            content: lastMsg.content + content,
            productCards: products ?? lastMsg.productCards,
          };
        }
        return { ...c, messages, updatedAt: Date.now() };
      });
      return { conversations };
    }),

  setStreaming: (value) => set({ isStreaming: value }),
  setSelectedOccasion: (occasion) => set({ selectedOccasion: occasion }),

  loadConversations: (conversations) => set({ conversations }),
}));

// ── Cart Store ──────────────────────────────────────────
interface CartState {
  items: CartItem[];
  addItem: (product: Product, conversationId?: string) => void;
  removeItem: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
  totalItems: () => number;
  totalPrice: () => number;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
  items: [],

  addItem: (product, conversationId) =>
    set((s) => {
      const existing = s.items.find((i) => i.productId === product.id);
      if (existing) {
        return {
          items: s.items.map((i) =>
            i.productId === product.id ? { ...i, quantity: i.quantity + 1 } : i
          ),
        };
      }
      return {
        items: [
          ...s.items,
          { productId: product.id, product, quantity: 1, addedFromConversationId: conversationId },
        ],
      };
    }),

  removeItem: (productId) =>
    set((s) => ({ items: s.items.filter((i) => i.productId !== productId) })),

  updateQuantity: (productId, quantity) =>
    set((s) => ({
      items: quantity <= 0
        ? s.items.filter((i) => i.productId !== productId)
        : s.items.map((i) => (i.productId === productId ? { ...i, quantity } : i)),
    })),

  clearCart: () => set({ items: [] }),

  totalItems: () => get().items.reduce((sum, i) => sum + i.quantity, 0),
  totalPrice: () => get().items.reduce((sum, i) => sum + i.product.price * i.quantity, 0),
    }),
    { name: 'catholic-chat-cart' }
  )
);

// ── Init from localStorage ─────────────────────────────
const savedToken = localStorage.getItem('catholic-chat-token');
const savedUser = localStorage.getItem('catholic-chat-user');
if (savedToken && savedUser) {
  try {
    useAuthStore.setState({ user: JSON.parse(savedUser), token: savedToken, isAuthenticated: true });
  } catch {}
}
