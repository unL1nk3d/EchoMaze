import unittest
from unittest.mock import MagicMock
from GATHERINGDB.crud_mitre import CRUD_ARTIFACTS
from GATHERINGDB.model import Artifacts, IPNode
from GATHERINGDB.log import log


class TestCRUDArtifacts(unittest.TestCase):
    def setUp(self):
        self.mock_dao = MagicMock()
        self.crud_artifacts = CRUD_ARTIFACTS()

    def test_insert_artifact_success(self):
        """Test inserción exitosa de un artefacto"""
        mock_node = MagicMock(spec=IPNode)
        mock_node.id = 1
        self.mock_dao.seleccionarPorId.return_value = mock_node

        result = self.crud_artifacts.insert_artifact(
            filename="scan_results.xml",
            node_id=1,
            sha1="da39a3ee5e6b4b0d3255bfef95601890afd80709",
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            md5="d41d8cd98f00b204e9800998ecf8427e",
            size=2048,
            notes="nmap scan results",
            dao=self.mock_dao
        )

        self.mock_dao.insertar.assert_called_once()
        inserted_artifact = self.mock_dao.insertar.call_args[0][0]
        self.assertIsInstance(inserted_artifact, Artifacts)
        self.assertEqual(inserted_artifact.filename, "scan_results.xml")
        self.assertEqual(inserted_artifact.node_id, 1)
        self.assertEqual(inserted_artifact.size, 2048)
        self.assertEqual(inserted_artifact.sha256, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_insert_artifact_node_not_found(self):
        """Test inserción de artefacto cuando el nodo no existe"""
        self.mock_dao.seleccionarPorId.return_value = None

        with self.assertRaises(ValueError) as context:
            self.crud_artifacts.insert_artifact(
                filename="scan_results.xml",
                node_id=999,
                sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                size=2048,
                dao=self.mock_dao
            )
        self.assertIn("No IPNode found", str(context.exception))

    def test_insert_artifact_db_error(self):
        """Test inserción de artefacto con error de BD"""
        mock_node = MagicMock(spec=IPNode)
        self.mock_dao.seleccionarPorId.return_value = mock_node
        self.mock_dao.insertar.side_effect = Exception("DB connection error")

        with self.assertRaises(Exception):
            self.crud_artifacts.insert_artifact(
                filename="scan_results.xml",
                node_id=1,
                sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                dao=self.mock_dao
            )

    def test_insert_artifact_minimal_fields(self):
        """Test inserción de artefacto con campos mínimos"""
        mock_node = MagicMock(spec=IPNode)
        mock_node.id = 1
        self.mock_dao.seleccionarPorId.return_value = mock_node

        result = self.crud_artifacts.insert_artifact(
            filename="report.txt",
            node_id=1,
            dao=self.mock_dao
        )

        self.mock_dao.insertar.assert_called_once()
        inserted_artifact = self.mock_dao.insertar.call_args[0][0]
        self.assertEqual(inserted_artifact.filename, "report.txt")
        self.assertEqual(inserted_artifact.sha1, "")
        self.assertEqual(inserted_artifact.size, 0)

    def test_select_all_artifacts_success(self):
        """Test obtener todos los artefactos"""
        mock_artifacts = [
            MagicMock(spec=Artifacts, id=1, filename="scan1.xml", node_id=1),
            MagicMock(spec=Artifacts, id=2, filename="scan2.xml", node_id=2),
            MagicMock(spec=Artifacts, id=3, filename="report.pdf", node_id=1),
        ]
        self.mock_dao.seleccionar.return_value = mock_artifacts

        result = self.crud_artifacts.select_all_artifacts(dao=self.mock_dao)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].filename, "scan1.xml")
        self.assertEqual(result[2].filename, "report.pdf")
        self.mock_dao.seleccionar.assert_called_once_with(Artifacts)

    def test_select_all_artifacts_empty(self):
        """Test obtener artefactos cuando no hay"""
        self.mock_dao.seleccionar.return_value = []

        result = self.crud_artifacts.select_all_artifacts(dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_select_all_artifacts_db_error(self):
        """Test obtener artefactos con error de BD"""
        self.mock_dao.seleccionar.side_effect = Exception("DB error")

        result = self.crud_artifacts.select_all_artifacts(dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_select_artifacts_by_node_success(self):
        """Test obtener artefactos de un nodo específico"""
        mock_artifacts = [
            MagicMock(spec=Artifacts, id=1, filename="scan1.xml", node_id=1),
            MagicMock(spec=Artifacts, id=2, filename="scan2.xml", node_id=2),
            MagicMock(spec=Artifacts, id=3, filename="report.pdf", node_id=1),
        ]
        self.mock_dao.seleccionar.return_value = mock_artifacts

        result = self.crud_artifacts.select_artifacts_by_node(node_id=1, dao=self.mock_dao)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(a.node_id == 1 for a in result))
        self.assertEqual(result[0].filename, "scan1.xml")
        self.assertEqual(result[1].filename, "report.pdf")

    def test_select_artifacts_by_node_not_found(self):
        """Test obtener artefactos de un nodo sin artefactos"""
        mock_artifacts = [
            MagicMock(spec=Artifacts, id=1, filename="scan1.xml", node_id=1),
        ]
        self.mock_dao.seleccionar.return_value = mock_artifacts

        result = self.crud_artifacts.select_artifacts_by_node(node_id=999, dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_select_artifact_by_hash_sha256(self):
        """Test obtener artefactos por SHA256"""
        sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        mock_artifacts = [
            MagicMock(spec=Artifacts, id=1, filename="scan1.xml", sha256=sha256, sha1="", md5=""),
            MagicMock(spec=Artifacts, id=2, filename="scan2.xml", sha256="different_hash", sha1="", md5=""),
        ]
        self.mock_dao.seleccionar.return_value = mock_artifacts

        result = self.crud_artifacts.select_artifact_by_hash(sha256, dao=self.mock_dao)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].filename, "scan1.xml")

    def test_select_artifact_by_hash_sha1(self):
        """Test obtener artefactos por SHA1"""
        sha1 = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        mock_artifacts = [
            MagicMock(spec=Artifacts, id=1, filename="scan1.xml", sha1=sha1, sha256="", md5=""),
            MagicMock(spec=Artifacts, id=2, filename="scan2.xml", sha1="different_hash", sha256="", md5=""),
        ]
        self.mock_dao.seleccionar.return_value = mock_artifacts

        result = self.crud_artifacts.select_artifact_by_hash(sha1, dao=self.mock_dao)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].filename, "scan1.xml")

    def test_select_artifact_by_hash_md5(self):
        """Test obtener artefactos por MD5"""
        md5 = "d41d8cd98f00b204e9800998ecf8427e"
        mock_artifacts = [
            MagicMock(spec=Artifacts, id=1, filename="scan1.xml", md5=md5, sha1="", sha256=""),
            MagicMock(spec=Artifacts, id=2, filename="scan2.xml", md5="different_hash", sha1="", sha256=""),
        ]
        self.mock_dao.seleccionar.return_value = mock_artifacts

        result = self.crud_artifacts.select_artifact_by_hash(md5, dao=self.mock_dao)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].filename, "scan1.xml")

    def test_select_artifact_by_hash_not_found(self):
        """Test obtener artefactos por hash inexistente"""
        mock_artifacts = [
            MagicMock(spec=Artifacts, id=1, filename="scan1.xml", sha256="hash1", sha1="hash2", md5="hash3"),
        ]
        self.mock_dao.seleccionar.return_value = mock_artifacts

        result = self.crud_artifacts.select_artifact_by_hash("nonexistent_hash", dao=self.mock_dao)

        self.assertEqual(result, [])

    def test_update_artifact_success(self):
        """Test actualización exitosa de un artefacto"""
        mock_artifact = MagicMock(spec=Artifacts)
        mock_artifact.id = 1
        mock_artifact.filename = "scan1.xml"
        mock_artifact.notes = "old notes"
        mock_artifact.size = 1024

        self.mock_dao.seleccionar.return_value = [mock_artifact]

        self.crud_artifacts.update_artifact(
            artifact_id=1,
            filename="scan_updated.xml",
            notes="updated notes",
            size=2048,
            dao=self.mock_dao
        )

        self.assertEqual(mock_artifact.filename, "scan_updated.xml")
        self.assertEqual(mock_artifact.notes, "updated notes")
        self.assertEqual(mock_artifact.size, 2048)
        self.mock_dao.actualizar.assert_called_once_with(mock_artifact, 1)

    def test_update_artifact_partial_fields(self):
        """Test actualización parcial de artefacto"""
        mock_artifact = MagicMock(spec=Artifacts)
        mock_artifact.id = 1
        mock_artifact.filename = "scan1.xml"
        mock_artifact.notes = "old notes"
        mock_artifact.sha256 = "old_hash"

        self.mock_dao.seleccionar.return_value = [mock_artifact]

        self.crud_artifacts.update_artifact(
            artifact_id=1,
            notes="new notes",
            dao=self.mock_dao
        )

        self.assertEqual(mock_artifact.filename, "scan1.xml")  # sin cambios
        self.assertEqual(mock_artifact.notes, "new notes")  # actualizado
        self.assertEqual(mock_artifact.sha256, "old_hash")  # sin cambios

    def test_update_artifact_not_found(self):
        """Test actualización de artefacto inexistente"""
        self.mock_dao.seleccionar.return_value = []

        with self.assertRaises(ValueError) as context:
            self.crud_artifacts.update_artifact(
                artifact_id=999,
                filename="new_name.xml",
                dao=self.mock_dao
            )
        self.assertIn("No Artifact found", str(context.exception))

    def test_update_artifact_with_hashes(self):
        """Test actualización de hashes de artefacto"""
        mock_artifact = MagicMock(spec=Artifacts)
        mock_artifact.id = 1
        mock_artifact.sha1 = ""
        mock_artifact.sha256 = ""
        mock_artifact.md5 = ""

        self.mock_dao.seleccionar.return_value = [mock_artifact]

        self.crud_artifacts.update_artifact(
            artifact_id=1,
            sha1="da39a3ee5e6b4b0d3255bfef95601890afd80709",
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            md5="d41d8cd98f00b204e9800998ecf8427e",
            dao=self.mock_dao
        )

        self.assertEqual(mock_artifact.sha1, "da39a3ee5e6b4b0d3255bfef95601890afd80709")
        self.assertEqual(mock_artifact.sha256, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        self.assertEqual(mock_artifact.md5, "d41d8cd98f00b204e9800998ecf8427e")

    def test_delete_artifact_success(self):
        """Test eliminación exitosa de un artefacto"""
        mock_artifact = MagicMock(spec=Artifacts)
        mock_artifact.id = 1
        self.mock_dao.seleccionar.return_value = [mock_artifact]

        self.crud_artifacts.delete_artifact(artifact_id=1, dao=self.mock_dao)

        self.mock_dao.eliminar.assert_called_once_with(mock_artifact, 1)

    def test_delete_artifact_not_found(self):
        """Test eliminación de artefacto inexistente"""
        self.mock_dao.seleccionar.return_value = []

        with self.assertRaises(ValueError) as context:
            self.crud_artifacts.delete_artifact(artifact_id=999, dao=self.mock_dao)
        self.assertIn("No Artifact found", str(context.exception))

    def test_delete_artifact_db_error(self):
        """Test eliminación con error de BD"""
        mock_artifact = MagicMock(spec=Artifacts)
        mock_artifact.id = 1
        self.mock_dao.seleccionar.return_value = [mock_artifact]
        self.mock_dao.eliminar.side_effect = Exception("DB error")

        with self.assertRaises(Exception):
            self.crud_artifacts.delete_artifact(artifact_id=1, dao=self.mock_dao)


if __name__ == '__main__':
    unittest.main()