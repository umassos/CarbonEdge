import pytest
import requests

from src.sinfonia.carbonedge_fetcher import RealTimeFetcher


class TestRealTimeCarbonIntensityFetcher:
    def setup_method(self):
        self.token = "test-token"
        self.coord = (52.52, 13.405)  # Berlin

    def test_fetch_success_with_coordinates(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"carbonIntensity": 123.4}
        mock_resp.raise_for_status = mocker.Mock()

        mock_get = mocker.patch("requests.get", return_value=mock_resp)

        fetcher = RealTimeFetcher(self.token, self.coord)
        result = fetcher.fetch()

        assert result == 123.4
        mock_get.assert_called_once_with(
            fetcher.ELECTRICITY_MAP_CARBON_INTENSITY_URL,
            headers={"auth-token": self.token},
            params={"lat": 52.52, "lon": 13.405}
        )

    def test_fetch_success_without_coordinates(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"carbonIntensity": 99.9}
        mock_resp.raise_for_status = mocker.Mock()

        mock_get = mocker.patch("requests.get", return_value=mock_resp)

        fetcher = RealTimeFetcher(self.token, None)
        result = fetcher.fetch()

        assert result == 99.9
        mock_get.assert_called_once_with(
            fetcher.ELECTRICITY_MAP_CARBON_INTENSITY_URL,
            headers={"auth-token": self.token},
            params={}
        )

    def test_fetch_raises_http_error(self, mocker):
        mock_resp = mocker.Mock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")

        mock_get = mocker.patch("requests.get", return_value=mock_resp)

        fetcher = RealTimeFetcher(self.token, self.coord)

        with pytest.raises(requests.HTTPError):
            fetcher.fetch()
