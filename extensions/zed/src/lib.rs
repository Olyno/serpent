use zed_extension_api::{self as zed, Command, Extension, LanguageServerId, Result, Worktree};

struct SerpentVyperExtension;

impl Extension for SerpentVyperExtension {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &LanguageServerId,
        worktree: &Worktree,
    ) -> Result<Command> {
        // Detect if flatpak-spawn is available
        let has_flatpak = std::process::Command::new("sh")
            .arg("-c")
            .arg("command -v flatpak-spawn >/dev/null 2>&1")
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false);

        if has_flatpak {
            Ok(Command {
                command: "/usr/bin/flatpak-spawn".into(),
                args: vec!["--host".into(), "serpent-lsp".into()],
                env: vec![],
            })
        } else {
            // Resolve serpent-lsp in PATH to get an absolute path
            let lsp_path = worktree
                .which("serpent-lsp")
                .unwrap_or_else(|| "serpent-lsp".to_string());
            Ok(Command {
                command: lsp_path,
                args: vec![],
                env: vec![],
            })
        }
    }
}

zed::register_extension!(SerpentVyperExtension);
