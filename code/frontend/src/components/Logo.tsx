export function LogoMark({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 8 8" shapeRendering="crispEdges" aria-hidden="true">
      <rect width="8" height="8" rx="1.6" fill="var(--accent)" />
      <rect x="1" y="1" width="2" height="1" fill="#052b14" opacity=".4" />
      <rect x="5" y="2" width="2" height="2" fill="#052b14" opacity=".4" />
      <rect x="2" y="5" width="2" height="2" fill="#052b14" opacity=".4" />
      <rect x="5" y="5" width="1" height="1" fill="#052b14" opacity=".4" />
    </svg>
  );
}

/** Аватарка ответа системы: зелёная плашка с «лицом». */
export function AnswerAvatar() {
  return (
    <div className="avatar">
      <svg width="20" height="20" viewBox="0 0 8 8" shapeRendering="crispEdges" aria-hidden="true">
        <rect x="1" y="1" width="2" height="2" fill="#052b14" />
        <rect x="5" y="2" width="2" height="2" fill="#052b14" />
        <rect x="2" y="5" width="3" height="2" fill="#052b14" />
      </svg>
    </div>
  );
}
