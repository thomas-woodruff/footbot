{ stdenv
, buildPythonPackage
, fetchPypi
, freezegun
, google_resumable_media
, google_api_core
, google_cloud_core
, pandas
, pyarrow
, fastavro
, pytest
, mock
, ipython
}:

buildPythonPackage rec {
  pname = "google-cloud-bigquery-storage";
  version = "1.0.0";

  src = fetchPypi {
    inherit pname version;
    sha256 = "1qy8h0ji21fqnjbv1rcxjzjqs6z76k4j1p993imppyb6rmqnp5rx";
  };

  checkInputs = [ pytest mock ipython freezegun ];
  propagatedBuildInputs = [ google_resumable_media google_api_core google_cloud_core pandas pyarrow fastavro ];

  doCheck = false;

  meta = with stdenv.lib; {
    description = "Google BigQuery API client library";
    homepage = "https://github.com/GoogleCloudPlatform/google-cloud-python";
    license = licenses.asl20;
    maintainers = [ maintainers.costrouc ];
  };
}