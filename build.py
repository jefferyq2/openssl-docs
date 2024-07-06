import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


VERSION_MAP = {
    "master": "master",
    "3.3": "openssl-3.3",
    "3.2": "openssl-3.2",
    "3.1": "openssl-3.1",
    "3.0": "openssl-3.0",
    "1.1.1": "OpenSSL_1_1_1-stable",
    "1.0.2": "OpenSSL_1_0_2-stable",
}


def clone(branch: str, tmp_dir: str) -> None:
    subprocess.run(
        ["git", "clone", "--single-branch", "-b", branch, "--depth", "1", "https://github.com/openssl/openssl", tmp_dir]
    )


def build_manpages(tmp_dir: str):
    if return_code := subprocess.run(["sh", "config"], cwd=tmp_dir).returncode != 0:
        raise SystemExit(return_code)
    cmd = ["make", "-j", str(os.cpu_count()), "build_man_docs"]
    if return_code := subprocess.run(cmd, cwd=tmp_dir).returncode != 0:
        raise SystemExit(return_code)


def clean_docs():
    try:
        shutil.rmtree("docs/")
    except FileNotFoundError:
        pass


def create_dirs():
    os.makedirs("docs/man1", exist_ok=True)
    os.makedirs("docs/man3", exist_ok=True)
    os.makedirs("docs/man5", exist_ok=True)
    os.makedirs("docs/man7", exist_ok=True)


def convert_pod_to_md(tmp_dir: str):
    # for openssl 1.0.2
    dir_map = {
        "apps": "man1",
        "crypto": "man3",
        "ssl": "man3",
        "man1": "man1",
        "man3": "man3",
        "man5": "man5",
        "man7": "man7",
    }
    for pod in Path(f"{tmp_dir}/doc").glob("**/*.pod"):
        if "internal" in pod.parent.parts:
            continue
        target = f"docs/{dir_map[pod.parent.name]}/{pod.stem}.md"
        ps = subprocess.run(["pod2markdown", "--man-url-prefix", "../../man", str(pod), target])
        if ps.returncode != 0:
            raise SystemExit(ps.returncode)


def copy_images(tmp_dir: str):
    shutil.copytree(f"{tmp_dir}/doc/man7/img", "docs/man7/img")


def build_site(version: str):
    return subprocess.run(["mike", "deploy", version]).returncode


def main():
    version = sys.argv[1]
    clean_docs()
    create_dirs()
    with tempfile.TemporaryDirectory() as tmp_dir:
        clone(VERSION_MAP[version], tmp_dir)
        if version not in ["1.0.2", "1.1.1"]:
            build_manpages(tmp_dir)
        convert_pod_to_md(tmp_dir)
        if version not in ["1.0.2", "1.1.1"]:
            copy_images(tmp_dir)
    return build_site(version)


if __name__ == "__main__":
    sys.exit(main())
