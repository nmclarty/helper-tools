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
    ;
  cfg = config.services.py-backup;
  toml = pkgs.formats.toml { };
in
{
  options.services.py-backup = {
    enable = mkEnableOption "Enable system backup services.";
    interval = mkOption {
      type = types.str;
      description = "Run backup services at this interval.";
    };
    command = mkOption {
      type = with types; listOf str;
      description = "Wrapped backup command to run (should be absolute path)";
    };
    settings = {
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

  config = mkIf cfg.enable {
    systemd = {
      tmpfiles.rules = [ "d ${cfg.settings.zpool.directory}" ];
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
          environment = {
            PYTHONUNBUFFERED = "1"; # otherwise stdout is delayed
            PY_BACKUP_CONFIG_FILE = "${toml.generate "py-backup-config.toml" cfg.settings}";
            PY_BACKUP_COMMAND = "${builtins.toJSON cfg.command}";
          };
          serviceConfig = {
            Type = "oneshot";
            ExecStart = "${flake.packages.${pkgs.stdenv.hostPlatform.system}.default}/bin/py-backup";
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
            OnCalendar = cfg.interval;
            Persistent = true;
          };
        };
      };
    };
  };
}
