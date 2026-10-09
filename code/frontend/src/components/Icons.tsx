import type { ReactNode } from 'react';

function Icon({ size = 20, sw = 2, children }: { size?: number; sw?: number; children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={sw}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

type P = { size?: number };

export const PanelIcon = ({ size }: P) => (
  <Icon size={size}>
    <rect x="3" y="4" width="18" height="16" rx="3" />
    <path d="M9 4v16" />
  </Icon>
);
export const PlusIcon = ({ size }: P) => (
  <Icon size={size} sw={2.2}>
    <path d="M12 5v14M5 12h14" />
  </Icon>
);
export const MenuIcon = ({ size }: P) => (
  <Icon size={size}>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </Icon>
);
export const ChatIcon = ({ size = 18 }: P) => (
  <Icon size={size}>
    <path d="M5 6h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-8l-5 4v-4H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z" />
  </Icon>
);
export const UserIcon = ({ size }: P) => (
  <Icon size={size}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
  </Icon>
);
export const LogoutIcon = ({ size }: P) => (
  <Icon size={size}>
    <path d="M9 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3M16 8l4 4-4 4M20 12H9" />
  </Icon>
);
export const SearchIcon = ({ size }: P) => (
  <Icon size={size}>
    <circle cx="11" cy="11" r="7" />
    <path d="M20 20l-4-4" />
  </Icon>
);
export const SendIcon = ({ size }: P) => (
  <Icon size={size} sw={2.6}>
    <path d="M12 19V5M5 12l7-7 7 7" />
  </Icon>
);
export const ExternalIcon = ({ size = 16 }: P) => (
  <Icon size={size}>
    <path d="M14 4h6v6M20 4l-9 9M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4" />
  </Icon>
);
export const AlertIcon = ({ size = 18 }: P) => (
  <Icon size={size}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v5M12 16.5v.01" />
  </Icon>
);
export const CheckIcon = ({ size = 18 }: P) => (
  <Icon size={size} sw={2.4}>
    <path d="M5 12.5l4.5 4.5L19 7.5" />
  </Icon>
);
export const CrossIcon = ({ size = 18 }: P) => (
  <Icon size={size} sw={2.4}>
    <path d="M6 6l12 12M18 6L6 18" />
  </Icon>
);
export const SpinnerIcon = ({ size = 18 }: P) => (
  <svg className="spin" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" aria-hidden="true">
    <path d="M12 3a9 9 0 0 1 9 9" />
  </svg>
);
