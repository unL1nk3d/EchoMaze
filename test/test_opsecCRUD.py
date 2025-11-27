import unittest
from unittest.mock import MagicMock
from GATHERINGDB.crud_mitre import CRUD_OPSEC
from GATHERINGDB.model import Opsec_logs, Actions
from GATHERINGDB.log import log


class TestCRUDOpsec(unittest.TestCase):
    def setUp(self):
        self.mock_dao = MagicMock()
        self.crud_opsec = CRUD_OPSEC()

    def test_insert_opsec_log_success(self):
        """Test inserción exitosa de un registro OPSEC"""
        mock_action = MagicMock(spec=Actions)
        mock_action.id = 1
        self.mock_dao.seleccionar.return_value = [mock_action]

        result = self.crud_opsec.insert_opsec_log(
            action_id=1,
            event="scan_completed",
            severity=2,
            details="Network scan completed successfully",
            dao=self.mock_dao
        )

        self.mock_dao.insertar.assert_called_once()
        inserted_log = self.mock_dao.insertar.call_args[0][0]
        self.assertIsInstance(inserted_log, Opsec_logs)
        self.assertEqual(inserted_log.action_id, 1)
        self.assertEqual(inserted_log.event, "scan_completed")
        self.assertEqual(inserted_log.severity, 2)
        self.assertEqual(inserted_log.details, "Network scan completed successfully")

    def test_insert_opsec_log_action_not_found(self):
        """Test inserción de log OPSEC cuando la acción no existe"""
        self.mock_dao.seleccionar.return_value = []

        with self.assertRaises(ValueError) as context:
            self.crud_opsec.insert_opsec_log(
                action_id=999,
                event="scan_failed",
                severity=3,
                details="Action not found",
                dao=self.mock_dao
            )
        self.assertIn("No Action found", str(context.exception))

    def test_insert_opsec_log_minimal_fields(self):
        """Test inserción de log OPSEC con campos mínimos"""
        mock_action = MagicMock(spec=Actions)
        mock_action.id = 1
        self.mock_dao.seleccionar.return_value = [mock_action]

        result = self.crud_opsec.insert_opsec_log(
            action_id=1,
            event="action_executed",
            severity=1,
            dao=self.mock_dao
        )

        inserted_log = self.mock_dao.insertar.call_args[0][0]
        self.assertEqual(inserted_log.event, "action_executed")
        self.assertEqual(inserted_log.severity, 1)
        self.assertEqual(inserted_log.details, "")

    def test_insert_opsec_log_db_error(self):
        """Test inserción de log OPSEC con error de BD"""
        mock_action = MagicMock(spec=Actions)
        self.mock_dao.seleccionar.return_value = [mock_action]
        self.mock_dao.insertar.side_effect = Exception("DB connection error")

        with self.assertRaises(Exception):
            self.crud_opsec.insert_opsec_log(
                action_id=1,
                event="scan_completed",
                severity=2,
                dao=self.mock_dao
            )

    def test_select_all_opsec_logs_success(self):
        """Test obtener todos los registros OPSEC"""
        mock_logs = [
            MagicMock(spec=Opsec_logs, id=1, action_id=1, event="scan_started", severity=1),
            MagicMock(spec=Opsec_logs, id=2, action_id=1, event="scan_completed", severity=2),
            MagicMock(spec=Opsec_logs, id=3, action_id=2, event="error_occurred", severity=3),
        ]
        self.mock_dao.seleccionar.return_value = mock_logs

        result = self.crud_opsec.select_all_opsec_logs(dao=self.mock_dao)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].event, "scan_started")
        self.assertEqual(result[2].event, "error_occurred")
        self.mock_dao.seleccionar.assert_called_once_with(Opsec_logs)

    def test_select_all_opsec_logs_empty(self):
        """Test obtener logs OPSEC cuando no hay"""
        self.mock_dao.seleccionar.return_value = []

        result = self.crud_opsec.select_all_opsec_logs(dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_select_all_opsec_logs_db_error(self):
        """Test obtener logs OPSEC con error de BD"""
        self.mock_dao.seleccionar.side_effect = Exception("DB error")

        result = self.crud_opsec.select_all_opsec_logs(dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_select_opsec_logs_by_action_success(self):
        """Test obtener logs OPSEC de una acción específica"""
        mock_logs = [
            MagicMock(spec=Opsec_logs, id=1, action_id=1, event="scan_started", severity=1),
            MagicMock(spec=Opsec_logs, id=2, action_id=2, event="scan_completed", severity=2),
            MagicMock(spec=Opsec_logs, id=3, action_id=1, event="error_occurred", severity=3),
        ]
        self.mock_dao.seleccionar.return_value = mock_logs

        result = self.crud_opsec.select_opsec_logs_by_action(action_id=1, dao=self.mock_dao)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(log.action_id == 1 for log in result))
        self.assertEqual(result[0].event, "scan_started")
        self.assertEqual(result[1].event, "error_occurred")

    def test_select_opsec_logs_by_action_not_found(self):
        """Test obtener logs OPSEC de una acción sin registros"""
        mock_logs = [
            MagicMock(spec=Opsec_logs, id=1, action_id=1, event="scan_started", severity=1),
        ]
        self.mock_dao.seleccionar.return_value = mock_logs

        result = self.crud_opsec.select_opsec_logs_by_action(action_id=999, dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_select_opsec_logs_by_severity_low(self):
        """Test obtener logs OPSEC por severidad baja"""
        mock_logs = [
            MagicMock(spec=Opsec_logs, id=1, action_id=1, event="scan_started", severity=1),
            MagicMock(spec=Opsec_logs, id=2, action_id=1, event="scan_completed", severity=2),
            MagicMock(spec=Opsec_logs, id=3, action_id=2, event="info_event", severity=1),
        ]
        self.mock_dao.seleccionar.return_value = mock_logs

        result = self.crud_opsec.select_opsec_logs_by_severity(severity=1, dao=self.mock_dao)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(log.severity == 1 for log in result))

    def test_select_opsec_logs_by_severity_high(self):
        """Test obtener logs OPSEC por severidad alta (crítico)"""
        mock_logs = [
            MagicMock(spec=Opsec_logs, id=1, action_id=1, event="scan_started", severity=1),
            MagicMock(spec=Opsec_logs, id=2, action_id=2, event="critical_error", severity=5),
            MagicMock(spec=Opsec_logs, id=3, action_id=2, event="system_failure", severity=5),
        ]
        self.mock_dao.seleccionar.return_value = mock_logs

        result = self.crud_opsec.select_opsec_logs_by_severity(severity=5, dao=self.mock_dao)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(log.severity == 5 for log in result))

    def test_select_opsec_logs_by_severity_not_found(self):
        """Test obtener logs OPSEC por severidad inexistente"""
        mock_logs = [
            MagicMock(spec=Opsec_logs, id=1, action_id=1, event="event", severity=1),
        ]
        self.mock_dao.seleccionar.return_value = mock_logs

        result = self.crud_opsec.select_opsec_logs_by_severity(severity=99, dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_update_opsec_log_success(self):
        """Test actualización exitosa de un log OPSEC"""
        mock_log = MagicMock(spec=Opsec_logs)
        mock_log.id = 1
        mock_log.event = "scan_started"
        mock_log.severity = 1
        mock_log.details = "old details"

        self.mock_dao.seleccionar.return_value = [mock_log]

        self.crud_opsec.update_opsec_log(
            log_id=1,
            event="scan_updated",
            severity=2,
            details="new details",
            dao=self.mock_dao
        )

        self.assertEqual(mock_log.event, "scan_updated")
        self.assertEqual(mock_log.severity, 2)
        self.assertEqual(mock_log.details, "new details")
        self.mock_dao.actualizar.assert_called_once_with(mock_log, 1)

    def test_update_opsec_log_partial_fields(self):
        """Test actualización parcial de un log OPSEC"""
        mock_log = MagicMock(spec=Opsec_logs)
        mock_log.id = 1
        mock_log.event = "scan_started"
        mock_log.severity = 1
        mock_log.details = "original details"

        self.mock_dao.seleccionar.return_value = [mock_log]

        self.crud_opsec.update_opsec_log(
            log_id=1,
            severity=3,
            dao=self.mock_dao
        )

        self.assertEqual(mock_log.event, "scan_started")  # sin cambios
        self.assertEqual(mock_log.severity, 3)  # actualizado
        self.assertEqual(mock_log.details, "original details")  # sin cambios

    def test_update_opsec_log_not_found(self):
        """Test actualización de log OPSEC inexistente"""
        self.mock_dao.seleccionar.return_value = []

        with self.assertRaises(ValueError) as context:
            self.crud_opsec.update_opsec_log(
                log_id=999,
                event="new_event",
                dao=self.mock_dao
            )
        self.assertIn("No OPSEC log found", str(context.exception))

    def test_update_opsec_log_only_event(self):
        """Test actualización solo del evento de un log OPSEC"""
        mock_log = MagicMock(spec=Opsec_logs)
        mock_log.id = 1
        mock_log.event = "scan_started"
        mock_log.severity = 1
        mock_log.details = "details"

        self.mock_dao.seleccionar.return_value = [mock_log]

        self.crud_opsec.update_opsec_log(
            log_id=1,
            event="scan_completed",
            dao=self.mock_dao
        )

        self.assertEqual(mock_log.event, "scan_completed")
        self.assertEqual(mock_log.severity, 1)  # sin cambios
        self.assertEqual(mock_log.details, "details")  # sin cambios

    def test_delete_opsec_log_success(self):
        """Test eliminación exitosa de un log OPSEC"""
        mock_log = MagicMock(spec=Opsec_logs)
        mock_log.id = 1
        self.mock_dao.seleccionar.return_value = [mock_log]

        self.crud_opsec.delete_opsec_log(log_id=1, dao=self.mock_dao)

        self.mock_dao.eliminar.assert_called_once_with(mock_log, 1)

    def test_delete_opsec_log_not_found(self):
        """Test eliminación de log OPSEC inexistente"""
        self.mock_dao.seleccionar.return_value = []

        with self.assertRaises(ValueError) as context:
            self.crud_opsec.delete_opsec_log(log_id=999, dao=self.mock_dao)
        self.assertIn("No OPSEC log found", str(context.exception))

    def test_delete_opsec_log_db_error(self):
        """Test eliminación de log OPSEC con error de BD"""
        mock_log = MagicMock(spec=Opsec_logs)
        mock_log.id = 1
        self.mock_dao.seleccionar.return_value = [mock_log]
        self.mock_dao.eliminar.side_effect = Exception("DB error")

        with self.assertRaises(Exception):
            self.crud_opsec.delete_opsec_log(log_id=1, dao=self.mock_dao)

    def test_insert_opsec_log_high_severity(self):
        """Test inserción de log OPSEC con alta severidad"""
        mock_action = MagicMock(spec=Actions)
        mock_action.id = 1
        self.mock_dao.seleccionar.return_value = [mock_action]

        result = self.crud_opsec.insert_opsec_log(
            action_id=1,
            event="critical_security_breach",
            severity=5,
            details="Unauthorized access detected",
            dao=self.mock_dao
        )

        inserted_log = self.mock_dao.insertar.call_args[0][0]
        self.assertEqual(inserted_log.severity, 5)
        self.assertEqual(inserted_log.event, "critical_security_breach")

    def test_select_opsec_logs_mixed_actions_and_severities(self):
        """Test obtener logs OPSEC con múltiples acciones y severidades"""
        mock_logs = [
            MagicMock(spec=Opsec_logs, id=1, action_id=1, event="event1", severity=1),
            MagicMock(spec=Opsec_logs, id=2, action_id=2, event="event2", severity=2),
            MagicMock(spec=Opsec_logs, id=3, action_id=1, event="event3", severity=3),
            MagicMock(spec=Opsec_logs, id=4, action_id=3, event="event4", severity=1),
        ]
        self.mock_dao.seleccionar.return_value = mock_logs

        # Obtener logs de acción 1
        result_action = self.crud_opsec.select_opsec_logs_by_action(action_id=1, dao=self.mock_dao)
        self.assertEqual(len(result_action), 2)

        # Obtener logs de severidad 1
        result_severity = self.crud_opsec.select_opsec_logs_by_severity(severity=1, dao=self.mock_dao)
        self.assertEqual(len(result_severity), 2)


if __name__ == '__main__':
    unittest.main()