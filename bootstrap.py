#!/usr/bin/env python3
"""Install the pinned official Typst compiler locally, without sudo."""
import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    lock = json.loads((ROOT / 'toolchain.json').read_text())
    destination = ROOT / '.tools/bin/typst'
    for candidate in [str(destination), shutil.which('typst')]:
        if candidate and Path(candidate).is_file():
            if subprocess.check_output([candidate, '--version'], text=True).strip() == lock['typst_version']:
                print(f'Pinned Typst available: {candidate}')
                return
    machine = {'amd64': 'x86_64', 'arm64': 'aarch64'}.get(platform.machine(), platform.machine())
    suffix = {'Linux': 'unknown-linux-musl', 'Darwin': 'apple-darwin'}.get(platform.system())
    name = f'typst-{machine}-{suffix}.tar.xz'
    if name not in lock['assets']:
        raise SystemExit('Unsupported platform. Install the exact compiler in toolchain.json manually.')
    asset = lock['assets'][name]
    print(f'Downloading official compiler: {name}')
    with urllib.request.urlopen(asset['url'], timeout=90) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != asset['sha256']:
        raise SystemExit('Compiler archive checksum mismatch; refusing installation.')
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:xz') as archive:
        member = archive.getmember(name.removesuffix('.tar.xz') + '/typst')
        if not member.isfile():
            raise SystemExit('Expected a regular compiler binary.')
        binary = archive.extractfile(member).read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.tmp')
    temporary.write_bytes(binary)
    os.chmod(temporary, 0o755)
    os.replace(temporary, destination)
    version = subprocess.check_output([str(destination), '--version'], text=True).strip()
    if version != lock['typst_version']:
        raise SystemExit(f'Unexpected compiler version: {version}')
    print(f'Installed {version} in .tools/bin (not committed).')

if __name__ == '__main__':
    main()
