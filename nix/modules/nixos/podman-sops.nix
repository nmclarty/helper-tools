{ lib, config, perSystem, pkgs, ... }:
let
  inherit (lib) mkEnableOption mkOption types mkIf makeBinPath;
  cfg = config.services.podman-sops;
in
{
  options.services.podman-sops = {
    enable = mkEnableOption "Enable syncing podman secrets from sops-nix.";
    settings.sopsFile = mkOption {
      type = types.str;
      description = "The path to the encrypted (source) sops file.";
    };
  };
  config = mkIf cfg.enable {
    sops.secrets."podman-sops.yaml" = {
      inherit (cfg.settings) sopsFile;
      key = "";
    };
    system.activationScripts.podman-sops = {
      deps = [ "setupSecrets" ];
      text = ''
        export PATH=$PATH:${makeBinPath [ pkgs.podman ]}
        ${perSystem.helper-tools.default}/bin/podman_sops \
          --secret-file '${config.sops.secrets."podman-sops.yaml".path}' || true
      '';
    };
  };
}
