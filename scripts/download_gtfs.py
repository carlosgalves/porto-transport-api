import httpx
import zipfile
from pathlib import Path
from typing import Optional


def download_gtfs(
    url: str,
    output_dir: Path,
    timeout: float = 30.0,
) -> None:

    print(f"Downloading GTFS file from: {url}")
    
    # Download
    with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as response:
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
    GTFS_URL = (
        "https://opendata.porto.digital/dataset/5275c986-592c-43f5-8f87-aabbd4e4f3a4/"
        "resource/89a6854f-2ea3-4ba0-8d2f-6558a9df2a98/download/"
        "horarios_gtfs_stcp_16_04_2025.zip"
    )
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / "data" / "raw" / "stcp"
    
    try:
        download_gtfs(GTFS_URL, output_dir)
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