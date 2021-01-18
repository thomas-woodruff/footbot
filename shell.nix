with (import <nixpkgs> { });

let
  python3_ = python3.override {
    packageOverrides = self: super: {

      fastavro = super.callPackage ./nix/fastavro.nix { };
      google_cloud_bigquery_storage = super.callPackage ./nix/google_cloud_bigquery_storage.nix { };

      # broken test
      pyarrow = super.pyarrow.overrideAttrs (old: {
        postPatch = ''
          rm pyarrow/tests/test_pandas.py
        '';
      });
    };
  };

  interpreter = (python3_.withPackages (ps: with ps; [
      setuptools
      numpy
      pandas
      tables
      requests
      flask
      unidecode
      cvxpy
      scikitlearn
      google_cloud_bigquery
      google_cloud_tasks
      google_cloud_bigquery_storage
      click

      pytest
      isort
      black
      flake8
  ]));

in mkShell {

  buildInputs = [
    interpreter
  ];

  shellHook = ''
    rm -rf venv
    ln -s ${interpreter} venv
  '';

}
