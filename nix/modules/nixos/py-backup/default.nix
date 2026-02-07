{ lib, ... }:
let
  inherit (lib) mkEnableOption mkOption types;
in
{
  imports = [ ./config.nix ];
  options.services.py-backup = {
    enable = mkEnableOption "Enable system backup services.";
    interval = mkOption {
      type = types.str;
      description = "Run backup services at this interval.";
    };
    settings = {
      services = mkOption {
        type = types.listOf types.str;
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
          type = types.listOf types.str;
          default = [ ];
          description = "A list of zfs datasets that will be backed up.";
        };
      };
    };
    restic = {
      repository = mkOption {
        type = types.str;
        description = "The repository to use for restic backup.";
      };
      secrets = {
        password = mkOption {
          type = types.str;
          default = "restic/password";
          description = "The secret reference to use for the restic password";
        };
        accessKey = mkOption {
          type = types.str;
          default = "restic/access_key";
          description = "The secret reference to use for the s3 access key.";
        };
        secretKey = mkOption {
          type = types.str;
          default = "restic/secret_key";
          description = "The secret reference to use for the s3 secret key.";
        };
      };
      retention = {
        days = mkOption {
          type = types.int;
          description = "The amount of days to keep snapshots and backups for";
        };
        weeks = mkOption {
          type = types.int;
          description = "The amount of weeks to keep snapshots and backups for";
        };
      };
      statusFile = mkOption {
        type = types.str;
        default = "/var/lib/resticprofile/status.json";
        description = "The file where resticprofile's status will be written to.";
      };
    };
  };
}
