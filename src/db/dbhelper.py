"""This module reads and writes data to and from the cassandra DB

"""

__author__ = "Andrew Halloran"
__version__ = "$Revision: 0.1 $"
__date__ = "$Date: 2012/02/02 20:54:00 $"
__copyright__ ="Copyright (c) 2012 Andrew Halloran"

import hashlib
from datetime import datetime
import pycassa
from pycassa.pool import ConnectionPool
from pycassa.columnfamily import ColumnFamily
from pycassa.cassandra.ttypes import NotFoundException

patientFields = {
    'iDOB':'insuredsDOB',
    'iIDnum':'insuredsIDnumber',
    'icity':'insuredsaddresscity',
    'iline1':'insuredsaddressline1',
    'iline2':'insuredsaddressline2',
    'istate':'insuredsaddressstate',
    'izip':'insuredsaddresszip',
    'iemployer':'insuredsemployersorschoolsname',
    'iplanname':'insuredsinsuranceplanorprogramname',
    'iisthereanotherplan':'insuredsisthereanotherhealthplan',
    'iname':'insuredsname',
    'ipolicy':'insuredspolicygrouporfeca',
    'isex':'insuredssex',
    'iphone':'insuredstelephone',
    'oDOB':'otherinsuredsDOB',
    'oemployer':'otherinsuredsemployersorschoolsname',
    'oplanname':'otherinsuredsinsuranceplanorprogramname',
    'oname':'otherinsuredsname',
    'opolicy':'otherinsuredspolicyorgroup',
    'osex':'otherinsuredssex',
    'pDOB':'patientDOB',
    'pcity':'patientaddresscity',
    'pconditionrelatedto':'patientconditionrelatedto',
    'pline1':'patientaddressline1',
    'pline2':'patientaddressline2',
    'pstate':'patientaddressstate',
    'pphone':'patientaddresstelephone',
    'pzip':'patientaddresszip',
    'pID':'patientid',
    'pname':'patientname',
    'psex':'patientsex',
    'prelation':'patientsrelation',
    'pstatus':'patientstatus',
    'ptype':'patienttype',
    'reservedforlocaluse':'reservedforlocaluse',
    'hashkey':'hashkey'
}

providerFields = {
    'emailaddress':'emailaddress',
    'patientids':'patientids',
    'practiceaddresscity':'practiceaddresscity',
    'practiceaddressline1':'practiceaddressline1',
    'practiceaddressline2':'practiceaddressline2',
    'practiceaddressstate':'practiceaddressstate',
    'practiceaddresszip':'practiceaddresszip',
    'practicename':'practicename',
    'providerid':'providerid',
    'realname':'realname',
    'username':'username'
}


class DatabaseException(Exception):
    """Base class for exceptions in db module"""

class ProviderAlreadyExistsError(DatabaseException):
    """The user already exists"""

class ProviderHasNoUsernameError(DatabaseException):
    """User cannot be empty. User must contain data."""

class ProviderDoesNotExistError(DatabaseException):
    """The provider does not exist."""

class PatientCannotBeEmptyError(DatabaseException):
    """The patient cannot be empty"""
    
class PatientHashkeyAlreadyExistsError(DatabaseException):
    """The patient cannot be created because it already has a hashkey. The hashkey should only be computed by the create_patient function"""

class PatientAlreadyExistsError(DatabaseException):
    """The patient already exists"""

class PatientHashkeyDoesNotExistError(DatabaseException):
    """The patient does not have a hashkey."""

class PatientDoesNotExistError(DatabaseException):
    """The patient does not exist"""

class DatabaseObject(object):
    """The base object for database objects in the system"""
    def __init__(self, **kwargs):
        if 'hashkey' not in self.__dict__:
            self.hashkey = self.generate_hashkey()
        super(DatabaseObject,self).__init__(**kwargs)

    def __eq__(self,other):
        return self.__dict__ == other.__dict__

    def __ne__(self,other):
        return self.__dict__ != other.__dict__

    def generate_hashkey(self):
        hashkey = hashlib.sha1()
        hashkey.update(";".join(["%s=%s" % (k, v) for k, v in self.__dict__.items()]))
        hashkey.update(str(datetime.now()))
        return hashkey.hexdigest()

    def get_fields(self):
        return self.__dict__

class Provider(DatabaseObject):
    """An object representing a healthcare provider."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Provider,self).__init__()

class Patient(DatabaseObject):
    """An object representing a healthcare patient."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Patient,self).__init__()

class Claim(DatabaseObject):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super(Claim,self).__init__()

class Database():
    """A database object which handles modifications for a medical claim
    database Cassandra instance"""
    
    providerCFname = 'providers'
    patientMapCFname = 'provider_patient_map'
    claimMapCFname = 'provider_claim_map'
    patientCFname = 'patients'
    claimsCFname = 'claims'
    
    def __init__(self, keyspace=None, host='localhost', port='9160'):
        self.host = host
        self.port = port
        self.keyspace = keyspace
        self.pool = ConnectionPool(self.keyspace, [self.host+':'+self.port])
        self.providerCF = pycassa.ColumnFamily(self.pool, self.providerCFname)
        self.patientCF = pycassa.ColumnFamily(self.pool, self.patientCFname)
        self.patientMapCF = pycassa.ColumnFamily(self.pool, self.patientMapCFname)

    def create_provider(self, providerObj):
        if not hasattr(providerObj,'username'):
            raise ProviderHasNoUsernameError('')
        try:
            self.providerCF.get(providerObj.username)
        except NotFoundException:
            self.providerCF.insert(providerObj.username,providerObj.get_fields())
        else:
            raise ProviderAlreadyExistsError('') 
    
    def update_provider(self, providerObj):
        if not hasattr(providerObj,'username'):
            raise ProviderHasNoUsernameError('')
        self.providerCF.insert(providerObj.username,providerObj.get_fields())

    def delete_provider(self, providerKeyStr):
        self.providerCF.remove(providerKeyStr)

    def get_provider(self, providerKeyStr):
        try:
            providerDict = self.providerCF.get(providerKeyStr)
            return Provider(**providerDict)
        except NotFoundException:
            raise ProviderDoesNotExistError('')

    def create_patient(self, patientObj):
        if len(patientObj.get_fields()) == 0:
            raise PatientCannotBeEmptyError('')
        try:
            self.patientCF.get(patientObj.hashkey)
        except NotFoundException:
            self.patientCF.insert(patientObj.hashkey, patientObj.get_fields())
        else:
            raise PatientAlreadyExistsError('')

    def update_patient(self, patientObj):
        self.patientCF.insert(patientObj.hashkey,patientObj.get_fields())

    def get_patient(self, patientKeyStr):
        try:
            patientDict = self.patientCF.get(patientKeyStr)
            return Patient(**patientDict)
        except NotFoundException:
            raise PatientDoesNotExistError('')

    def delete_patient(self, patientKeyStr):
        self.patientCF.remove(patientKeyStr)

    def assign_patient(self, patientObj, providerObj):
        if not hasattr(providerObj, 'username'):
            raise ProviderHasNoUsernameError('')
        self.patientMapCF.insert(providerObj.username,{patientObj.hashkey:''})

    def unassign_patient(self, patientObj, providerObj):
        if not hasattr(providerObj,'username'):
            raise ProviderHasNoUsernameError('')
        self.patientMapCF.remove(providerObj.username,{patientObj.hashkey:''})


