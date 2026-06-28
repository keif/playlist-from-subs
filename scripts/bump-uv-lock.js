const VERSION_RE = /(\[\[package\]\]\s*\nname = "yt-sub-playlist"\s*\nversion = ")([^"]+)(")/;

module.exports = {
  readVersion(contents) {
    const m = contents.match(VERSION_RE);
    if (!m) throw new Error("yt-sub-playlist package not found in uv.lock");
    return m[2];
  },
  writeVersion(contents, version) {
    const m = contents.match(VERSION_RE);
    if (!m) throw new Error("yt-sub-playlist package not found in uv.lock");
    return contents.replace(VERSION_RE, `$1${version}$3`);
  },
};
