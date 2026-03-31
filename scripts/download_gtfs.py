import httpx
import zipfile
from pathlib import Path
from typing import Optional

API_URL = "https://opendata.porto.digital/api/3/action/package_show"
DATASET_ID = "horarios-paragens-e-rotas-em-formato-gtfs-stcp"

def get_latest_gtfs_url(timeout: float = 30.0) -> str:
    response = httpx.get(
        API_URL,
        params={"id": DATASET_ID},
        timeout=timeout,
        follow_redirects=True,
    )
    response.raise_for_status()
    payload = response.json()

    if not payload.get("success") or "result" not in payload:
        raise ValueError("Failed to fetch GTFS dataset metadata from Porto Open Data.")

    def is_gtfs_zip(resource: dict) -> bool:
        fmt = str(resource.get("format", "")).lower()
        url = str(resource.get("url", "")).lower()
        name = str(resource.get("name", "")).lower()
        return ("zip" in fmt or url.endswith(".zip")) and ("gtfs" in name or "gtfs" in url)

    candidates = [r for r in payload["result"].get("resources", []) if is_gtfs_zip(r)]
    if not candidates:
        raise ValueError("No GTFS ZIP resources found in dataset.")

    latest = max(candidates, key=lambda r: r.get("last_modified") or r.get("created") or "")
    url = latest.get("url")
    if not url:
        raise ValueError("Latest GTFS resource does not contain a download URL.")
    return url


def download_gtfs(
    output_dir: Path,
    url: Optional[str] = None,
    timeout: float = 30.0,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_url = url or get_latest_gtfs_url(timeout=timeout)

    print(f"Downloading GTFS file from: {source_url}")
    
    # Download
    with httpx.stream("GET", source_url, timeout=timeout, follow_redirects=True) as response:
        response.raise_for_status()
        
        zip_path = output_dir / "gtfs_temp.zip"
        
        print("Downloading...")
        with open(zip_path, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)
            
    # Extract zip
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(output_dir)
    
    # Remove zip
    zip_path.unlink()


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / "data" / "raw" / "stcp"
    
    try:
        download_gtfs(output_dir=output_dir)
        print(f"\nGTFS files downloaded and extracted to: {output_dir}")
    except httpx.HTTPError as e:
        print(f"Error downloading file: {e}")
        exit(1)
    except zipfile.BadZipFile as e:
        print(f"Error: Invalid zip file: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)