use zed_extension_api::{self as zed, Command, Extension, LanguageServerId, Result, Worktree};

struct SerpentVyperExtension;

impl Extension for SerpentVyperExtension {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        _language_server_id: &LanguageServerId,
        _worktree: &Worktree,
    ) -> Result<Command> {
        // Détecter si flatpak-spawn est disponible (via command -v dans un shell)
        let has_flatpak = std::process::Command::new("sh")
            .arg("-c")
            .arg("command -v flatpak-spawn >/dev/null 2>&1")
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false);

        if has_flatpak {
            Ok(Command {
                command: "flatpak-spawn".to_string(),
                args: vec!["--host".to_string(), "serpent-lsp".to_string()],
                env: vec![],
            })
        } else {
            Ok(Command {
                command: "serpent-lsp".to_string(),
                args: vec![],
                env: vec![],
            })
        }
    }
}

zed::register_extension!(SerpentVyperExtension);
