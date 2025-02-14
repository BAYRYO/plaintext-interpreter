import argparse
import logging
import sys
from pathlib import Path
from src.html_converter import HTMLConverter

def setup_logging():
    """Configure le logging global."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_arguments():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Convertisseur de texte en HTML avec gestion des assets."
    )
    parser.add_argument(
        "input_file",
        help="Chemin vers le fichier texte d'entrée"
    )
    parser.add_argument(
        "output_file",
        help="Chemin vers le fichier HTML de sortie"
    )
    parser.add_argument(
        "--config",
        default="configs/config.yml",
        help="Chemin vers le fichier de configuration (défaut: configs/config.yml)"
    )
    parser.add_argument(
        "--prepare-assets",
        action="store_true",
        help="Prépare les assets dans le dossier de sortie"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Active le mode debug"
    )
    
    return parser.parse_args()

def main():
    """Point d'entrée principal de l'application."""
    # Configuration du logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Parse les arguments
    args = parse_arguments()
    
    try:
        # Ajuste le niveau de logging si mode debug
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Crée le convertisseur
        converter = HTMLConverter(config_path=args.config)
        
        # Prépare les chemins
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prépare les assets si demandé
        if args.prepare_assets:
            logger.info("Préparation des assets...")
            converter.prepare_assets(output_path.parent)
        
        # Effectue la conversion
        logger.info(f"Début de la conversion de {args.input_file}")
        converter.convert(args.input_file, str(output_path))
        logger.info("Conversion terminée avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors de la conversion: {str(e)}")
        if args.debug:
            logger.exception("Détails de l'erreur:")
        sys.exit(1)

if __name__ == "__main__":
    main()
