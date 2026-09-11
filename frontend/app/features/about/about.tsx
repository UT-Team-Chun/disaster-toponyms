import { useEffect, useState } from "react";
import { Link } from "react-router";

import { SiteHeader } from "~/components/ui/siteHeader";
import { fetchMeta, fetchStats } from "~/lib/dataset/client";
import {
  EVIDENCE_LEVEL_DESCRIPTIONS,
  EVIDENCE_LEVEL_LABELS,
} from "~/lib/dataset/labels";
import type { Meta, Stats } from "~/lib/dataset/schema";

export function About() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [meta, setMeta] = useState<Meta | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [loadedStats, loadedMeta] = await Promise.all([
          fetchStats(),
          fetchMeta(),
        ]);
        if (cancelled) return;
        setStats(loadedStats);
        setMeta(loadedMeta);
      } catch {
        // 集計が読めなくても説明は表示する
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <SiteHeader builtAt={meta?.builtAt ?? null} />
      <main className="mx-auto w-full max-w-3xl flex-1 space-y-6 px-4 py-6 text-sm leading-relaxed">
        <section>
          <h1 className="text-xl font-semibold">この地図について</h1>
          <p className="mt-2">
            日本には、災害の経験や地形の危うさを先人が地名に刻んだ「警鐘地名（災害地名）」が
            残っています。この地図はそれを、
            <strong className="font-medium">
              文字パターンではなく出典に基づいて
            </strong>
            集約したものです。
          </p>
          <p className="mt-2">
            たとえば群馬県桐生市の旧小字「梅ヶ久保」は、梅の生えた窪地に見えます。しかし
            『桐生市地名考』は「梅は埋の替字で山腹の崩壊で埋まって傾斜地の出来たくぼ」と
            記しています。こうした記述がなければ、字面からは危険を読み取れません。
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold">根拠レベル</h2>
          <p className="mt-1">
            すべての地名に、出典が何を述べているかによる根拠レベルを付けています。
            災害リスクを地名から読むには、この区別が欠かせません。
          </p>
          <dl className="mt-3 space-y-2">
            {[3, 2, 1, 0].map((level) => (
              <div
                key={level}
                className="rounded-md border border-border bg-card p-2.5"
              >
                <dt className="text-xs font-semibold">
                  レベル {level}: {EVIDENCE_LEVEL_LABELS[level]}
                  {stats ? (
                    <span className="ml-2 font-normal text-muted-foreground">
                      {level === 0
                        ? stats.candidatesTotal
                        : (stats.byLevel[String(level)] ?? 0)}
                      件
                    </span>
                  ) : null}
                </dt>
                <dd className="mt-0.5 text-xs text-muted-foreground">
                  {EVIDENCE_LEVEL_DESCRIPTIONS[level]}
                </dd>
              </div>
            ))}
          </dl>
          <p className="mt-3">
            レベル0の候補は既定では非表示です。全国の住所データで表記が
            <Link
              to="/elements"
              className="text-primary underline underline-offset-2"
            >
              地名要素辞典
            </Link>
            に一致するだけのもので、災害履歴を示すとは限りません。
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold">俗説への注意</h2>
          <p className="mt-1">
            災害地名は、後から面白く語り直されることがあります。磯田(2018)は
            「現実的な被災の記憶や史実にもとづく災害地名とその由来は忘れられやすく、
            生き残る災害地名は話として面白くするために尾ひれをつけたものではないか」
            と指摘しています。
          </p>
          <p className="mt-2">
            この地図は、出典自身が由来に疑義を示している場合を
            <strong className="font-medium">「異説あり」</strong>
            として記録します。広島市安佐南区八木の「八木蛇落地悪谷」は代表例で、
            大蛇退治の伝説は地元の寺に伝わる一方、広島市郷土資料館は「蛇落地」「悪谷」を
            記す文献を確認できないとしています。反証も出典として並べて表示します。
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold">地名は点ではなく範囲</h2>
          <p className="mt-1">
            地名が指すのは一点ではなく広がりです。ハザードマップとして読むには、
            その広がりが警戒区域とどう重なるかが見えなければ意味がありません。
            小字の境界は全国では公開されていないため、公開されている最も細かい単位である
            <strong className="font-medium">国勢調査の町丁・字等</strong>
            のポリゴンで、各地名が属する区画を描いています。
          </p>
          <p className="mt-2">
            地図上の点は範囲の代表点で、地名が指す場所そのものではありません。
            各地名には位置の精度（小字・大字-町丁目・市区町村）を必ず添えています。
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold">
            現在のハザードマップとの関係
          </h2>
          <p className="mt-1">
            各地名の座標で、重ねるハザードマップの土砂災害警戒区域・洪水浸水想定区域・
            津波浸水想定・高潮浸水想定を照合しています。これは
            <strong className="font-medium">地名の由来とは別の軸</strong>
            です。今の指定と昔の警鐘が一致することもあれば、しないこともあります。
            混同しないよう、詳細パネルでは別の見出しで表示しています。
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold">作り方</h2>
          <ol className="mt-1 list-decimal space-y-1.5 pl-5">
            <li>
              自治体の地名考（『桐生市地名考』など）を版面のまま取り込み、
              「崩壊地名」「替字」といった記述を機械的に判定して根拠を付けます。
            </li>
            <li>
              散文の資料（自治体の防災資料、事典記事）は言語モデルで構造化しますが、
              引用文が原資料と一字一句一致するかを機械検証し、
              一致しないものは破棄します。モデルには記述の
              <strong className="font-medium">整理だけ</strong>
              を任せ、内容の創作はさせません。
            </li>
            <li>
              全国の大字・小字を要素辞典で走査してレベル0の候補を作ります。
            </li>
            <li>
              小字は全国のジオコーダに載らないため、位置の精度（小字・大字・市区町村）を
              必ず記録して表示します。
            </li>
          </ol>
        </section>

        <section>
          <h2 className="text-base font-semibold">収録状況</h2>
          {stats ? (
            <table className="mt-2 w-full max-w-sm text-xs">
              <tbody>
                <tr className="border-b border-border">
                  <td className="py-1">出典で裏づけた地名</td>
                  <td className="py-1 text-right font-mono">
                    {stats.toponymsTotal}
                  </td>
                </tr>
                <tr className="border-b border-border">
                  <td className="py-1">字面のみの候補</td>
                  <td className="py-1 text-right font-mono">
                    {stats.candidatesTotal}
                  </td>
                </tr>
                <tr className="border-b border-border">
                  <td className="py-1">自然災害伝承碑</td>
                  <td className="py-1 text-right font-mono">
                    {stats.monumentsTotal}
                  </td>
                </tr>
                <tr>
                  <td className="py-1">異説ありとして記録</td>
                  <td className="py-1 text-right font-mono">
                    {stats.disputedTotal}
                  </td>
                </tr>
              </tbody>
            </table>
          ) : null}
          <p className="mt-2 text-xs text-muted-foreground">
            候補（レベル0）と伝承碑は全国を覆っていますが、
            <strong className="font-medium text-foreground">
              根拠レベル2以上は群馬県（桐生市）に偏っています
            </strong>
            。これは危険が群馬に集中しているという意味ではなく、版面まで解析できた
            地名考が桐生市のものだけだからです。分布は「資料を入れた地域」を
            表していると読んでください。地名考・郡誌・村誌は自治体ごとに存在するため、
            出典を追加するほど収録は増えます。
          </p>
        </section>

        <section>
          <h2 className="text-base font-semibold">出典</h2>
          <p className="mt-1">
            <Link
              to="/sources"
              className="text-primary underline underline-offset-2"
            >
              出典一覧
            </Link>
            にすべての資料を掲載しています。
          </p>
          {meta && meta.attribution.length > 0 ? (
            <ul className="mt-2 list-disc space-y-0.5 pl-5 text-xs text-muted-foreground">
              {meta.attribution.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : null}
        </section>
      </main>
    </div>
  );
}
