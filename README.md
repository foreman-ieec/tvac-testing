# tvac-testing
TVAC testing chart generation

Aquest codi està dissenyat amb una estructura modular i orientada a objectes per facilitar el processament de dades de test i la seva visualització. A continuació es detallen els components clau perquè qualsevol enginyer pugui adaptar-lo a nous escenaris de prova:
1. Biblioteques i Configuració de l'Entorn
El script utilitza l'ecosistema estàndard de ciència de dades en Python:

    Pandas: Per a la manipulació i combinació de fitxers CSV.
    Matplotlib i Seaborn: Per a la generació de gràfiques. S'ha definit un estil visual per defecte (seaborn-v0_8) i una paleta de colors (husl) per mantenir la consistència visual en els informes.
    Pathlib: S'utilitza Path per a una gestió de rutes de fitxers robusta i independent del sistema operatiu (Windows/Linux).

2. Estructura de la Classe Principal
L'anàlisi s'encapsula en una classe (en l'exemple, PhotSatQMDataAnalyzer), la qual cosa permet mantenir l'estat de les dades i els paràmetres de configuració en un sol lloc.
El Constructor (__init__)
Aquesta és la part més crítica per a l'adaptació:

    Directori de dades: Accepta un argument data_directory. Per a un nou test, només cal canviar aquest valor al crear la instància de la classe.
    Evitar sobreescriptura: El codi inclou una lògica intel·ligent per crear carpetes de sortida. Utilitza un comptador incremental (ex: visualizations-1, visualizations-2) que verifica si la carpeta ja existeix abans de crear-ne una de nova, assegurant que no es perdin dades de tests anteriors.

3. Flux d'Execució
El script segueix el patró estàndard de Python per a l'execució:

    Funció main(): Actua com a punt d'entrada on s'instancia l'analitzador.
    Bloc if __name__ == "__main__":: Garanteix que el codi només s'executi si el fitxer es crida directament, permetent que la classe es pugui importar en altres scripts sense disparar l'anàlisi automàticament.

Guia per a l'Adaptació a Nous Testos
Per aplicar aquest codi a un nou conjunt de dades, els enginyers haurien de:

    Modificar el directori d'entrada: En el mètode __init__, canviar el valor per defecte de data_directory o passar-li la nova ruta en instanciar la classe al main().
    Configurar el nom de la carpeta de sortida: Canviar la variable base_name per reflectir el nom del nou test.
    Implementar la lògica de càrrega: Tot i que el fragment no mostra el mètode de lectura complet, el docstring indica que està preparat per llegir múltiples fitxers CSV (de "Day1" a "Day11") i combinar-los en un únic DataFrame (self.combined_data).

Aquesta arquitectura permet que el nucli de la gestió de fitxers i la configuració visual romangui intacte, mentre que la lògica específica de cada test es pot afegir com a nous mètodes dins de la mateixa classe.
