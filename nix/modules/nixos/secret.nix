{ flake, ... }:
{
  lib,
  config,
  pkgs,
  ...
}:
let
  inherit (lib)
    mkEnableOption
    mkOption
    types
    mkIf
    mkForce
    mkMerge
    makeBinPath
    ;
  cfg = config.services.helper-tools.secret;
  yaml = pkgs.formats.yaml { };
  helper-tools = "${flake.packages.${pkgs.stdenv.hostPlatform.system}.default}/bin/helper-tools";
in
{
  options.services.helper-tools.secret = {
    enable = mkEnableOption "Enable secret";
    dependencies = mkOption {
      type = with types; listOf str;
      default = [ "setupSecrets" ];
      description = "Activation script dependences to wait for.";
    };
    settings = {
      file = mkOption {
        type = types.str;
        description = "Path to the source secrets file.";
      };
    };
  };

  config = mkIf cfg.enable {
    services.helper-tools.settings = cfg.secret.settings;
    system.activationScripts.helper-tools = {
      deps = cfg.secret.dependencies;
      text = ''
        export PATH=$PATH:${makeBinPath [ pkgs.podman ]}
        ${helper-tools} secret --file ${cfg.settings.file} || true
      '';
    };
  };
}
