// 条目详情分片：构建（build-data.mjs）和前端（src/lib/data.ts）共用同一个哈希，保证能找到同一个分片。
export const SHARDS = 64;

/** djb2 哈希取模，返回 0..SHARDS-1。 */
export function shardOf(id) {
  let h = 5381;
  for (let i = 0; i < id.length; i++) h = ((h * 33) ^ id.charCodeAt(i)) >>> 0;
  return h % SHARDS;
}

export const pad = (n) => String(n).padStart(2, '0');
