import { useEffect, useState } from "react";

/** 絞り込みを地図の横に置ける幅。Tailwind の md と揃えている。 */
const DESKTOP_QUERY = "(min-width: 768px)";
/** 絞り込みと詳細を地図の両側に並べても地図が読める幅。 */
const WIDE_QUERY = "(min-width: 1100px)";

const useMediaQuery = (query: string, fallback: boolean): boolean => {
  const [matches, setMatches] = useState(fallback);

  useEffect(() => {
    const media = window.matchMedia(query);
    const sync = () => setMatches(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, [query]);

  return matches;
};

/**
 * 絞り込みと詳細を、地図の横のパネルとして置けるか。
 * 置けない狭い画面では、下からせり上がるシートに切り替える。
 */
export const useIsDesktop = (): boolean => useMediaQuery(DESKTOP_QUERY, true);

/**
 * 絞り込みと詳細を地図の両側に同時に並べられるか。
 * タブレットの幅では両方を並べると地図が読めなくなるため、詳細は地図に重ねる。
 */
export const useIsWide = (): boolean => useMediaQuery(WIDE_QUERY, true);
