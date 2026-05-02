import { useCartStore, useAuthStore } from '../store';
import { Icon } from './Icon';

interface Props {
  onClose: () => void;
}

const API_BASE = '/catholic-shop';

export function CartDrawer({ onClose }: Props) {
  const { items, removeItem, updateQuantity, totalPrice, clearCart } = useCartStore();
  const { isAuthenticated, token } = useAuthStore();

  const handleCheckout = async () => {
    if (items.length === 0) return;
    try {
      const response = await fetch(`${API_BASE}/api/v1/chat/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(isAuthenticated ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          items: items.map((i) => ({
            product_id: i.productId,
            quantity: i.quantity,
          })),
        }),
      });

      if (!response.ok) throw new Error('Checkout failed');
      const data = await response.json();

      if (data.stripe_checkout_url) {
        window.open(data.stripe_checkout_url, '_blank');
      }
    } catch {
      alert('Unable to begin checkout. Please try again, pilgrim.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <div className="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-96 max-w-[90vw] h-full bg-parchment-50 border-l border-ink-200/30 shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-ink-100 flex items-center justify-between">
          <h2 className="font-display text-base text-ink-800 flex items-center gap-2">
            <Icon name="cart" size={18} />
            Your Treasures ({items.length})
          </h2>
          <button onClick={onClose} className="text-ink-400 hover:text-ink-800 transition-colors">
            <Icon name="cross" size={18} />
          </button>
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {items.length === 0 ? (
            <div className="p-8 text-center">
              <Icon name="cross" size={32} className="text-ink-200 mx-auto mb-3" />
              <p className="font-body text-ink-500 text-sm">
                Your treasure chest is empty, pilgrim.
              </p>
            </div>
          ) : (
            items.map((item) => (
              <div
                key={item.productId}
                className="p-3 border-b border-ink-100 flex gap-3"
              >
                <img
                  src={item.product.imageUrl}
                  alt={item.product.name}
                  className="w-14 h-14 rounded object-cover shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <p className="font-body text-sm text-ink-800 font-medium truncate">
                    {item.product.name}
                  </p>
                  <p className="text-xs text-ink-400">
                    {item.product.destination} · ${item.product.price}
                  </p>
                  <div className="flex items-center gap-1.5 mt-1">
                    <button
                      onClick={() => updateQuantity(item.productId, item.quantity - 1)}
                      className="w-5 h-5 rounded border border-ink-200 text-ink-500 text-xs flex items-center justify-center hover:bg-ink-50"
                    >
                      −
                    </button>
                    <span className="text-xs text-ink-700 w-4 text-center tabular-nums">
                      {item.quantity}
                    </span>
                    <button
                      onClick={() => updateQuantity(item.productId, item.quantity + 1)}
                      className="w-5 h-5 rounded border border-ink-200 text-ink-500 text-xs flex items-center justify-center hover:bg-ink-50"
                    >
                      +
                    </button>
                  </div>
                </div>
                <button
                  onClick={() => removeItem(item.productId)}
                  className="text-ink-300 hover:text-red-500 transition-colors shrink-0"
                >
                  <Icon name="cross" size={14} />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className="p-4 border-t border-ink-100 bg-parchment-50">
            <div className="flex items-center justify-between mb-3">
              <span className="font-display text-sm text-ink-600">Total</span>
              <span className="font-display text-lg text-gold-700">
                ${totalPrice().toFixed(2)}
              </span>
            </div>
            <button
              onClick={handleCheckout}
              className="w-full scriptorium-button-gold text-sm py-2.5"
            >
              Proceed to Offering
            </button>
            <button
              onClick={clearCart}
              className="w-full mt-2 text-xs text-ink-400 hover:text-red-600 transition-colors font-body"
            >
              Clear all
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
