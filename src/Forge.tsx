import { useCallback, useEffect, useState } from 'react';
import { figTypeLabel } from './labels';

/** 生成服务的地址。默认本地 8780 端口（8770 常被 macOS sharingd 占用）。 */
const API = (import.meta as any).env?.VITE_FIGGEN_URL || 'http://127.0.0.1:8780';

type Contract = {
  id: string;
  no: string | null;
  figType?: string;
  title: string;
  image: string;
};

type History = {
  round: number;
  score?: number;
  problems?: string[];
  fixes?: string[];
  error?: string;
};

const TARGETS: { key: string; label: string; hint: string }[] = [
  { key: 'pipeline', label: '架构总览', hint: '整体流程 + 关键模块放大' },
  { key: 'teaser', label: 'Teaser 主图', hint: '点出问题 + 一眼看到核心想法' },
  { key: 'motivation', label: '动机图', hint: '对比现有方法的失败与本文思路' },
  { key: 'comparison', label: '定性对比', hint: '输入/基线/本文 的对比网格' },
  { key: 'system', label: '系统图', hint: '模块划分与数据流' },
];

export default function Forge() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [online, setOnline] = useState<boolean | null>(null);
  const [refId, setRefId] = useState('');
  const [method, setMethod] = useState('');
  const [target, setTarget] = useState('pipeline');
  const [rounds, setRounds] = useState(3);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<History[]>([]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const h = await fetch(API + '/api/health');
        const hj = await h.json();
        if (!alive) return;
        setOnline(Boolean(hj.llm_configured));
        const c = await fetch(API + '/api/contracts');
        const cj = await c.json();
        if (!alive) return;
        setContracts(cj.contracts || []);
        if ((cj.contracts || []).length) setRefId(cj.contracts[0].id);
      } catch {
        if (alive) setOnline(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const run = useCallback(async () => {
    if (!method.trim() || busy) return;
    setBusy(true);
    setErr('');
    setResult(null);
    setHistory([]);
    try {
      const res = await fetch(API + '/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method, reference: refId, target, rounds }),
      });
      const j = await res.json();
      if (!res.ok || j.error) {
        setErr(j.error || '生成失败');
        setHistory(j.history || []);
      } else {
        setResult(j);
        setHistory(j.history || []);
      }
    } catch (e: any) {
      setErr(
        '连不上本地生成服务。先在仓库目录跑\n\n  npm run figgen:serve\n\n' +
          '然后刷新本页。（' + String(e?.message || e) + '）',
      );
    } finally {
      setBusy(false);
    }
  }, [method, refId, target, rounds, busy]);

  const download = (kind: 'svg' | 'png') => {
    if (!result) return;
    if (kind === 'svg' && result.svg) {
      const blob = new Blob([result.svg], { type: 'image/svg+xml' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = result.svg_file || 'figure.svg';
      a.click();
      URL.revokeObjectURL(a.href);
    } else if (kind === 'png' && result.png_file) {
      window.open(API + '/out/' + result.png_file, '_blank');
    }
  };

  return (
    <div className="forge">
      <div className="forge-head">
        <h2>框架图生成</h2>
        <p>
          选一张参考图定视觉语法，填写你的方法，生成<strong>可编辑 SVG</strong>。
          生成在本地完成，API key 不会离开你的机器。
        </p>
        {online === false && (
          <div className="forge-warn">
            本地生成服务未连接。在仓库目录运行 <code>npm run figgen:serve</code> 后刷新。
          </div>
        )}
      </div>

      <div className="forge-grid">
        <section className="forge-card">
          <label className="forge-label">参考图（决定视觉语法）</label>
          <div className="forge-refs">
            {contracts.map((c) => (
              <button
                key={c.id}
                className="forge-ref"
                data-active={refId === c.id}
                onClick={() => setRefId(c.id)}
                title={c.title}
              >
                <img src={'./' + c.image} alt={c.title} loading="lazy" />
                <span>{c.no || ''}</span>
              </button>
            ))}
            {!contracts.length && <div className="forge-empty">还没有设计契约缓存</div>}
          </div>

          <label className="forge-label">图的类型</label>
          <div className="forge-targets">
            {TARGETS.map((t) => (
              <button
                key={t.key}
                className="forge-target"
                data-active={target === t.key}
                onClick={() => setTarget(t.key)}
                title={t.hint}
              >
                {t.label}
              </button>
            ))}
          </div>

          <label className="forge-label">最多轮数</label>
          <div className="forge-targets">
            {[1, 2, 3, 5].map((n) => (
              <button
                key={n}
                className="forge-target"
                data-active={rounds === n}
                onClick={() => setRounds(n)}
              >
                {n} 轮
              </button>
            ))}
          </div>
        </section>

        <section className="forge-card">
          <label className="forge-label">你的方法（越具体越好）</label>
          <textarea
            className="forge-method"
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            placeholder={
              '例如：\n' +
              '问题：全注意力在 128K 上下文下 O(N²) 显存开销。\n' +
              '方法：1) 把序列切成 M 个块，每块独立 K/V 分片；' +
              '2) 用一个可学习的 router 记忆库给每个块打分，选 top-k；' +
              '3) 未选中的块聚合成 summary slots 保留全局信息。\n' +
              '结果：128K 上下文下 2.5x 加速，困惑度只涨 0.4。'
            }
            rows={12}
          />
          <div className="forge-actions">
            <button className="forge-go" onClick={run} disabled={busy || !method.trim()}>
              {busy ? '生成中…' : '生成框架图'}
            </button>
            <span className="forge-hint">
              约 {(rounds * 40).toFixed(0)}–{(rounds * 90).toFixed(0)} 秒
            </span>
          </div>
          {err && <pre className="forge-err">{err}</pre>}
        </section>
      </div>

      {(result || history.length > 0) && (
        <section className="forge-card forge-result">
          <div className="forge-result-head">
            <h3>结果</h3>
            {result && (
              <div className="forge-badges">
                <span className="forge-badge">评审 {Number(result.best_score).toFixed(1)}/10</span>
                <span className="forge-badge">{result.rounds} 轮</span>
                <button className="forge-dl" onClick={() => download('svg')}>
                  下载 SVG（可编辑）
                </button>
                {result.png_file && (
                  <button className="forge-dl" onClick={() => download('png')}>
                    下载 PNG
                  </button>
                )}
              </div>
            )}
          </div>

          <div className="forge-history">
            {history.map((h, i) => (
              <div key={i} className="forge-step">
                <b>第 {h.round} 轮</b>
                {h.score != null && <span> · {Number(h.score).toFixed(1)} 分</span>}
                {h.error && <span className="forge-step-err"> · {h.error}</span>}
                {!!(h.problems && h.problems.length) && (
                  <ul>
                    {h.problems.map((p, k) => (
                      <li key={k}>{p}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>

          {result?.svg && (
            <div
              className="forge-preview"
              dangerouslySetInnerHTML={{ __html: result.svg }}
            />
          )}
        </section>
      )}
    </div>
  );
}
