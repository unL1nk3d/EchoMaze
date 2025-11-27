import unittest

# Importa los módulos de test individuales
from test_crud import TestCRUD_GATHERINGDB
from test_dao import TestGenericDAO, TestTransaction
from test_connection import TestSQLiteConnectionPool

def suite():
    test_suite = unittest.TestSuite()
    # CRUD_GATHERINGDB tests
    #test_suite.addTest(TestCRUD_GATHERINGDB)
    
    # GenericDAO and Transaction tests
    test_suite.addTest(TestGenericDAO)
    test_suite.addTest(TestTransaction)
    
    # SQLiteConnectionPool tests
    test_suite.addTest(TestSQLiteConnectionPool)
    
    return test_suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
