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
  cfg = config.services.helper-tools;
  yaml = pkgs.formats.yaml { };
  helper-tools = "${flake.packages.${pkgs.stdenv.hostPlatform.system}.default}/bin/helper-tools";
in
{
  _file = "helper-tools.nix";
  options.services.helper-tools = {
    backup = {
      enable = mkEnableOption "Enable backup";
      interval = mkOption {
        type = types.str;
        description = "Run backup services at this interval.";
      };
      settings = {
        command = mkOption {
          type = with types; listOf str;
          description = "Wrapped backup command to run (should be absolute path)";
        };
        services = mkOption {
          type = with types; listOf str;
          default = [ ];
          description = "A list of systemd services to be stopped for snapshotting.";
        };
        zpool = {
          name = mkOption {
            type = types.str;
            description = "The zpool that contains all the datasets to be backed up.";
          };
          directory = mkOption {
            type = types.str;
            default = "/.backup";
            description = "The directory that snapshots will be mounted into for backup.";
          };
          datasets = mkOption {
            type = with types; listOf str;
            default = [ ];
            description = "A list of zfs datasets that will be backed up.";
          };
        };
      };
    };
    secret = {
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
    settings = mkOption {
      type = yaml.type;
      default = { };
      description = "The final configuration for helper-tools/config.yaml.";
    };
  };

  config = mkMerge [
    {
      environment.etc."helper-tools/config.yaml".source =
        yaml.generate "helper-tools-config.yaml" cfg.settings;
    }

    (mkIf cfg.backup.enable {
      services.helper-tools.settings = cfg.backup.settings;
      systemd = {
        tmpfiles.rules = [ "d ${cfg.backup.settings.zpool.directory}" ];
        services = {
          # otherwise starting sanoid with systemd won't wait for completion
          sanoid.serviceConfig.Type = "oneshot";
          backup = {
            description = "Snapshot disks and backup";
            after = [
              "network-online.target"
              "zfs.target"
            ];
            requires = [
              "network-online.target"
              "zfs.target"
            ];
            path = with pkgs; [
              zfs
              util-linux
            ];
            environment.PYTHONUNBUFFERED = "1"; # otherwise stdout is delayed
            serviceConfig = {
              Type = "oneshot";
              ExecStart = "${helper-tools} backup";
            };
          };
        };
        timers = {
          # since we're triggering sanoid manually, disable its timer
          sanoid.enable = mkForce false;
          backup = {
            enable = true;
            wantedBy = [ "timers.target" ];
            timerConfig = {
              OnCalendar = cfg.backup.interval;
              Persistent = true;
            };
          };
        };
      };
    })

    (mkIf cfg.secret.enable {
      services.helper-tools.settings = cfg.secret.settings;
      system.activationScripts.helper-tools = {
        deps = cfg.secret.dependencies;
        text = ''
          export PATH=$PATH:${makeBinPath [ pkgs.podman ]}
          ${helper-tools} secret || true
        '';
      };
    })
  ];
}
