import { Map as MapIcon } from "lucide-react";
import { Link, useLocation } from "react-router";

const NAV = [
  { to: "/", label: "地図" },
  { to: "/elements", label: "地名要素辞典" },
  { to: "/sources", label: "出典" },
  { to: "/about", label: "この地図について" },
];

type Props = {
  builtAt?: string | null;
};

export function SiteHeader(props: Props) {
  const { pathname } = useLocation();

  return (
    <header className="flex h-11 shrink-0 items-center gap-3 border-b border-border bg-sidebar px-3">
      <Link to="/" className="flex items-center gap-1.5 whitespace-nowrap">
        <MapIcon className="size-4 text-primary" />
        <span className="text-sm font-semibold">警鐘地名マップ</span>
      </Link>
      <nav className="flex min-w-0 items-center gap-1 overflow-x-auto">
        {NAV.map((item) => {
          const active =
            item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
          return (
            <Link
              key={item.to}
              to={item.to}
              className={[
                "rounded-md px-2 py-1 text-xs whitespace-nowrap transition-colors",
                active
                  ? "bg-accent font-medium text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/60",
              ].join(" ")}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      {props.builtAt ? (
        <span className="ml-auto hidden shrink-0 text-[10px] text-muted-foreground sm:block">
          データ生成 {props.builtAt.slice(0, 10)}
        </span>
      ) : null}
    </header>
  );
}
