//! Development consistency checks, not execution attestation or live acceptance.
use std::{
    collections::BTreeMap,
    fs,
    io::Write,
    path::{Component, Path},
    process::{Command, Stdio},
};

pub const README: &str = include_str!("../templates/README.md");
pub const CHECKS: &str = include_str!("../templates/checks.tsv");
const BADGE: &str = "https://raw.githubusercontent.com/tcballard/omarchy-badges/75975e5b5bf75e7ede3764bcd2950046f7abfe2c/badges/v1/omarchy-theme.svg";
type Manifest = BTreeMap<String, String>;

fn safe_relative(s: &str) -> Result<(), String> {
    if s.is_empty()
        || s.contains(['\t', '\n', '\r', '\\'])
        || Path::new(s)
            .components()
            .any(|c| !matches!(c, Component::Normal(_)))
    {
        return Err(format!("expected a safe relative file path: {s}"));
    }
    Ok(())
}
fn files(root: &Path, dir: &Path, out: &mut Vec<String>) -> Result<(), String> {
    for entry in fs::read_dir(dir).map_err(|e| e.to_string())? {
        let p = entry.map_err(|e| e.to_string())?.path();
        let rel = p
            .strip_prefix(root)
            .unwrap()
            .to_str()
            .ok_or("non-UTF-8 path")?
            .to_owned();
        if rel == ".git" {
            continue;
        }
        safe_relative(&rel)?;
        let meta = fs::symlink_metadata(&p).map_err(|e| e.to_string())?;
        if meta.file_type().is_symlink() {
            return Err(format!("symlink: {rel}"));
        }
        if meta.is_dir() {
            files(root, &p, out)?;
        } else if meta.is_file() {
            out.push(rel);
        } else {
            return Err(format!("not a regular file: {rel}"));
        }
    }
    Ok(())
}
fn tree(root: &Path) -> Result<Vec<String>, String> {
    let meta = fs::symlink_metadata(root).map_err(|e| e.to_string())?;
    if !meta.is_dir() || meta.file_type().is_symlink() {
        return Err("use a real theme directory".into());
    }
    let mut out = Vec::new();
    files(root, root, &mut out)?;
    out.sort();
    Ok(out)
}
fn hash(root: &Path, path: &str) -> Result<String, String> {
    // Stable Git blob SHA-1, independent of repo configuration, filters and index.
    let bytes = fs::read(root.join(path)).map_err(|e| e.to_string())?;
    let mut child = Command::new("git")
        .args(["hash-object", "--stdin"])
        .env_remove("GIT_DEFAULT_HASH")
        .current_dir(std::env::temp_dir())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Git is required for content manifests: {e}"))?;
    child
        .stdin
        .take()
        .unwrap()
        .write_all(&bytes)
        .map_err(|e| e.to_string())?;
    let output = child.wait_with_output().map_err(|e| e.to_string())?;
    if !output.status.success() {
        return Err("git hash-object failed".into());
    }
    let result = String::from_utf8(output.stdout)
        .map_err(|e| e.to_string())?
        .trim()
        .to_owned();
    if result.len() != 40 || !result.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err("expected Git SHA-1 blob hash".into());
    }
    Ok(result)
}
fn manifest(root: &Path, implementation: bool) -> Result<Manifest, String> {
    tree(root)?
        .into_iter()
        .filter(|p| !p.starts_with("evidence/") && !(implementation && p.ends_with(".md")))
        .map(|p| hash(root, &p).map(|h| (p, h)))
        .collect()
}
pub fn snapshot(root: &Path, path: &str, implementation: bool) -> Result<(), String> {
    safe_relative(path)?;
    if !path.starts_with("evidence/") || !path.ends_with(".manifest") {
        return Err("write snapshots under evidence/ with a .manifest suffix".into());
    }
    let values = manifest(root, implementation)?;
    let mut text = format!(
        "# git-blob-sha1 {}\n",
        if implementation {
            "implementation"
        } else {
            "delivery"
        }
    );
    for (path, hash) in values {
        text.push_str(&format!("{hash}\t{path}\n"));
    }
    super::new_file(&root.join(path), &text)
        .map_err(|e| format!("snapshot is immutable; use a new name: {e}"))?;
    println!("Recorded {path}; no validation command was run.");
    Ok(())
}
fn load_manifest(root: &Path, path: &str) -> Result<(bool, Manifest), String> {
    safe_relative(path)?;
    if !path.starts_with("evidence/") || !path.ends_with(".manifest") {
        return Err("manifest must be in evidence/".into());
    }
    let text = fs::read_to_string(root.join(path)).map_err(|e| format!("{path}: {e}"))?;
    let mut lines = text.lines();
    let implementation = match lines.next() {
        Some("# git-blob-sha1 implementation") => true,
        Some("# git-blob-sha1 delivery") => false,
        _ => return Err(format!("{path}: invalid manifest header")),
    };
    let mut values = Manifest::new();
    for line in lines {
        let (hash, file) = line.split_once('\t').ok_or("invalid manifest entry")?;
        safe_relative(file)?;
        if file.starts_with("evidence/")
            || hash.len() != 40
            || !hash.bytes().all(|c| c.is_ascii_hexdigit())
            || values.insert(file.into(), hash.into()).is_some()
        {
            return Err(format!("{path}: invalid/duplicate manifest entry"));
        }
    }
    if !values.contains_key("colors.toml") {
        return Err(format!("{path}: missing colors.toml"));
    }
    Ok((implementation, values))
}
fn field<'a>(text: &'a str, name: &str) -> Option<&'a str> {
    text.lines()
        .find_map(|l| l.strip_prefix(name))
        .map(str::trim)
        .filter(|s| !s.is_empty())
}
fn attr<'a>(tag: &'a str, key: &str) -> Option<&'a str> {
    for quote in ['"', '\''] {
        let start = format!("{key}={quote}");
        if let Some((_, tail)) = tag.split_once(&start) {
            return tail.split(quote).next();
        }
    }
    None
}
fn local_link(root: &Path, doc: &str, target: &str, errors: &mut Vec<String>) {
    let target = target.trim().trim_matches(['<', '>']);
    if target.starts_with('#') || target.contains("://") || target.starts_with("mailto:") {
        return;
    }
    let path = target.split(['#', '?']).next().unwrap_or("");
    // Percent-encoded paths and parent traversal need manual normalization; never silently skip them.
    if path.contains('%') || safe_relative(path).is_err() {
        errors.push(format!(
            "{doc}: unsupported local link {target}; use a plain relative path"
        ));
        return;
    }
    if !root
        .join(Path::new(doc).parent().unwrap())
        .join(path)
        .exists()
    {
        errors.push(format!("{doc}: stale asset/link {target}"));
    }
}
fn links(root: &Path, doc: &str, text: &str, errors: &mut Vec<String>) {
    // Supported authoring subset: inline Markdown, reference definitions, HTML and bare asset paths.
    for line in text.lines() {
        let mut tail = line;
        while let Some((_, rest)) = tail.split_once("](") {
            if let Some((target, next)) = rest.split_once(')') {
                local_link(root, doc, target.split(" \"").next().unwrap(), errors);
                tail = next;
            } else {
                errors.push(format!("{doc}: unclosed Markdown link"));
                break;
            }
        }
        if line.trim_start().starts_with('[') {
            if let Some((_, target)) = line.split_once("]: ") {
                local_link(root, doc, target.split(" \"").next().unwrap(), errors);
            }
        }
        for part in line.split('<').skip(1) {
            if let Some((tag, _)) = part.split_once('>') {
                for key in ["src", "href"] {
                    if let Some(target) = attr(tag, key) {
                        local_link(root, doc, target, errors);
                    }
                }
            }
        }
        for token in line.split(|c: char| c.is_whitespace() || "`\"'<>()[ ]*,;".contains(c)) {
            let token = token.trim_end_matches('.');
            let ext = Path::new(token)
                .extension()
                .and_then(|e| e.to_str())
                .unwrap_or("")
                .to_lowercase();
            if !token.contains("://")
                && [
                    "png", "jpg", "jpeg", "webp", "gif", "bmp", "svg", "mp4", "m4v", "mov", "webm",
                    "mkv", "avi",
                ]
                .contains(&ext.as_str())
            {
                local_link(root, doc, token, errors);
            }
        }
    }
}

