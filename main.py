import asyncio
import argparse
import sys
from pathlib import Path
from src.html_converter import HTMLConverter
from src.utils.logging_utils import setup_logging, get_logger

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
        "--log-config",
        default="configs/logging_config.yml",
        help="Chemin vers le fichier de configuration de logging"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Active le mode debug"
    )
    
    return parser.parse_args()

async def main_async():
    """Async entry point"""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(default_path=args.log_config)
    logger = get_logger(__name__)
    
    if args.debug:
        logger.setLevel('DEBUG')
    
    logger.info("Starting HTML converter")
    
    try:
        converter = HTMLConverter(config_path=args.config)
        output_path = Path(args.output_file)
        
        logger.debug(f"Creating output directory: {output_path.parent}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Converting {args.input_file} to {args.output_file}")
        await converter.convert_async(args.input_file, str(output_path))
        
        logger.info("Conversion completed successfully")
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main_async())
