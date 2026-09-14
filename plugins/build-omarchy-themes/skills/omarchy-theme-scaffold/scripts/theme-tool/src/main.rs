mod handoff;
use std::{
    collections::BTreeMap,
    env, fs,
    io::{self, Write},
    path::Path,
    process,
};
const REQUIRED: &[&str] = &[
    "accent",
    "background",
    "foreground",
    "red",
    "yellow",
    "green",
    "cyan",
    "blue",
    "magenta",
];
const DENIED: &[&str] = &[
    "alacritty.toml",
    "foot.ini",
    "ghostty.conf",
    "kitty.conf",
    "vscode.json",
];
const STARTER: &str = include_str!("../starter.toml");

// A deliberately narrow authoring syntax, NOT a general TOML/legacy parser.
fn palette(text: &str) -> Result<BTreeMap<String, String>, String> {
    let mut values = BTreeMap::new();
    for (i, line) in text.lines().enumerate() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let (key, raw) = line
            .split_once('=')
            .ok_or_else(|| format!("line {}: expected key = quoted value", i + 1))?;
        let key = key.trim();
        if key.is_empty() || !key.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'_') {
            return Err(format!("line {}: unsupported key syntax", i + 1));
        }
        let raw = raw.trim();
        let quote = raw
            .chars()
            .next()
            .filter(|c| *c == '\'' || *c == '"')
            .ok_or_else(|| format!("line {}: use a quoted value", i + 1))?;
        let tail = &raw[1..];
        let end = tail
            .find(quote)
            .ok_or_else(|| format!("line {}: unclosed value", i + 1))?;
        let value = &tail[..end];
        let rest = tail[end + 1..].trim();
        if !rest.is_empty() && !rest.starts_with('#') {
            return Err(format!("line {}: trailing input", i + 1));
        }
        if key == "mode" {
            if value != "dark" && value != "light" {
                return Err("mode must be dark or light".into());
            }
        } else if rgb(value).is_none() {
            return Err(format!("{key}: helper accepts #RRGGBB only; use upstream validation for other supported syntax"));
        }
        if values.insert(key.to_string(), value.to_string()).is_some() {
            return Err(format!("duplicate key: {key}"));
        }
    }
    for key in REQUIRED {
        if !values.contains_key(*key) {
            return Err(format!("missing required semantic key: {key}; migrate legacy input with the upstream resolver"));
        }
    }
    Ok(values)
}
fn rgb(s: &str) -> Option<[f64; 3]> {
    if s.len() != 7 || !s.starts_with('#') || !s.as_bytes()[1..].iter().all(u8::is_ascii_hexdigit) {
        return None;
    }
    let mut out = [0.; 3];
    for i in 0..3 {
        out[i] = u8::from_str_radix(&s[1 + i * 2..3 + i * 2], 16).ok()? as f64 / 255.;
    }
    Some(out)
}
fn luminance(s: &str) -> f64 {
    let c = rgb(s).expect("validated colour").map(|x| {
        if x <= 0.04045 {
            x / 12.92
        } else {
            ((x + 0.055) / 1.055).powf(2.4)
        }
    });
    c[0] * 0.2126 + c[1] * 0.7152 + c[2] * 0.0722
}
fn contrast(a: &str, b: &str) -> f64 {
    let (a, b) = (luminance(a), luminance(b));
    (a.max(b) + 0.05) / (a.min(b) + 0.05)
}
fn slug_ok(s: &str) -> bool {
    !s.is_empty()
        && s.as_bytes()[0].is_ascii_lowercase()
        && s.bytes()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == b'-')
}
fn new_file(p: &Path, text: &str) -> io::Result<()> {
    let mut f = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(p)?;
    f.write_all(text.as_bytes())
}
fn scaffold(dest: &Path) -> Result<(), String> {
    let name = dest
        .file_name()
        .and_then(|x| x.to_str())
        .ok_or("invalid directory name")?;
    let slug = name
        .strip_prefix("omarchy-")
        .and_then(|s| s.strip_suffix("-theme"))
        .ok_or("use omarchy-<slug>-theme as the destination name")?;
    if !slug_ok(slug) {
        return Err(
            "use a lowercase slug starting with a letter, with letters, digits and hyphens".into(),
        );
    }
    // create_dir, not create_dir_all: existing destinations (including symlinks) are never replaced.
    fs::create_dir(dest).map_err(|e| format!("cannot create destination: {e}"))?;
    let result = (|| -> io::Result<()> {
        new_file(&dest.join("colors.toml"), STARTER)?;
        fs::create_dir(dest.join("backgrounds"))?;
        new_file(
            &dest.join("README.md"),
            &handoff::README.replace("{{slug}}", slug),
        )?;
        new_file(&dest.join("CREDITS.md"), "# Media credits\n\nNo media is bundled. For each delivered asset, list its exact root-relative path, creator, source URL, licence and redistribution permission (or explicitly pending). Code licensing does not cover artwork.\n")?;
        fs::create_dir(dest.join("evidence"))?;
        new_file(&dest.join("evidence/checks.tsv"), handoff::CHECKS)?;
        new_file(
            &dest.join("media.tsv"),
            include_str!("../templates/media.tsv"),
        )?;
        Ok(())
    })();
    result.map_err(|e| {
        format!(
            "scaffold incomplete at {}: {e}; inspect before retrying",
            dest.display()
        )
    })?;
    println!(
        "Created {}. Desktop preview, licensed wallpaper and live testing remain pending.",
        dest.display()
    );
    Ok(())
}
fn walk(
    root: &Path,
    dir: &Path,
    errors: &mut Vec<String>,
    warnings: &mut Vec<String>,
    total: &mut u64,
) -> io::Result<()> {
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let p = entry.path();
        let rel = p.strip_prefix(root).unwrap();
        if rel == Path::new(".git") {
            continue;
        }
        let meta = fs::symlink_metadata(&p)?;
        if meta.file_type().is_symlink() {
            errors.push(format!("symlink: {}", rel.display()));
            continue;
        }
        if meta.is_dir() {
            walk(root, &p, errors, warnings, total)?;
        } else if meta.is_file() {
            *total = total.saturating_add(meta.len());
            if dir == root {
                let name = entry.file_name();
                let name = name.to_string_lossy();
                if DENIED.contains(&name.as_ref()) || name.ends_with(".lua") {
                    warnings.push(format!("ignored by Git-installed theme staging: {name}"));
                }
            }
        } else {
            errors.push(format!("not a regular file: {}", rel.display()));
        }
    }
    Ok(())
}
fn check(root: &Path, release: bool) -> Result<(), String> {
    let meta = fs::symlink_metadata(root).map_err(|e| e.to_string())?;
    if !meta.is_dir() || meta.file_type().is_symlink() {
        return Err("check a real source directory, not a symlink".into());
    }
    let mut errors = Vec::new();
    let mut warnings = Vec::new();
    let mut total = 0;
    walk(root, root, &mut errors, &mut warnings, &mut total).map_err(|e| e.to_string())?;
    if total > 400 * 1024 * 1024 {
        errors.push("working tree exceeds 400 MiB".into());
    }
    if !errors.is_empty() {
        return Err(errors.join("\n"));
    }
    // Refuse to read palette through a link, including when other findings exist.
    let p = root.join("colors.toml");
    let pm = fs::symlink_metadata(&p).map_err(|e| format!("colors.toml: {e}"))?;
    if !pm.is_file() || pm.file_type().is_symlink() || pm.len() > 1024 * 1024 {
        return Err("colors.toml must be a regular file <=1 MiB".into());
    }
    let values = palette(&fs::read_to_string(&p).map_err(|e| e.to_string())?)?;
    if !values.contains_key("mode") {
        warnings.push("mode undeclared; set dark or light explicitly".into());
    }
    for (a, b, min) in [
        ("foreground", "background", 4.5),
        ("foreground", "selection", 4.5),
        ("accent", "background", 3.0),
    ] {
        if let (Some(x), Some(y)) = (values.get(a), values.get(b)) {
            let c = contrast(x, y);
            println!("CONTRAST {a}/{b}: {c:.2}:1 (design target {min}:1)");
            if c < min {
                warnings.push(format!("review {a}/{b} contrast in actual use"));
            }
        }
    }
    if !root.join("backgrounds").is_dir() {
        warnings.push("backgrounds/ missing".into());
    } else if fs::read_dir(root.join("backgrounds"))
        .map_err(|e| e.to_string())?
        .next()
        .is_none()
    {
        warnings.push("no wallpaper supplied".into());
    }
    if release && !root.join("preview.png").is_file() {
        errors.push("recommended release profile requires root preview.png; other registry preview formats require upstream validation".into());
    }
    for w in warnings {
        println!("WARN {w}");
    }
    println!("NOT CHECKED: image decoding/dimensions, media rights, reserved/taken names, live rendering, upstream registry acceptance.");
    if errors.is_empty() {
        println!("PASS: local authoring subset only");
        Ok(())
    } else {
        Err(errors.join("\n"))
    }
}
fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().skip(1).collect();
    match args.as_slice() {
        [cmd, path] if cmd == "scaffold" => scaffold(Path::new(path)),
        [cmd, path] if cmd == "check" => check(Path::new(path), false),
        [cmd, path, flag] if cmd == "check" && flag == "--release" => check(Path::new(path), true),
        [cmd, path, manifest] if cmd == "snapshot" => handoff::snapshot(Path::new(path), manifest, false),
        [cmd, path, manifest, flag] if cmd == "snapshot" && flag == "--implementation" => handoff::snapshot(Path::new(path), manifest, true),
        [cmd, path, manifest] if cmd == "handoff" => handoff::check(Path::new(path), manifest),
        _ => Err("usage: omarchy-theme-tool scaffold DIR | check DIR [--release] | snapshot DIR evidence/NAME.manifest [--implementation] | handoff DIR evidence/DELIVERY.manifest".into()),
    }
}
fn main() {
    if let Err(e) = run() {
        eprintln!("ERROR: {e}");
        process::exit(1);
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn starter_is_complete() {
        let p = palette(STARTER).unwrap();
        assert_eq!(p.len(), 26);
        assert!(contrast(&p["foreground"], &p["background"]) >= 4.5);
    }
    #[test]
    fn black_white_contrast() {
        assert!((contrast("#000000", "#ffffff") - 21.).abs() < 0.0001);
    }
    #[test]
    fn equal_colours() {
        assert!((contrast("#123456", "#123456") - 1.).abs() < 0.0001);
    }
    #[test]
    fn duplicates_fail() {
        assert!(palette(&format!("{STARTER}\naccent = \"#123456\"\n"))
            .unwrap_err()
            .contains("duplicate"));
    }
    #[test]
    fn bad_hex_and_utf8_fail() {
        for c in ["#12345z", "#ééé", "1234567", "#123"] {
            assert!(rgb(c).is_none());
        }
    }
    #[test]
    fn comments_work() {
        assert!(palette(&STARTER.replace("mode = \"dark\"", "mode = 'dark' # explicit")).is_ok());
    }
    #[test]
    fn suffix_input_fails() {
        assert!(palette(&STARTER.replace("mode = \"dark\"", "mode = \"dark\" junk")).is_err());
    }
    #[test]
    fn nested_tables_fail() {
        assert!(palette(&format!("[palette]\n{STARTER}")).is_err());
    }
    #[test]
    fn required_key_fails() {
        assert!(palette(&STARTER.replace("accent = \"#9bbf94\"", "")).is_err());
    }
    #[test]
    fn slug_safety() {
        for s in ["../x", "-x", "a/b", "a;b", "", "École"] {
            assert!(!slug_ok(s));
        }
        assert!(slug_ok("moss-2"));
    }
}
