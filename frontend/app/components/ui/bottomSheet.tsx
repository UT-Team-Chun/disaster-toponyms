import { X } from "lucide-react";

type Props = {
  title: string;
  open: boolean;
  onClose: () => void;
  /** シートの高さ。画面の高さに対する割合で指定する。 */
  heightClass?: string;
  children: React.ReactNode;
};

/**
 * 画面下からせり上がるパネル。
 * 狭い画面では地図を隠さずに操作できるよう、左右のサイドバーの代わりに使う。
 */
export function BottomSheet(props: Props) {
  if (!props.open) return null;
  return (
    <div className="absolute inset-0 z-30 flex flex-col justify-end md:hidden">
      <button
        type="button"
        aria-label="閉じる"
        className="flex-1 cursor-pointer bg-black/20"
        onClick={props.onClose}
      />
      <div
        className={[
          "flex flex-col rounded-t-xl border-t border-border bg-card shadow-2xl",
          props.heightClass ?? "max-h-[72dvh]",
        ].join(" ")}
      >
        <div className="flex shrink-0 items-center justify-between border-b border-border px-3 py-2">
          <span
            aria-hidden
            className="absolute inset-x-0 top-1.5 mx-auto h-1 w-10 rounded-full bg-border"
          />
          <h2 className="text-sm font-semibold">{props.title}</h2>
          <button
            type="button"
            onClick={props.onClose}
            aria-label="閉じる"
            className="flex size-9 cursor-pointer items-center justify-center rounded-md hover:bg-accent"
          >
            <X className="size-4" />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain pb-[env(safe-area-inset-bottom)]">
          {props.children}
        </div>
      </div>
    </div>
  );
}
