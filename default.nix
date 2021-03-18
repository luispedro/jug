#!/usr/bin/env nix-shell

with import <nixpkgs> {};
{ python ? python27, pythonPackages ? pkgs.python27Packages }:

let
  version = "1.2.1";
in

pythonPackages.buildPythonPackage {
  name = "jug-${version}";
  buildInputs = [
    pythonPackages.pytest
  ];
  propagatedBuildInputs = [
    python
    pythonPackages.virtualenv
    pythonPackages.setuptools
    pythonPackages.pyyaml
    pythonPackages.numpy
    pythonPackages.redis

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
