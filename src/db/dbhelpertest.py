"""Unit test for dbhelper.py

"""

__author__ = "Andrew Halloran"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2012/02/01 20:26:00 $"
__copyright__ ="Copyright (c) 2012 Andrew Halloran"

import pycassa
from pycassa.pool import ConnectionPool
from pycassa.columnfamily import ColumnFamily
from pycassa.cassandra.ttypes import NotFoundException
import dbhelper
import unittest
from dbhelper import Database, DatabaseException, ProviderAlreadyExistsError, ProviderHasNoUsernameError, ProviderDoesNotExistError, Provider, Patient, Claim, PatientDoesNotExistError

class ProviderTests(unittest.TestCase):

    def setUp(self):
        self.keyspace = 'Claimspace'
        self.host = 'localhost'
        self.port = '9160'
        self.pool = ConnectionPool(self.keyspace, [self.host+':'+self.port])
        self.cf = pycassa.ColumnFamily(self.pool,Database.providerCFname)
        self.db = Database(self.keyspace)
        self.providerDict = {'username':'testuser123',
                             'realname':'Testy User',
                             'providerid':'8675309'}
        self.providerObj = Provider(**self.providerDict)

    def tearDown(self):
        if hasattr(self.providerObj, 'username'):
            self.cf.remove(self.providerObj.username) 
    
    def test_create_provider(self):
        try:
            self.cf.get(self.providerObj.username)
        except NotFoundException:
            self.db.create_provider(self.providerObj)
        else:
            self.cf.remove(self.providerObj.username)
            self.db.create_provider(self.providerObj)
        resultDict = self.cf.get(self.providerObj.username)
        self.assertEqual(self.providerObj.get_fields(),resultDict)
    
    def test_create_provider_no_id(self):
        del self.providerObj.username
        self.assertRaises(ProviderHasNoUsernameError,
                          self.db.create_provider,
                          self.providerObj)

    def test_create_provider_already_exists(self):
        self.cf.insert(self.providerObj.username,self.providerObj.get_fields())
        self.assertRaises(ProviderAlreadyExistsError,
                          self.db.create_provider,
                          self.providerObj)


    def test_delete_provider(self):
        self.cf.insert(self.providerObj.username,self.providerObj.get_fields())
        self.db.delete_provider(self.providerObj.username)
        self.assertRaises(NotFoundException,
                          self.cf.get,
                          self.providerObj.username)

    def test_get_provider(self):
        self.cf.insert(self.providerObj.username,self.providerObj.get_fields())
        resultObj = self.db.get_provider(self.providerObj.username)
        self.assertEqual(self.providerObj,resultObj)
    
    def test_get_not_found(self):
        self.assertRaises(ProviderDoesNotExistError,
                          self.db.get_provider,
                          self.providerObj.username)

    def test_update_provider(self):
        self.cf.insert(self.providerObj.username,self.providerObj.get_fields())
        self.providerObj.realname = 'John Doe'
        self.db.update_provider(self.providerObj)
        resultDict = self.cf.get(self.providerObj.username)
        resultObj = Provider(**resultDict)
        self.assertEqual(self.providerObj.get_fields(),resultDict)

    def test_update_no_id(self):
        del self.providerObj.username
        self.assertRaises(ProviderHasNoUsernameError,
                          self.db.update_provider,
                          self.providerObj)

class PatientTests(unittest.TestCase):

    def setUp(self):
        self.keyspace = 'Claimspace'
        self.host = 'localhost'
        self.port = '9160'
        self.pool = ConnectionPool(self.keyspace, [self.host+':'+self.port])
        self.proCF = pycassa.ColumnFamily(self.pool,Database.providerCFname)
        self.patCF = pycassa.ColumnFamily(self.pool,Database.patientCFname)
        self.patMapCF = pycassa.ColumnFamily(self.pool, Database.patientMapCFname)
        self.db = Database(self.keyspace)
        self.providerDict = {'username':'testuser123',
                             'realname':'Testy User',
                             'providerid':'8675309'}
        self.providerObj = Provider(**self.providerDict)
        self.patientDict = {'pname':'John Doe',
                            'psex':'m',
                            'pid':'88888'}
        self.patientObj = Patient(**self.providerDict)
        self.patientDict['hashkey']=self.patientObj.hashkey

    def tearDown(self):
        pass

    def test_create_patient(self):
        try:
            self.patCF.get(self.patientObj.hashkey)
        except NotFoundException:
            self.db.create_patient(self.patientObj)
        else:
            self.patCF.remove(self.username)
            self.db.create_patient(self.patientObj)
        resultDict = self.patCF.get(self.patientObj.hashkey)
        self.assertEqual(self.patientObj.get_fields(),resultDict)

    def test_update_patient(self):
        self.patCF.insert(self.patientObj.hashkey,self.patientObj.get_fields())
        self.patientObj.pname = 'John Deer'
        self.db.update_patient(self.patientObj)
        resultDict = self.patCF.get(self.patientObj.hashkey)
        resultObj = Patient(**resultDict)
        self.assertEqual(self.patientObj.get_fields(),resultDict)

    def test_get_patient(self):
        self.patCF.insert(self.patientObj.hashkey,self.patientObj.get_fields())
        resultObj = self.db.get_patient(self.patientObj.hashkey)
        self.assertEqual(self.patientObj,resultObj)
        
    def test_get_not_found(self):
        self.assertRaises(PatientDoesNotExistError,
                          self.db.get_patient,
                          self.patientObj.hashkey)

    def test_delete_patient(self):
        self.patCF.insert(self.patientObj.hashkey,self.patientObj.get_fields())
        self.db.delete_patient(self.patientObj.hashkey)
        self.assertRaises(NotFoundException,
                          self.patCF.get,
                          self.patientObj.hashkey)

    def test_assign_patient(self):
        self.db.assign_patient(self.patientObj, self.providerObj)
        resultDict = self.patMapCF.get(self.providerObj.username)
        self.assertTrue(self.patientObj.hashkey in resultDict)

    def test_unassign_patient(self):
        self.patMapCF.insert(self.providerObj.username,{self.patientObj.hashkey:''})
        self.db.unassign_patient(self.patientObj,self.providerObj)
        resultDict = self.patMapCF.get(self.providerObj.username)
        self.assertTrue(self.patientObj.hashkey not in resultDict)



if __name__ == "__main__":
    unittest.main()
