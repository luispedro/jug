#!/usr/bin/env nix-shell

with import <nixpkgs> {};

let
  version = "1.2.1";
in

buildPythonPackage {
  name = "jug-${version}";
  buildInputs = with pkgs.python27Packages; [
    python27Full
    python27Packages.virtualenv
    python27Packages.setuptools
    python27Packages.pyyaml
    python27Packages.numpy
    python27Packages.nose
    python27Packages.redis
    python27Packages.six

    zlib
  ];
  src = ./.;
  # When used as `nix-shell --pure`
  shellHook = ''
  unset http_proxy
  export GIT_SSL_CAINFO=/etc/ssl/certs/ca-bundle.crt
  '';
  # used when building environments
  extraCmds = ''
  unset http_proxy # otherwise downloads will fail ("nodtd.invalid")
  export GIT_SSL_CAINFO=/etc/ssl/certs/ca-bundle.crt
  '';
}
