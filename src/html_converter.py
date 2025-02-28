from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from pathlib import Path
import logging
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
import json
import shutil
import re
from bs4 import BeautifulSoup
from .interfaces import IContentProcessor, ITemplateEngine
from .processors import CodeProcessor, ListProcessor, TableProcessor
from .validators import ValidatorFactory
import os
import time
import aiofiles
import asyncio
from functools import lru_cache
from hashlib import md5
from .utils.logging_utils import get_logger, log_execution_time, log_async_execution_time

@dataclass
class Title:
    level: int
    text: str
    id: str

class HTMLConverter:
    """Classe principale pour la conversion de texte en HTML."""
    
    def __init__(self, 
                 config_path: str = 'config.yml',
                 processors: Optional[List[IContentProcessor]] = None,
                 template_engine: Optional[ITemplateEngine] = None,
                 logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger('html_converter')
        self.logger.info("Initializing HTMLConverter")
        self.config = self._load_config(config_path)
        self.jinja_env = template_engine or self._setup_jinja()
        self.regex_pattern = self.config['patterns']['title']
        
        self.processors = processors or [
            CodeProcessor(),
            ListProcessor(),
            TableProcessor()
        ]
        self.logger.debug(f"Initialized with {len(self.processors)} processors")
        
        self._validate_paths()
        self._validate_templates()

    def _load_config(self, config_path: str) -> dict:
        """Charge la configuration depuis le fichier YAML."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Fichier de configuration '{config_path}' non trouvé.")

    def _setup_logger(self) -> logging.Logger:
        """Configure et retourne le logger."""
        logger = logging.getLogger(__name__)
        logger.setLevel(
            logging.DEBUG if self.config['general']['debug_mode'] else logging.INFO
        )
        
        # Ajout d'un handler si aucun n'existe
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger

    def _setup_jinja(self) -> Environment:
        """Configure et retourne l'environnement Jinja2."""
        template_dir = str(Path('templates').absolute())
        return Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def read_file(self, file_path: str) -> str:
        """Lit le contenu d'un fichier."""
        path = Path(file_path)
        try:
            return path.read_text(encoding=self.config['general']['encoding'])
        except FileNotFoundError:
            raise FileNotFoundError(
                self.config['messages']['errors']['file_not_found'].format(
                    file_path=file_path
                )
            )

    def process_titles(self, content: str) -> Tuple[str, List[Title]]:
        """Traite les titres dans le contenu et retourne le contenu modifié et la liste des titres."""
        titles = []
        allowed_tags = self.config['html']['allowed_tags']
        matches = re.finditer(self.regex_pattern, content, re.MULTILINE | re.DOTALL)
        
        processed_content = []
        last_index = 0
        
        for index, match in enumerate(matches):
            tag_content = match.group(0)
            tag_match = re.match(r'<(\w+)', tag_content)
            
            if tag_match and tag_match.group(1) in allowed_tags:
                if tag_match.group(1).startswith('h'):
                    title = self._process_single_title(tag_content, index)
                    if title:
                        titles.append(title)
                        tag_content = self._add_id_to_title(tag_content, title)
                
                processed_content.append(content[last_index:match.start()])
                processed_content.append(self._process_content(tag_content))
                last_index = match.end()
        
        processed_content.append(content[last_index:])
        return "".join(processed_content), titles

    def _process_single_title(self, tag_content: str, index: int) -> Optional[Title]:
        """Traite un titre individuel."""
        title_match = re.match(r'<h([1-6])', tag_content)
        if title_match:
            level = int(title_match.group(1))
            soup = BeautifulSoup(tag_content, 'html.parser')
            text = soup.get_text(" ", strip=True)
            return Title(
                level=level,
                text=text,
                id=f"{self.config['ids']['title_prefix']}{index + 1}"
            )
        return None

    def _add_id_to_title(self, tag_content: str, title: Title) -> str:
        """Ajoute un ID à une balise de titre."""
        return tag_content.replace(
            f"<h{title.level}>",
            f"<h{title.level} id=\"{title.id}\">"
        )

    def _process_content(self, content: str) -> str:
        """Traite le contenu avec tous les processeurs."""
        for processor in self.processors:
            content = processor.process(content)
        return content

    def generate_navigation_panel(self, titles: List[Title]) -> str:
        """Génère le panneau de navigation."""
        template = self.jinja_env.get_template('components/navigation.html')
        return template.render(
            titles=titles,
            config=self.config,
            nav_button=self.read_file(self.config['templates']['paths']['nav_button'])
        )

    def verify_favicon_resources(self) -> Dict[str, List[str]]:
        """Vérifie la présence et la validité des ressources favicon."""
        results = {'missing': [], 'invalid': []}
        images_path = Path(self.config['templates']['paths']['assets']['images'])
        
        for favicon_file in self.config['favicons']['required_files']:
            file_path = images_path / favicon_file
            if not file_path.exists():
                results['missing'].append(favicon_file)
                continue
                
            validator = ValidatorFactory.get_validator(file_path.suffix)
            if validator and not validator.validate(file_path):
                results['invalid'].append(favicon_file)

        # Vérification du webmanifest
        self._validate_webmanifest(images_path / 'site.webmanifest', results)
        
        return results

    def _validate_webmanifest(self, manifest_path: Path, results: Dict[str, List[str]]) -> None:
        """Valide le fichier webmanifest."""
        if not manifest_path.exists():
            results['missing'].append('site.webmanifest')
            return

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                
            required_fields = ['name', 'icons']
            if not all(field in manifest for field in required_fields):
                results['invalid'].append('site.webmanifest')
                return
                
            if not manifest['icons'] or not isinstance(manifest['icons'], list):
                results['invalid'].append('site.webmanifest')
                return
                
            for icon in manifest['icons']:
                if not all(field in icon for field in ['src', 'sizes', 'type']):
                    results['invalid'].append('site.webmanifest')
                    return
                    
        except Exception:
            results['invalid'].append('site.webmanifest')

    def _validate_paths(self) -> None:
        """Vérifie que tous les chemins nécessaires existent."""
        required_paths = [
            self.config['templates']['paths']['header'],
            self.config['templates']['paths']['footer'],
            self.config['templates']['paths']['nav_button'],
            Path(self.config['templates']['paths']['assets']['css']),
            Path(self.config['templates']['paths']['assets']['js']),
            Path(self.config['templates']['paths']['assets']['images'])
        ]
        
        for path in required_paths:
            if not Path(path).exists():
                raise FileNotFoundError(f"Chemin requis non trouvé : {path}")

    def _validate_templates(self) -> None:
        """Vérifie que tous les templates nécessaires existent."""
        for template_name, template_path in self.config['templates']['paths'].items():
            if isinstance(template_path, str) and not Path(template_path).exists():
                raise FileNotFoundError(
                    f"Template '{template_name}' introuvable : {template_path}"
                )
            
    def _verify_assets_integrity(self, assets_dir: Path) -> None:
        """
        Vérifie l'intégrité des assets après la copie.
        
        Args:
            assets_dir (Path): Dossier des assets à vérifier
        """
        expected_structure = {
            'css': ['.css'],
            'js': ['.js'],
            'images': ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg']
        }

        for asset_type, extensions in expected_structure.items():
            type_dir = assets_dir / asset_type
            if not type_dir.exists():
                self.logger.warning(f"Dossier {asset_type} manquant dans les assets")
                continue

            files = list(type_dir.rglob('*'))
            if not files:
                self.logger.warning(f"Aucun fichier trouvé dans {type_dir}")
            else:
                valid_files = [f for f in files if f.is_file() and f.suffix in extensions]
                if not valid_files:
                    self.logger.warning(f"Aucun fichier valide trouvé dans {type_dir}")

    def prepare_assets(self, output_dir: Path) -> None:
        """
        Prépare et copie les assets vers le dossier de destination.
        
        Args:
            output_dir (Path): Chemin du dossier de sortie
        
        Raises:
            OSError: En cas d'erreur lors de la copie des fichiers
        """
        assets_dir = output_dir / 'assets'
        
        # Structure des assets à copier
        asset_structure = {
            'css': self.config['templates']['paths']['assets']['css'],
            'js': self.config['templates']['paths']['assets']['js'],
            'images': self.config['templates']['paths']['assets']['images']
        }

        try:
            # 1. Nettoyage du dossier assets existant si nécessaire
            if assets_dir.exists():
                self.logger.info(f"Nettoyage du dossier assets existant: {assets_dir}")
                shutil.rmtree(assets_dir, ignore_errors=True)

            # 2. Création de la structure de base
            for asset_type in asset_structure.keys():
                (assets_dir / asset_type).mkdir(parents=True, exist_ok=True)

            # 3. Copie des assets avec gestion des erreurs
            for asset_type, source_path in asset_structure.items():
                source_dir = Path(source_path)
                if not source_dir.exists():
                    self.logger.warning(f"Dossier source manquant: {source_dir}")
                    continue

                dest_dir = assets_dir / asset_type
                self._copy_directory_contents(source_dir, dest_dir)

            self.logger.info(f"Assets copiés avec succès vers {assets_dir}")
            
            # 4. Vérification post-copie
            self._verify_assets_integrity(assets_dir)

        except Exception as e:
            self.logger.error(f"Erreur lors de la préparation des assets: {str(e)}")
            raise

    def _copy_directory_contents(self, source_dir: Path, dest_dir: Path) -> None:
        """
        Copie récursivement le contenu d'un dossier avec gestion des erreurs.
        
        Args:
            source_dir (Path): Dossier source
            dest_dir (Path): Dossier destination
        """
        try:
            for item in source_dir.rglob('*'):
                # Calcul du chemin relatif pour préserver la structure
                relative_path = item.relative_to(source_dir)
                destination = dest_dir / relative_path

                if item.is_file():
                    # Création des sous-dossiers si nécessaire
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copie avec retry
                    self._copy_with_retry(item, destination)
                    
                elif item.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            self.logger.error(f"Erreur lors de la copie de {source_dir} vers {dest_dir}: {str(e)}")
            raise

    def _copy_with_retry(self, src: Path, dst: Path, max_attempts: int = 3, delay: float = 0.5) -> None:
        """Copie un fichier avec plusieurs tentatives en cas d'erreur."""
        import time
        
        for attempt in range(max_attempts):
            try:
                # Si le fichier existe déjà, on essaie de le supprimer
                if dst.exists():
                    try:
                        dst.unlink()
                    except Exception:
                        pass
                        
                # Copie du fichier
                shutil.copy2(src, dst)
                return
                
            except PermissionError:
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                    continue
                raise
                
            except Exception as e:
                self.logger.error(f"Erreur lors de la copie de {src} vers {dst}: {str(e)}")
                raise


    @log_execution_time()
    def convert(self, input_file: str, output_file: str) -> None:
        """Synchronous conversion method"""
        self.logger.info(f"Starting conversion: {input_file} -> {output_file}")
        try:
            input_path = Path(input_file).resolve()
            output_path = Path(output_file).resolve()
            
            self.logger.debug(f"Reading input file: {input_path}")
            content = self.read_file(str(input_path))
            
            self.logger.debug("Processing content")
            processed_content, titles = self.process_titles(content)
            
            self.logger.debug("Preparing template data")
            template_data = self._prepare_template_data(processed_content, titles, output_path)
            
            self.logger.debug("Generating HTML")
            output_html = self.jinja_env.get_template('base.html').render(**template_data)
            
            self.logger.debug(f"Writing output file: {output_path}")
            output_path.write_text(output_html, encoding=self.config['general']['encoding'])
            
            self.logger.info(f"Successfully converted {input_file} to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Conversion failed: {str(e)}", exc_info=True)
            raise

    @log_async_execution_time()
    async def convert_async(self, input_file: str, output_file: str) -> None:
        """Asynchronous conversion method"""
        self.logger.info(f"Starting async conversion: {input_file} -> {output_file}")
        try:
            input_path = Path(input_file).resolve()
            output_path = Path(output_file).resolve()
            
            self.logger.debug(f"Reading input file: {input_path}")
            content = await self._read_file_async(str(input_path))
            
            self.logger.debug("Processing content")
            processed_content, titles = self.process_titles(content)
            
            self.logger.debug("Preparing template data")
            template_data = await self._prepare_template_data(processed_content, titles, output_path)
            
            self.logger.debug("Generating HTML")
            output_html = self.jinja_env.get_template('base.html').render(**template_data)
            
            self.logger.debug(f"Writing output file: {output_path}")
            await self._write_file_async(output_path, output_html)
            
            self.logger.info(f"Successfully converted {input_file} to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Async conversion failed: {str(e)}", exc_info=True)
            raise

    async def _read_file_async(self, file_path: str) -> str:
        """Async file reading"""
        try:
            async with aiofiles.open(file_path, mode='r', encoding=self.config['general']['encoding']) as f:
                return await f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")

    async def _write_file_async(self, file_path: Path, content: str) -> None:
        """Async file writing"""
        async with aiofiles.open(file_path, mode='w', encoding=self.config['general']['encoding']) as f:
            await f.write(content)

    async def _prepare_template_data(self, content: str, titles: List[Title], output_path: Path) -> Dict:
        """Prepare template data asynchronously"""
        return {
            'content': content,
            'titles': titles,
            'config': self.config,
            'navigation': await asyncio.to_thread(self.generate_navigation_panel, titles),
            'assets': await asyncio.to_thread(self._calculate_assets_paths, output_path),
            'favicon_status': await asyncio.to_thread(self.verify_favicon_resources)
        }

    def _calculate_assets_paths(self, output_path: Path) -> Dict:
        """Calculate assets paths"""
        relative_assets_path = Path('assets')
        return {
            'css': str(relative_assets_path / 'css'),
            'js': str(relative_assets_path / 'js'),
            'images': str(relative_assets_path / 'images')
        }

    async def prepare_assets_async(self, output_dir: Path) -> None:
        """Async version of prepare_assets"""
        await asyncio.to_thread(self.prepare_assets, output_dir)

    def _get_relative_path(self, from_path: Path, to_path: Path) -> str:
        """Calcule le chemin relatif entre deux chemins."""
        try:
            return str(Path(os.path.relpath(to_path, from_path.parent)))
        except ValueError:
            return str(to_path)
        
    def _verify_assets_structure(self, output_dir: Path) -> None:
        """Vérifie que la structure des assets est correcte."""
        required_dirs = ['css', 'js', 'images']
        assets_dir = output_dir / 'assets'
        
        for dir_name in required_dirs:
            dir_path = assets_dir / dir_name
            if not dir_path.exists():
                self.logger.warning(f"Dossier d'assets manquant : {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)

        # Vérification des fichiers essentiels
        required_files = {
            'css': ['styles.css'],
            'js': ['main.js'],
            'images/favicons': self.config['favicons']['required_files']
        }
        
        for dir_name, files in required_files.items():
            dir_path = assets_dir / dir_name
            for file_name in files:
                file_path = dir_path / file_name
                if not file_path.exists():
                    self.logger.warning(f"Fichier d'asset manquant : {file_path}")
