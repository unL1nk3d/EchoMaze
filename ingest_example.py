from launch import build_core_stack
dao, crud, core, cmd, generic = build_core_stack()
document = '{"technique": "T1021", "name": "Remote Services", "templates": [{"desc": "SSH tunneling for pivoting", "linux": "ssh -L 8080:target:80 user@pivot", "windows": "plink.exe -L 8080:target:80 user@pivot", "noise_estimate": 3}]}'
generic.ingestor.ingestJsonDocument(document)
print('Cheatsheet ingested')