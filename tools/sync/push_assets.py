"""把暂存的原图增量上传到 Hugging Face 数据集（只传清单里 uploaded=false 且本地存在的文件）。"""
from __future__ import annotations

from pathlib import Path

from .common import dump_json, load_json

REPO_ID = "OliverThompson/figtx-assets"
README = Path(__file__).with_name("hf_readme.md")


def original_url(item_id: str, ext: str) -> str:
    return f"https://huggingface.co/datasets/{REPO_ID}/resolve/main/originals/{item_id}.{ext}"


def push(originals_dir, manifest_path, api=None, dry_run: bool = False) -> dict:
    """上传 uploaded=false 的原图；删除清单里标记 takedown 的原图。任何 HTTP 错误都记进报告，不中断同步。"""
    originals_dir = Path(originals_dir)
    manifest = load_json(manifest_path, {})
    pending = sorted(k for k, v in manifest.items() if not v.get("takedown") and not v.get("uploaded")
                     and (originals_dir / f"{k}.{v['ext']}").is_file())
    takedown = sorted(k for k, v in manifest.items() if v.get("takedown"))
    if dry_run:
        out = {"uploaded": 0, "pending": len(pending)}
        if takedown:
            out["pending_delete"] = len(takedown)
        return out
    if not pending and not takedown:
        return {"uploaded": 0}
    if api is None:
        from huggingface_hub import HfApi

        api = HfApi()
    from huggingface_hub.errors import HfHubHTTPError, LocalTokenNotFoundError

    rep = {"uploaded": 0}
    try:
        api.create_repo(REPO_ID, repo_type="dataset", exist_ok=True, private=False)
        if pending:
            files = [f"{k}.{manifest[k]['ext']}" for k in pending]
            api.upload_folder(repo_id=REPO_ID, repo_type="dataset", folder_path=str(originals_dir),
                              path_in_repo="originals", allow_patterns=files,
                              commit_message=f"sync: add/update {len(files)} originals")
            api.upload_file(path_or_fileobj=str(README), path_in_repo="README.md", repo_id=REPO_ID,
                            repo_type="dataset", commit_message="sync: dataset card")
            for k in pending:
                manifest[k]["uploaded"] = True
            rep["uploaded"] = len(files)
        remote = [k for k in takedown if manifest[k].get("uploaded")]
        if remote:
            api.delete_files(repo_id=REPO_ID, repo_type="dataset",
                             delete_patterns=[f"originals/{k}.{manifest[k]['ext']}" for k in remote],
                             commit_message=f"takedown: remove {len(remote)} originals")
        if remote:
            rep["deleted"] = len(remote)
        for k in takedown:
            manifest.pop(k, None)
    except LocalTokenNotFoundError:
        print("跳过上传：未登录 Hugging Face（本地运行 hf auth login，或在 CI 里设置 HF_TOKEN）")
        return {"uploaded": 0, "skipped": "no-auth"}
    except (HfHubHTTPError, OSError) as e:
        rep["error"] = f"{type(e).__name__}: {e}"[:300]
    dump_json(manifest_path, manifest)
    return rep
