{ inputs, ... }:
with inputs.nixpkgs.lib;
{
  # Creates a system user and group, commonly used for container users.
  # - name (The name of the user)
  # - id (The uid/gid of the user)
  mkContainerUser = { name, id }: {
    users.${name} = {
      isSystemUser = true;
      description = "${name} container user";
      group = name;
      uid = id;
    };
    groups.${name}.gid = id;
  };

  # Creates multiple option sets, for each container passed.
  # - apps (a list of containers)
  mkContainerOptions = apps: builtins.listToAttrs (
    map
      ({ id, name, tag }: {
        inherit name;
        value = {
          enable = mkEnableOption "Enable ${name}";
          tag = mkOption {
            type = types.str;
            default = tag;
            description = "The image tag to use.";
          };
          user = {
            name = mkOption {
              type = types.str;
              default = name;
              description = "The user to create and use for ${name}.";
            };
            id = mkOption {
              type = types.int;
              default = id;
              description = "The uid/gid for the user.";
            };
          };
        };
      })
      apps
  );

  # Creates a list of systemd dependencies for a quadlet container.
  # - deps (a list of service names to depend on)
  mkContainerDeps = deps:
    let
      services = map (dep: "${dep}.service") deps;
    in
    {
      Requires = services;
      After = services;
    };

  # Creates multiple sops-nix secrets based on the keys and then input file.
  # - keys (a list of the keys to create secrets for)
  # - sopsFile (a string containing the path to the secret file)
  mkSecrets = keys: sopsFile:
    builtins.listToAttrs (
      map
        (key: {
          name = key;
          value = {
            inherit key sopsFile;
          };
        })
        keys
    );
}