pub fn check(root: &Path, delivery: &str) -> Result<(), String> {
    let paths = tree(root)?; // Reject links before reading any content.
    let mut errors = Vec::new();
    let readme = fs::read_to_string(root.join("README.md")).map_err(|e| e.to_string())?;
    let credits =
        fs::read_to_string(root.join("CREDITS.md")).map_err(|e| format!("CREDITS.md: {e}"))?;
    let badge = readme
        .split('<')
        .filter_map(|p| p.split_once('>').map(|x| x.0))
        .any(|tag| {
            tag.starts_with("img ")
                && attr(tag, "src") == Some(BADGE)
                && attr(tag, "height") == Some("20")
                && attr(tag, "width").is_none()
                && attr(tag, "style").is_none()
        });
    if !badge {
        errors.push(
            "README: missing approved Theme SVG at height=20 with natural proportions".into(),
        );
    }
    for prefix in ["Target:", "Status:"] {
        if !readme
            .split('<')
            .filter_map(|p| p.split_once('>').map(|x| x.0))
            .any(|tag| {
                tag.starts_with("img ")
                    && attr(tag, "alt").is_some_and(|a| a.starts_with(prefix))
                    && attr(tag, "height") == Some("20")
                    && attr(tag, "width").is_none()
                    && attr(tag, "style").is_none()
            })
        {
            errors.push(format!(
                "README: missing {prefix} badge at natural 20px height"
            ));
        }
    }
    for label in [
        "Status:",
        "Intended Omarchy target:",
        "Tested installed Omarchy version:",
    ] {
        if field(&readme, label).is_none() {
            errors.push(format!("README: missing {label}"));
        }
    }
    for heading in ["## Install", "## Rollback", "## Validation limits"] {
        if !readme.contains(heading) {
            errors.push(format!("README: missing {heading}"));
        }
    }
    for phrase in [
        "compatible with",
        "tested on",
        "works on",
        "production-ready",
        "fully tested",
    ] {
        if readme.to_lowercase().contains(phrase) {
            errors.push(format!("README: unsupported compatibility claim '{phrase}'; use the tested-version field and scoped evidence"));
        }
    }
    for path in paths
        .iter()
        .filter(|p| p.ends_with(".md") && !p.starts_with("evidence/"))
    {
        links(
            root,
            path,
            &fs::read_to_string(root.join(path)).map_err(|e| e.to_string())?,
            &mut errors,
        );
    }
    for asset in paths.iter().filter(|p| p.starts_with("backgrounds/")) {
        if !credits.contains(asset) {
            errors.push(format!("CREDITS.md: missing delivered asset {asset}"));
        }
    }
    let media =
        fs::read_to_string(root.join("media.tsv")).map_err(|e| format!("media.tsv: {e}"))?;
    let mut media_paths = Vec::new();
    let mut desktop_media = false;
    for line in media
        .lines()
        .filter(|l| !l.starts_with('#') && !l.is_empty())
    {
        let cols: Vec<_> = line.split('\t').collect();
        if cols.len() != 3 || cols.iter().any(|c| c.trim().is_empty()) {
            errors.push("media.tsv: expected path, kind, caption".into());
            continue;
        }
        let (path, kind, caption) = (cols[0], cols[1], cols[2]);
        if safe_relative(path).is_err()
            || !paths.iter().any(|p| p == path)
            || media_paths.contains(&path)
        {
            errors.push(format!("media.tsv: stale/invalid/duplicate asset {path}"));
        }
        media_paths.push(path);
        if !["wallpaper", "contact-sheet", "desktop-screenshot", "mockup"].contains(&kind) {
            errors.push(format!("media.tsv: unknown media kind {kind}"));
        }
        if kind == "contact-sheet" || kind == "mockup" {
            if !caption.contains("not a desktop screenshot") {
                errors.push(format!("{path}: label {kind} as not a desktop screenshot"));
            }
            if Path::new(path).file_stem().and_then(|x| x.to_str()) == Some("preview") {
                errors.push(format!(
                    "{path}: reserve preview.* for real desktop captures"
                ));
            }
        }
        if readme.contains(path) && !readme.contains(caption) {
            errors.push(format!("{path}: README must include its media caption"));
        }
        if kind == "desktop-screenshot" {
            desktop_media = true;
        }
    }
    for path in &paths {
        let ext = Path::new(path)
            .extension()
            .and_then(|e| e.to_str())
            .unwrap_or("")
            .to_lowercase();
        if [
            "png", "jpg", "jpeg", "webp", "gif", "bmp", "svg", "mp4", "m4v", "mov", "webm", "mkv",
            "avi",
        ]
        .contains(&ext.as_str())
            && !media_paths.contains(&path.as_str())
        {
            errors.push(format!("media.tsv: unclassified delivered media {path}"));
        }
        if path.starts_with("evidence/")
            && path != "evidence/checks.tsv"
            && !["manifest", "txt", "log", "md"].contains(&ext.as_str())
        {
            errors.push(format!(
                "{path}: evidence/ is reserved for ledgers, manifests and text logs"
            ));
        }
    }
    let current = manifest(root, false)?;
    let current_implementation: Manifest = current
        .iter()
        .filter(|(p, _)| !p.ends_with(".md"))
        .map(|(p, h)| (p.clone(), h.clone()))
        .collect();
    let (implementation, delivered) = load_manifest(root, delivery)?;
    if implementation || delivered != current {
        errors.push("delivery manifest differs from delivered files (refresh documentation/asset handoff snapshot)".into());
    }
    let ledger = fs::read_to_string(root.join("evidence/checks.tsv")).map_err(|e| e.to_string())?;
    let mut kinds = Vec::new();
    let mut live_versions = Vec::new();
    for (i, line) in ledger.lines().enumerate() {
        if line.starts_with('#') || line.is_empty() {
            continue;
        }
        let cols: Vec<_> = line.split('\t').collect();
        if cols.len() != 7 || cols.iter().any(|c| c.trim().is_empty()) {
            errors.push(format!(
                "checks.tsv:{}: expected seven nonempty tab-separated fields",
                i + 1
            ));
            continue;
        }
        let (state, kind, snapshot, upstream, version, command, result) = (
            cols[0], cols[1], cols[2], cols[3], cols[4], cols[5], cols[6],
        );
        if !["now", "historical", "failure", "not-run"].contains(&state)
            || !["local", "live", "registry"].contains(&kind)
        {
            errors.push(format!("checks.tsv:{}: invalid state/kind", i + 1));
            continue;
        }
        if upstream != "none"
            && !upstream
                .split(|c: char| !c.is_ascii_hexdigit())
                .any(|part| part.len() == 40)
        {
            errors.push(format!("{state} {kind}: upstream must identify an exact commit/blob SHA, not a moving branch"));
        }
        kinds.push(kind);
        if state == "not-run" {
            if snapshot != "-" || version != "-" || command != "-" {
                errors.push(
                    "not-run must not claim a snapshot, installed version or executed command"
                        .into(),
                );
            }
        } else {
            if command == "-"
                || (kind != "local" && (upstream == "none" || version == "-" && kind == "live"))
            {
                errors.push(format!(
                    "{state} {kind}: command/upstream/installed version missing"
                ));
            }
            let (scope, recorded) = load_manifest(root, snapshot)?;
            let matches = recorded
                == if scope {
                    &current_implementation
                } else {
                    &current
                }
                .clone();
            if state == "now" && !matches {
                errors.push(format!("{snapshot}: evidence from different files cannot be reported as reproduced now"));
            }
            if kind == "live" && matches && ["now", "historical"].contains(&state) {
                live_versions.push(version);
            }
            if state == "historical" {
                println!(
                    "HISTORICAL {kind}: {result}; files {}",
                    if matches {
                        "unchanged; not rerun"
                    } else {
                        "DIFFER; not evidence for this delivery"
                    }
                );
            }
        }
        if state != "historical" {
            println!("{} {kind}: {result}", state.to_uppercase());
        }
    }
    for kind in ["local", "live", "registry"] {
        if !kinds.contains(&kind) {
            errors.push(format!(
                "checks.tsv: missing {kind} evidence or explicit not-run row"
            ));
        }
    }
    if desktop_media && live_versions.is_empty() {
        errors.push(
            "desktop screenshots require matching live evidence; a contact sheet is not a capture"
                .into(),
        );
    }
    if let Some(version) = field(&readme, "Tested installed Omarchy version:") {
        if version != "none" && !live_versions.contains(&version) {
            errors.push(format!("README: unsupported tested installed version '{version}'; no matching live evidence for these files"));
        }
    }
    println!("NOT CHECKED: execution authenticity, prose completeness, remote URLs, image content/rights, live desktop acceptance, release readiness, registry submission.");
    if errors.is_empty() {
        println!("PASS: development handoff consistency only; failures and not-run checks above remain limits");
        Ok(())
    } else {
        Err(errors.join("\n"))
    }
}
