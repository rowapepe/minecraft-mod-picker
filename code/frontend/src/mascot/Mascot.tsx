import type { Rect } from './costumes';
import { MASCOT_NAME, SKELETON, THINKING_SAY, ZOMBIE_BODY, type Costume } from './costumes';

function Pixels({ rects, width, height, className }: { rects: Rect[]; width: number; height: number; className?: string }) {
  return (
    <svg className={className} viewBox={`0 0 ${width} ${height}`} shapeRendering="crispEdges" aria-hidden="true">
      {rects.map(([x, y, w, h, fill, opacity], i) => (
        <rect key={i} x={x} y={y} width={w} height={h} fill={fill} opacity={opacity} />
      ))}
    </svg>
  );
}

/** Зомби с костюмом. `key` на слое костюма заново запускает анимацию «падения» при смене. */
export function Zombie({ costume, thinking = false, className = '' }: { costume: Costume; thinking?: boolean; className?: string }) {
  return (
    <div className={`zwrap ${thinking ? 'think' : ''} ${className}`} aria-hidden="true">
      <div className="zsvg">
        <Pixels className="layer" rects={ZOMBIE_BODY} width={24} height={33} />
        {costume.rects.length > 0 && <Pixels key={costume.id} className="layer costume" rects={costume.rects} width={24} height={33} />}
      </div>
    </div>
  );
}

/** Зомби над формой запроса: имя, реплика в рамке и сам талисман (RULE-MASCOT-01…05). */
export function MascotRow({ costume, thinking }: { costume: Costume; thinking: boolean }) {
  return (
    <div className="mascot-row">
      <div className="bubble">
        <span className="bubble-name">{MASCOT_NAME}</span>
        <span className="bubble-say">{thinking ? THINKING_SAY : costume.say}</span>
      </div>
      <Zombie costume={costume} thinking={thinking} />
    </div>
  );
}

/** Поверженный скелет для пустого списка запросов (RULE-UI-09), без анимации. */
export function FallenSkeleton() {
  return (
    <div className="skeleton-empty">
      <svg className="skeleton-img" viewBox="0 0 40 16" shapeRendering="crispEdges" role="img" aria-label="Поверженный скелет">
        {SKELETON.map(([x, y, w, h, fill, opacity], i) => (
          <rect key={i} x={x} y={y} width={w} height={h} fill={fill} opacity={opacity} />
        ))}
      </svg>
      <span className="skeleton-caption">Нет чатов</span>
    </div>
  );
}
