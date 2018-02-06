Les fichiers db et conf peuvent être générés avec les scripts du provisionning WINGS :
- random_epc_gen avec option -b, pour générer le fichiers des URN;
- ons-zone-gen.py avec option -z pour générer les zones, copier les fichiers 
db ici et ajouter les lignes du .conf généré dans le fichier de conf ici.
- ajouter le TTL et le serveur secondaire, voir avec JP pour déclarer la 
nouvelle zone sur ns3.nic.fr.
