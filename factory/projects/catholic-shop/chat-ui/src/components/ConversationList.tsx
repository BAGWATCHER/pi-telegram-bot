import { useChatStore } from '../store';
import { Icon } from './Icon';

interface Props {
  onClose: () => void;
}

export function ConversationList({ onClose }: Props) {
  const { conversations, activeConversationId, setActiveConversation, createConversation } =
    useChatStore();

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-80 max-w-[85vw] h-full bg-parchment-50 border-r border-ink-200/30 shadow-2xl flex flex-col">
        <div className="p-4 border-b border-ink-100 flex items-center justify-between">
          <h2 className="font-display text-base text-ink-800">Your Journeys</h2>
          <button onClick={onClose} className="text-ink-400 hover:text-ink-800 transition-colors">
            <Icon name="cross" size={18} />
          </button>
        </div>

        <div className="p-3 border-b border-ink-100">
          <button
            onClick={() => { createConversation(); onClose(); }}
            className="w-full scriptorium-button-gold text-sm py-2"
          >
            New Pilgrimage
          </button>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {conversations.length === 0 ? (
            <div className="p-6 text-center text-ink-400 font-body text-sm">
              No journeys yet.
            </div>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => { setActiveConversation(conv.id); onClose(); }}
                className={`w-full text-left p-3.5 border-b border-ink-100 hover:bg-parchment-50 transition-colors ${
                  conv.id === activeConversationId
                    ? 'bg-gold-50/70 border-l-[3px] border-l-gold-400'
                    : 'border-l-[3px] border-l-transparent'
                }`}
              >
                <p className="font-body text-[13px] text-ink-800 truncate font-medium">
                  {conv.title}
                </p>
                <p className="text-[11px] text-ink-400 mt-0.5">
                  {new Date(conv.updatedAt).toLocaleDateString('en-US', {
                    month: 'short', day: 'numeric',
                  })}
                  {conv.productCount > 0 && (
                    <span className="ml-2 text-gold-600">
                      · {conv.productCount} treasure{conv.productCount !== 1 ? 's' : ''}
                    </span>
                  )}
                </p>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
