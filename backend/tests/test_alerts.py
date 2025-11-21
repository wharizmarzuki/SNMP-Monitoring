"""
Integration tests for alert workflow
"""
import pytest
from fastapi import status


@pytest.mark.integration
@pytest.mark.alert
class TestAlertWorkflow:
    """Test alert state machine and workflow"""

    def test_alert_state_transitions(self, client, sample_device):
        """Test alert state transitions: clear -> triggered -> acknowledged -> clear"""
        # Initial state should be clear
        response = client.get(f"/device/{sample_device.ip_address}")
        assert response.json()["cpu_alert_state"] == "clear"

        # Acknowledge when in clear state
        response = client.put(
            f"/device/{sample_device.ip_address}/alert/cpu/acknowledge"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "acknowledged"

        # Resolve from acknowledged state
        response = client.put(
            f"/device/{sample_device.ip_address}/alert/cpu/resolve"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "clear"

    def test_acknowledge_cpu_alert(self, client, sample_device):
        """Test acknowledging CPU alert"""
        response = client.put(
            f"/device/{sample_device.ip_address}/alert/cpu/acknowledge"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "state" in data
        assert "acknowledged_at" in data
        assert data["state"] == "acknowledged"

    def test_acknowledge_memory_alert(self, client, sample_device):
        """Test acknowledging memory alert"""
        response = client.put(
            f"/device/{sample_device.ip_address}/alert/memory/acknowledge"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "acknowledged"

    def test_acknowledge_reachability_alert(self, client, sample_device):
        """Test acknowledging reachability alert"""
        response = client.put(
            f"/device/{sample_device.ip_address}/alert/reachability/acknowledge"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "acknowledged"

    def test_resolve_cpu_alert(self, client, sample_device):
        """Test resolving CPU alert"""
        # First acknowledge
        client.put(f"/device/{sample_device.ip_address}/alert/cpu/acknowledge")

        # Then resolve
        response = client.put(
            f"/device/{sample_device.ip_address}/alert/cpu/resolve"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "clear"

    def test_resolve_memory_alert(self, client, sample_device):
        """Test resolving memory alert"""
        # First acknowledge
        client.put(f"/device/{sample_device.ip_address}/alert/memory/acknowledge")

        # Then resolve
        response = client.put(
            f"/device/{sample_device.ip_address}/alert/memory/resolve"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "clear"

    def test_alert_not_found(self, client):
        """Test acknowledging alert for non-existent device"""
        response = client.put("/device/192.168.99.99/alert/cpu/acknowledge")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_interface_alert_acknowledge(self, client, sample_device, sample_interface):
        """Test acknowledging interface alert"""
        response = client.put(
            f"/device/{sample_device.ip_address}/interface/{sample_interface.if_index}/alert/status/acknowledge"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "state" in data

    def test_interface_alert_resolve(self, client, sample_device, sample_interface):
        """Test resolving interface alert"""
        # First acknowledge
        client.put(
            f"/device/{sample_device.ip_address}/interface/{sample_interface.if_index}/alert/status/acknowledge"
        )

        # Then resolve
        response = client.put(
            f"/device/{sample_device.ip_address}/interface/{sample_interface.if_index}/alert/status/resolve"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["state"] == "clear"

    def test_alert_response_format(self, client, sample_device):
        """Test that alert responses follow standard format"""
        response = client.put(
            f"/device/{sample_device.ip_address}/alert/cpu/acknowledge"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify required fields
        required_fields = ["message", "state", "acknowledged_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


@pytest.mark.integration
class TestRecipientEndpoints:
    """Test alert recipient management"""

    def test_get_recipients_empty(self, client):
        """Test getting recipients when none exist"""
        response = client.get("/recipients/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_create_recipient(self, client):
        """Test creating a new recipient"""
        response = client.post(
            "/recipients/",
            json={"email": "newrecipient@example.com"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newrecipient@example.com"
        assert "id" in data

    def test_create_duplicate_recipient(self, client, sample_recipient):
        """Test creating a recipient with duplicate email"""
        response = client.post(
            "/recipients/",
            json={"email": sample_recipient.email}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_all_recipients(self, client, sample_recipient):
        """Test getting all recipients"""
        response = client.get("/recipients/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(r["email"] == sample_recipient.email for r in data)

    def test_delete_recipient(self, client, sample_recipient):
        """Test deleting a recipient"""
        response = client.delete(f"/recipients/{sample_recipient.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion
        response = client.get("/recipients/")
        data = response.json()
        assert not any(r["id"] == sample_recipient.id for r in data)

    def test_delete_nonexistent_recipient(self, client):
        """Test deleting a non-existent recipient"""
        response = client.delete("/recipients/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
