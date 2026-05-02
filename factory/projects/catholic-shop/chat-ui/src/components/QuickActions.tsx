import { useRef, useEffect, useState } from 'react';
import { useChatStore } from '../store';
import { OCCASION_LABELS, type Occasion } from '../types';
import { Icon } from './Icon';

const QUICK_OCCASIONS: Occasion[] = [
  'baptism', 'first_communion', 'confirmation', 'wedding',
  'healing', 'mourning', 'home_blessing', 'just_browsing',
];

export function QuickActions() {
  const { selectedOccasion, setSelectedOccasion } = useChatStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [overflow, setOverflow] = useState<'none' | 'left' | 'both' | 'right'>('none');

  const checkOverflow = () => {
    const el = scrollRef.current;
    if (!el) return;
    const sl = el.scrollLeft;
    const max = el.scrollWidth - el.clientWidth;
    if (max <= 1) { setOverflow('none'); return; }
    if (sl < 2) { setOverflow('right'); return; }
    if (sl > max - 2) { setOverflow('left'); return; }
    setOverflow('both');
  };

  useEffect(() => {
    checkOverflow();
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener('scroll', checkOverflow, { passive: true });
    const ro = new ResizeObserver(checkOverflow);
    ro.observe(el);
    return () => {
      el.removeEventListener('scroll', checkOverflow);
      ro.disconnect();
    };
  }, []);

  const scroll = (dir: 'left' | 'right') => {
    scrollRef.current?.scrollBy({ left: dir === 'left' ? -160 : 160, behavior: 'smooth' });
  };

  const showLeft = overflow === 'left' || overflow === 'both';
  const showRight = overflow === 'right' || overflow === 'both';

  return (
    <div className="shrink-0 relative h-10 flex items-center border-b border-ink-100 bg-parchment-50">
      {/* Left fade + button */}
      <div
        className={`absolute left-0 top-0 bottom-0 w-9 z-10 bg-gradient-to-r from-parchment-50 to-transparent
          flex items-center pl-1 transition-opacity duration-200 ${showLeft ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
      >
        <button onClick={() => scroll('left')} className="p-1">
          <Icon name="chevronLeft" size={13} className="text-ink-400" />
        </button>
      </div>

      {/* Scrollable chip row */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-x-auto custom-scrollbar scroll-smooth overscroll-contain px-4"
      >
        <div className="flex gap-1.5 min-w-max items-center h-10">
          {QUICK_OCCASIONS.map((occ) => {
            const { label, icon } = OCCASION_LABELS[occ];
            const active = selectedOccasion === occ;
            return (
              <button
                key={occ}
                onClick={() => setSelectedOccasion(active ? null : occ)}
                className={`inline-flex items-center gap-1 px-2.5 py-1 text-[12px] rounded-full
                  whitespace-nowrap transition-colors duration-200 font-body shrink-0
                  ${active
                    ? 'bg-gold-100 text-gold-800 border border-gold-300'
                    : 'text-ink-500 active:bg-ink-100 border border-transparent'
                  }`}
              >
                <Icon name={icon as any} size={12} />
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Right fade + button */}
      <div
        className={`absolute right-0 top-0 bottom-0 w-9 z-10 bg-gradient-to-l from-parchment-50 to-transparent
          flex items-center justify-end pr-1 transition-opacity duration-200 ${showRight ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
      >
        <button onClick={() => scroll('right')} className="p-1">
          <Icon name="chevronRight" size={13} className="text-ink-400" />
        </button>
      </div>
    </div>
  );
}
