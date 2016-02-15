#!/usr/bin/env nix-shell

with import <nixpkgs> {};
with pkgs.python27Packages;

buildPythonPackage { 
  name = "jugEnv";
  buildInputs = [
    git
    python27Full
    python27Packages.virtualenv
    python27Packages.setuptools
    python27Packages.pyyaml
    python27Packages.numpy
    python27Packages.nose
    python27Packages.six
    stdenv
    zlib
  ];
  src = null;
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
