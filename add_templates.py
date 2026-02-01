#!/usr/bin/env python3
import json
from cheatIngestor.core import Ingestor
from cheatIngestor.adapters.drivens.RepositoryImpl import Repository
from cheatIngestor.models.repository import Configurator
from GATHERINGDB.dao import GenericDAO

# Datos de ejemplo para templates de pivoting
sample_templates = [
    {
        "technique": "T1021.001",
        "name": "Remote Desktop Protocol",
        "templates": [
            {
                "desc": "Connect to RDP service",
                "linux": "xfreerdp /u:username /p:password /v:TARGET_IP",
                "windows": "mstsc /v:TARGET_IP",
                "noise_estimate": 3
            }
        ]
    },
    {
        "technique": "T1021.002",
        "name": "SMB/Windows Admin Shares",
        "templates": [
            {
                "desc": "Mount SMB share",
                "linux": "mount -t cifs //TARGET_IP/share /mnt/share -o username=user,password=pass",
                "windows": "net use Z: \\\\TARGET_IP\\share /user:user pass",
                "noise_estimate": 2
            }
        ]
    },
    {
        "technique": "T1078",
        "name": "Valid Accounts",
        "templates": [
            {
                "desc": "SSH login",
                "linux": "ssh user@TARGET_IP",
                "windows": "ssh user@TARGET_IP",
                "noise_estimate": 1
            }
        ]
    }
]

def main():
    dao = GenericDAO()
    repository = Repository()
    configurator = Configurator(True, repository, dao)
    repository.initialize_repository(configurator)
    ingestor = Ingestor(repository)

    for template_data in sample_templates:
        document = json.dumps(template_data)
        ingestor.ingestJsonDocument(document)
        print(f"Ingested template for {template_data['technique']}")

if __name__ == "__main__":
    main()